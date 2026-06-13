"""
E2E de la biblioteca: estado vacío (L1), aparición de canción (L2), búsqueda (L3).
"""

import pytest

from tests.conftest import sample_song_payload, wipe_songs

pytestmark = pytest.mark.e2e


def test_estado_vacio(page, live_server, api):
    wipe_songs(api)
    page.goto(live_server + "/static/library.html", wait_until="networkidle")
    page.wait_for_selector(".empty-state", timeout=8000)
    assert "Aún no tienes partituras" in page.inner_text(".empty-state")


def test_cancion_aparece_como_tarjeta(page, live_server, api):
    wipe_songs(api)
    api.post("/songs/", json=sample_song_payload(title="Cancion Visible"))
    page.goto(live_server + "/static/library.html", wait_until="networkidle")
    page.wait_for_selector(".song-card", timeout=8000)
    assert "Cancion Visible" in page.inner_text("#song-grid")


def test_busqueda_filtra(page, live_server, api):
    wipe_songs(api)
    api.post("/songs/", json=sample_song_payload(title="Wonderwall"))
    api.post("/songs/", json=sample_song_payload(title="Creep"))
    page.goto(live_server + "/static/library.html", wait_until="networkidle")
    page.wait_for_selector(".song-card", timeout=8000)

    page.fill("#search-input", "wonder")
    page.wait_for_timeout(300)  # la búsqueda es en vivo (input event)
    grid = page.inner_text("#song-grid")
    assert "Wonderwall" in grid
    assert "Creep" not in grid
