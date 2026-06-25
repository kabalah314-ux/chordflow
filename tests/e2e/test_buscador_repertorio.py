"""
E2E T-144 — Buscador en el repertorio de banda (filtro cliente).

La pestaña Repertorio gana una caja de búsqueda que oculta/mostra las canciones por título/artista.
"""

import pytest

from tests.conftest import sample_song_payload

pytestmark = pytest.mark.e2e


def test_buscador_repertorio_filtra(page, live_server, api):
    bid = api.post("/bands/", json={"name": "Banda Buscador"}).json()["id"]
    api.post(f"/bands/{bid}/songs/", json=sample_song_payload(title="Wonderwall"))
    api.post(f"/bands/{bid}/songs/", json=sample_song_payload(title="Creep"))

    page.goto(live_server + f"/static/band.html?id={bid}", wait_until="networkidle")
    page.click('.bf-tab[data-tab="repertorio"]')
    page.wait_for_selector("#b-repertoire .setlist-song", timeout=8000)
    assert page.locator("#b-repertoire .setlist-song").count() == 2

    page.fill("#b-rep-search", "wonder")
    page.wait_for_function(
        "[...document.querySelectorAll('#b-repertoire .setlist-song')]"
        ".filter(li => li.style.display !== 'none').length === 1", timeout=5000)
    visible = page.locator("#b-repertoire .setlist-song:visible")
    assert visible.count() == 1
    assert "Wonderwall" in visible.first.inner_text()
