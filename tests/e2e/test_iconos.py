"""
E2E T-122 — `icons.js` disponible en el reproductor y el editor.

Hasta ahora `icons.js` (que define `bfIcon`) NO se cargaba en `index.html` (player) ni en
`editor.html`; sin él no se pueden sustituir los emoji por SVG (T-123/T-124). Aquí se comprueba
que `bfIcon` es una función en ambas páginas y que devuelve un `<svg>` para los iconos nuevos.
"""

import pytest

from tests.conftest import sample_song_payload, wipe_songs

pytestmark = pytest.mark.e2e


def test_player_iconos_svg(page, live_server, api):
    """T-123: los botones de control del reproductor muestran SVG (no emoji), conservan su
    aria-label y el play/pausa sigue arrancando la reproducción (el motor no se toca)."""
    wipe_songs(api)
    sid = api.post("/songs/", json=sample_song_payload(title="Iconos SVG")).json()["id"]
    page.goto(live_server + f"/static/index.html?songId={sid}", wait_until="networkidle")
    page.wait_for_selector(".chord-container, .chord-pill", timeout=8000)

    # Cada botón de control contiene exactamente un <svg> (ya no un emoji).
    for sel in ["#btn-stop", "#btn-metronome", "#btn-stage", "#btn-key-save",
                "#btn-print", "#btn-tuner", "#btn-play-pause"]:
        assert page.locator(f"{sel} svg").count() == 1, f"{sel} no tiene SVG"

    # aria-label preservado (accesibilidad, regresión T-021).
    assert page.get_attribute("#btn-stop", "aria-label") == "Detener"
    assert page.get_attribute("#btn-key-save", "aria-label") == "Guardar tono"

    # El play/pausa sigue arrancando la reproducción.
    page.locator("#score-container").click()
    page.click("#btn-play-pause")
    page.wait_for_timeout(700)
    page.click("#btn-play-pause")
    valor = float(page.get_attribute("#current-beat-display", "data-beat"))
    assert valor > 0.0, "el play con icono SVG no arrancó la reproducción"


def test_setlists_iconos_y_quitar_no_es_borrar(page, live_server, api):
    """T-124: en setlists los botones de acción muestran SVG; 'quitar de la lista' es NEUTRO
    (sin clase danger) y solo el BORRADO real conserva el rojo (danger)."""
    a = api.post("/songs/", json=sample_song_payload(title="SL Icon Song")).json()["id"]
    api.post("/setlists/", json={"name": "SL Iconos", "items": [{"song_id": a, "note": None}]})

    page.goto(live_server + "/static/setlists.html", wait_until="networkidle")
    page.wait_for_selector('.song-card:has-text("SL Iconos")', timeout=8000)
    card = page.locator('.song-card:has-text("SL Iconos")')

    # Editar y Borrar: ambos con SVG. Borrar (del) conserva danger; editar es neutro.
    assert card.locator('[data-act="edit"] svg').count() == 1
    assert card.locator('[data-act="del"] svg').count() == 1
    assert "danger" in (card.locator('[data-act="del"]').get_attribute("class") or "")
    assert "danger" not in (card.locator('[data-act="edit"]').get_attribute("class") or "")

    # En el editor, el botón "quitar" (data-rm) es neutro (sin danger) y con SVG.
    card.locator('[data-act="edit"]').click()
    page.wait_for_selector('#sl-selected [data-rm]', timeout=8000)
    rm = page.locator('#sl-selected [data-rm]').first
    assert rm.locator("svg").count() == 1
    assert "danger" not in (rm.get_attribute("class") or ""), "quitar no debe ser danger (rojo)"


def test_iconos_disponibles_en_player(page, live_server):
    page.goto(live_server + "/static/index.html", wait_until="networkidle")
    assert page.evaluate("typeof bfIcon") == "function"
    # Un icono nuevo del reproductor (play) devuelve SVG.
    assert "<svg" in page.evaluate("bfIcon('play')")
    # Varios de los añadidos en T-122 existen (no caen al fallback 'music').
    for name in ("pause", "stop", "save", "printer", "mic", "maximize", "trash", "x"):
        assert "<svg" in page.evaluate("(n) => bfIcon(n)", name)


def test_iconos_disponibles_en_editor(page, live_server):
    page.goto(live_server + "/static/editor.html", wait_until="networkidle")
    assert page.evaluate("typeof bfIcon") == "function"
    assert "<svg" in page.evaluate("bfIcon('edit')")
