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
    assert "0.0" in page.inner_text("#current-beat-display")
    page.click("#btn-play-pause")
    page.wait_for_timeout(900)  # dejar correr ~1s de reproducción
    page.click("#btn-play-pause")  # pausar
    beat_txt = page.inner_text("#current-beat-display")
    # El beat debe haber avanzado por encima de 0.0
    valor = float(beat_txt.split(":")[1].strip())
    assert valor > 0.0, f"el beat no avanzó: {beat_txt}"


def test_accesibilidad_aria_y_atajo_espacio(page, live_server, api):
    """Los botones de emoji tienen aria-label y la barra espaciadora alterna play/pausa (T-021)."""
    _crear_y_abrir(page, live_server, api)
    # aria-label en botones de icono/emoji.
    for sel, etiqueta in [("#btn-stop", "Detener"), ("#btn-key-save", "Guardar tono"),
                          ("#btn-bpm-up", "Subir BPM")]:
        assert page.get_attribute(sel, "aria-label") == etiqueta

    # Atajo: barra espaciadora arranca la reproducción.
    page.locator("#score-container").click()  # foco fuera de inputs
    page.keyboard.press("Space")
    page.wait_for_timeout(600)
    page.keyboard.press("Space")  # pausar
    valor = float(page.inner_text("#current-beat-display").split(":")[1].strip())
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
