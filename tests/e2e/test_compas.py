"""
E2E T-V5-07 — Compases.

- La barra del reproductor muestra el COMPÁS ("Compás N"), no el beat crudo (que va en `data-beat`).
- El editor tiene un selector de compás (2/4·3/4·4/4·6/8) que se persiste y se recarga al editar.
"""

import pytest

from tests.conftest import sample_song_payload, wipe_songs

pytestmark = pytest.mark.e2e


def test_barra_muestra_el_compas(page, live_server, api):
    wipe_songs(api)
    sid = api.post("/songs/", json=sample_song_payload(title="Compas Song")).json()["id"]
    page.goto(live_server + f"/static/index.html?songId={sid}", wait_until="networkidle")
    page.wait_for_selector(".chord-container, .chord-pill", timeout=8000)

    txt = page.inner_text("#current-beat-display")
    assert txt.startswith("Compás"), f"la barra no muestra el compás: {txt!r}"
    # En reposo se está en el compás 1, y el beat crudo (data-beat) es 0.
    assert "Compás 1" in txt
    assert float(page.get_attribute("#current-beat-display", "data-beat")) == 0.0


def test_editor_guarda_y_recarga_el_compas(page, live_server, api):
    wipe_songs(api)
    page.goto(live_server + "/static/editor.html", wait_until="networkidle")
    page.fill("#title", "Vals en 3/4")
    page.select_option("#time-signature", "3/4")
    page.fill("#raw-text", "Verso:\nAm C\nHola compas")
    page.click("#btn-save")
    page.wait_for_url("**/index.html?songId=*", timeout=8000)

    # Se guardó con el compás elegido (GET completo trae time_signature).
    song = next(s for s in api.get("/songs/").json() if s["title"] == "Vals en 3/4")
    full = api.get(f"/songs/{song['id']}").json()
    assert full["time_signature_num"] == 3 and full["time_signature_den"] == 4

    # Al reabrir en el editor, el selector recupera el compás guardado.
    page.goto(live_server + f"/static/editor.html?songId={song['id']}", wait_until="networkidle")
    page.wait_for_selector("#time-signature", timeout=8000)
    assert page.input_value("#time-signature") == "3/4"
