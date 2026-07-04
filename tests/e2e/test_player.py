"""
E2E del reproductor: carga la canción (P1), Play avanza el beat (P2),
transponer cambia los acordes (P3).
"""

import pytest

from tests.conftest import sample_song_payload, wipe_songs

pytestmark = pytest.mark.e2e


def _crear_y_abrir(page, live_server, api, title="Cancion Player"):
    wipe_songs(api)
    sid = api.post("/songs/", json=sample_song_payload(title=title)).json()["id"]
    page.goto(live_server + f"/static/index.html?songId={sid}", wait_until="networkidle")
    page.wait_for_selector(".chord-container, .chord-pill", timeout=8000)
    return sid


def _apagar_cuenta(page):
    """T-V5-08: la cuenta atrás viene en 4 por defecto; la apagamos para probar el arranque
    inmediato del motor (si no, el Play tendría 2 s de pre-roll antes de avanzar el beat)."""
    for _ in range(3):
        if page.inner_text("#btn-countin") == "–":
            return
        page.click("#btn-countin")


def test_carga_la_cancion(page, live_server, api):
    _crear_y_abrir(page, live_server, api, title="Cancion Cargada")
    assert page.inner_text("#song-title") == "Cancion Cargada"
    assert page.locator(".chord-container, .chord-pill").count() >= 1


def test_carga_por_defecto_sin_songId(page, live_server, api):
    """Abrir el reproductor SIN ?songId debe cargar la primera canción con sus
    acordes. Regresión T-010: el listado /songs/ se volvió ligero (SongSummary sin
    `sections`); app.js debe pedir el detalle de songs[0], no renderizar el resumen."""
    wipe_songs(api)
    api.post("/songs/", json=sample_song_payload(title="Primera Por Defecto"))
    page.goto(live_server + "/static/index.html", wait_until="networkidle")
    page.wait_for_selector(".chord-container, .chord-pill", timeout=8000)
    assert page.inner_text("#song-title") == "Primera Por Defecto"
    # Si app.js hubiera renderizado el SongSummary (sin sections), no habría acordes.
    assert page.locator(".chord-container, .chord-pill").count() >= 1


def test_songid_inexistente_avisa_al_usuario(page, live_server, api):
    """Abrir el reproductor con un ?songId inexistente (404) muestra un aviso claro en el
    área principal con salida a la biblioteca, no una pantalla en blanco ni un mensaje
    técnico (T-041)."""
    page.goto(live_server + "/static/index.html?songId=no-existe-1234",
              wait_until="networkidle")
    page.wait_for_selector(".empty-state", timeout=8000)
    texto = page.inner_text("#score-content")
    assert "No encontramos esta canción" in texto
    # Hay una salida a la biblioteca.
    assert page.locator('#score-content a[href="library.html"]').count() == 1
    # No se filtra el mensaje técnico viejo.
    assert "FastAPI" not in page.inner_text("#song-title")


def test_play_avanza_el_beat(page, live_server, api):
    _crear_y_abrir(page, live_server, api)
    _apagar_cuenta(page)   # sin pre-roll, para medir el arranque inmediato
    # T-V5-07: la barra muestra el COMPÁS ("Compás N"); el beat crudo va en data-beat.
    assert page.inner_text("#current-beat-display").startswith("Compás")
    assert float(page.get_attribute("#current-beat-display", "data-beat")) == 0.0
    page.click("#btn-play-pause")
    page.wait_for_timeout(900)  # dejar correr ~1s de reproducción
    page.click("#btn-play-pause")  # pausar
    # El beat debe haber avanzado por encima de 0.0 (leído del data-beat).
    valor = float(page.get_attribute("#current-beat-display", "data-beat"))
    assert valor > 0.0, f"el beat no avanzó: data-beat={valor}"


def test_accesibilidad_aria_y_atajo_espacio(page, live_server, api):
    """Los botones de emoji tienen aria-label y la barra espaciadora alterna play/pausa (T-021)."""
    _crear_y_abrir(page, live_server, api)
    _apagar_cuenta(page)   # sin pre-roll, para medir el arranque inmediato
    # aria-label en botones de icono/emoji.
    for sel, etiqueta in [("#btn-stop", "Detener"), ("#btn-key-save", "Guardar tono"),
                          ("#btn-bpm-up", "Subir BPM")]:
        assert page.get_attribute(sel, "aria-label") == etiqueta

    # Atajo: barra espaciadora arranca la reproducción.
    page.locator("#score-container").click()  # foco fuera de inputs
    page.keyboard.press("Space")
    page.wait_for_timeout(600)
    page.keyboard.press("Space")  # pausar
    valor = float(page.get_attribute("#current-beat-display", "data-beat"))
    assert valor > 0.0, "la barra espaciadora no arrancó la reproducción"


def _payload_largo(title="Cancion Larga"):
    """Canción con muchas secciones/líneas para que la partitura requiera scroll."""
    secciones = []
    for s in range(8):
        lineas = []
        for ln in range(4):
            lineas.append({
                "order": ln + 1, "type": "lyric",
                "content": f"Linea {s}-{ln} con algo de letra para ocupar alto",
                "beat_start": (s * 16) + ln * 4, "beat_duration": 4,
                "chords": [{"chord_name": "C", "char_position": 0,
                            "beat_offset": (s * 16) + ln * 4}],
            })
        secciones.append({"name": f"Seccion {s}", "order": s + 1, "lines": lineas})
    return {"title": title, "artist": "Tester", "bpm": 240, "sections": secciones}


def test_autoscroll_mantiene_visible_el_acorde_activo(page, live_server, api):
    """El auto-scroll sigue al acorde activo: tras reproducir un rato en una canción larga, el
    acorde activo (.active) queda dentro del viewport del contenedor (T-019), no desfasado."""
    wipe_songs(api)
    sid = api.post("/songs/", json=_payload_largo()).json()["id"]
    page.goto(live_server + f"/static/index.html?songId={sid}", wait_until="networkidle")
    page.wait_for_selector(".chord-container, .chord-pill", timeout=8000)

    _apagar_cuenta(page)   # sin pre-roll: medir el auto-scroll durante la reproducción real
    page.locator("#score-container").click()
    page.click("#btn-play-pause")
    page.wait_for_timeout(2500)  # dejar avanzar varios acordes
    page.click("#btn-play-pause")  # pausar
    page.wait_for_timeout(600)    # que termine el scroll suave

    visible = page.evaluate("""() => {
        const active = document.querySelector('.chord-container.active, .chord-pill.active');
        if (!active) return null;
        const c = document.getElementById('score-container').getBoundingClientRect();
        const e = active.getBoundingClientRect();
        // El acorde activo está dentro del viewport del contenedor (con margen).
        return e.bottom > c.top && e.top < c.bottom;
    }""")
    assert visible is True, "el acorde activo no quedó visible tras el auto-scroll"
    # Y efectivamente hubo scroll (no se quedó arriba del todo).
    assert page.evaluate("document.getElementById('score-container').scrollTop") > 0


def test_acorde_activo_tiene_glow(page, live_server, api):
    """T-086 (V3-F1 teleprompter espectacular): al reproducir, el acorde activo recibe el realce
    visual (glow coral) — su box-shadow computado deja de ser 'none'. Solo CSS; la estructura del
    render no cambia (sigue habiendo acordes, como verifican los demás tests)."""
    _crear_y_abrir(page, live_server, api, title="Cancion Glow")
    _apagar_cuenta(page)   # sin pre-roll: que el acorde activo aparezca ya
    page.locator("#score-container").click()
    page.click("#btn-play-pause")
    page.wait_for_timeout(700)
    page.click("#btn-play-pause")  # pausar: el acorde activo conserva la clase .active
    glow = page.evaluate("""() => {
        const el = document.querySelector('.chord-container.active, .chord-pill.active');
        if (!el) return null;
        return getComputedStyle(el).boxShadow;
    }""")
    assert glow and glow != "none", f"el acorde activo no tiene glow: {glow}"


def test_bolita_de_posicion_avanza(page, live_server, api):
    """T-088 (V3-F2): la bolita de posición progresa con la reproducción — el relleno
    (#song-progress-fill) pasa de 0% y se muestra la sección actual. Todo derivado del beat
    existente; el motor (sync_engine.js) no se toca."""
    wipe_songs(api)
    sid = api.post("/songs/", json=_payload_largo()).json()["id"]
    page.goto(live_server + f"/static/index.html?songId={sid}", wait_until="networkidle")
    page.wait_for_selector(".chord-container, .chord-pill", timeout=8000)
    _apagar_cuenta(page)   # sin pre-roll: medir el avance de la bolita durante la reproducción
    page.locator("#score-container").click()
    page.click("#btn-play-pause")
    page.wait_for_timeout(1200)
    page.click("#btn-play-pause")  # pausar
    width = page.evaluate("() => document.getElementById('song-progress-fill').style.width")
    pct = float(width.replace("%", "")) if width and width.endswith("%") else 0.0
    assert pct > 0.0, f"la bolita no avanzó: {width!r}"
    seccion = page.inner_text("#current-section-display").strip()
    assert seccion != "", "no se muestra la sección actual"


def test_modo_directo_alterna_y_oculta_barra(page, live_server, api):
    """T-089 (V3-F4): el Modo Directo añade la clase `stage-mode` (escenario sin distracciones:
    oculta la barra superior y agranda la letra) y alterna al volver a pulsar. Funciona aunque el
    navegador bloquee la pantalla completa (la clase es independiente del Fullscreen API). Solo
    CSS/JS de control; el motor (sync_engine.js) no se toca."""
    _crear_y_abrir(page, live_server, api, title="Cancion Directo")

    def top_display():
        return page.evaluate("() => getComputedStyle(document.querySelector('.top-bar')).display")

    assert "stage-mode" not in (page.get_attribute("body", "class") or "")
    assert top_display() != "none"
    page.click("#btn-stage")
    assert "stage-mode" in (page.get_attribute("body", "class") or "")
    assert top_display() == "none", "el Modo Directo no oculta la barra superior"
    # La letra de la partitura es mayor en escenario.
    lyric_fs = page.evaluate(
        "() => { const e = document.querySelector('.line-lyric'); return e ? parseFloat(getComputedStyle(e).fontSize) : null; }")
    if lyric_fs is not None:
        assert lyric_fs > 24, f"la letra no se agranda en escenario ({lyric_fs}px)"
    page.click("#btn-stage")
    assert "stage-mode" not in (page.get_attribute("body", "class") or "")
    assert top_display() != "none"


def test_afinador_detecta_y_abre(page, live_server, api):
    """T-091 (V3-F4): la detección de tono (función pura por autocorrelación) reconoce una onda
    sintética de 440 Hz como La4, y el panel del afinador abre/cierra. La detección se prueba sin
    micrófono (función pura `bfDetectPitch`); el plumbing del micro va aparte."""
    _crear_y_abrir(page, live_server, api, title="Cancion Afinador")
    freq = page.evaluate("""() => {
        const sr = 44100, N = 2048, f = 440;
        const buf = new Float32Array(N);
        for (let i = 0; i < N; i++) buf[i] = Math.sin(2 * Math.PI * f * i / sr);
        return window.bfDetectPitch(buf, sr);
    }""")
    assert abs(freq - 440) < 8, f"detección de 440 Hz incorrecta: {freq}"
    note = page.evaluate("() => window.bfFreqToNote(440)")
    assert note["name"] == "La" and note["octave"] == 4, note
    assert page.is_visible("#tuner-panel") is False
    page.click("#btn-tuner")
    assert page.is_visible("#tuner-panel") is True
    page.click("#tuner-close")
    assert page.is_visible("#tuner-panel") is False


def test_pasapaginas_hace_scroll(page, live_server, api):
    """T-092 (V3-F4): el pasapáginas (PageDown, como envían los pedales Bluetooth) hace scroll de
    una página en la partitura cuando no hay setlist. Manos libres en el atril."""
    wipe_songs(api)
    sid = api.post("/songs/", json=_payload_largo()).json()["id"]
    page.goto(live_server + f"/static/index.html?songId={sid}", wait_until="networkidle")
    page.wait_for_selector(".chord-container, .chord-pill", timeout=8000)
    page.locator("#score-container").click()
    before = page.evaluate("document.getElementById('score-container').scrollTop")
    page.keyboard.press("PageDown")
    page.wait_for_timeout(600)
    after = page.evaluate("document.getElementById('score-container').scrollTop")
    assert after > before, f"el pasapáginas no avanzó la partitura ({before} -> {after})"


def test_video_de_referencia_youtube(page, live_server, api):
    """T-090 (V3-F4): si la canción tiene reference_url de YouTube, aparece el botón 🎬 y al pulsarlo
    se embebe el iframe del vídeo (id parseado del enlace)."""
    wipe_songs(api)
    payload = sample_song_payload(title="Con Referencia")
    payload["reference_url"] = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    sid = api.post("/songs/", json=payload).json()["id"]
    page.goto(live_server + f"/static/index.html?songId={sid}", wait_until="networkidle")
    page.wait_for_selector(".chord-container, .chord-pill", timeout=8000)
    assert page.is_visible("#btn-reference"), "no aparece el botón de vídeo de referencia"
    page.click("#btn-reference")
    src = page.get_attribute("#reference-embed iframe", "src")
    assert src and "youtube.com/embed/dQw4w9WgXcQ" in src, f"iframe de referencia incorrecto: {src!r}"


def test_sin_referencia_no_hay_boton(page, live_server, api):
    """T-090: una canción sin reference_url no muestra el botón de vídeo de referencia."""
    _crear_y_abrir(page, live_server, api, title="Sin Referencia")
    assert page.is_visible("#btn-reference") is False


def test_export_pdf_oculta_controles(page, live_server, api):
    """El botón de PDF existe y, en media 'print', se ocultan los controles y la partitura
    queda visible (Fase 5). No imprime de verdad; emula el media print para validar el CSS."""
    _crear_y_abrir(page, live_server, api, title="Cancion PDF")
    assert page.locator("#btn-print").count() == 1

    page.emulate_media(media="print")
    page.wait_for_timeout(150)
    # La barra inferior de controles se oculta al imprimir...
    assert page.locator(".bottom-bar").is_visible() is False
    # ...y la partitura sigue visible.
    assert page.locator("#score-content").is_visible() is True
    page.emulate_media(media="screen")


def test_transponer_cambia_los_acordes(page, live_server, api):
    _crear_y_abrir(page, live_server, api)
    acorde = page.locator(".chord-container, .chord-pill").first
    original = acorde.inner_text().strip()
    page.click("#btn-key-up")  # +1 semitono
    page.wait_for_timeout(150)
    nuevo = acorde.inner_text().strip()
    assert nuevo != original, f"el acorde no cambió al transponer ({original})"
    assert page.inner_text("#key-value") in ("+1", "1")
