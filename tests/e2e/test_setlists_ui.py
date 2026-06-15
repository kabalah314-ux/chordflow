"""
E2E de repertorios (Fase 5): crear un repertorio con canciones y verlo en orden.
"""

import pytest

from tests.conftest import sample_song_payload

pytestmark = pytest.mark.e2e


def test_crear_y_ver_repertorio(page, live_server, api):
    a = api.post("/songs/", json=sample_song_payload(title="SL Cancion Uno")).json()["id"]
    b = api.post("/songs/", json=sample_song_payload(title="SL Cancion Dos")).json()["id"]

    page.goto(live_server + "/static/setlists.html", wait_until="networkidle")
    page.click("#btn-new-setlist")
    page.wait_for_selector("#sl-name", timeout=8000)
    page.fill("#sl-name", "Bolo E2E")

    # Añadir las dos canciones (por su id, robusto frente a otras canciones en la BD)
    page.click(f'#sl-available button[data-id="{a}"]')
    page.click(f'#sl-available button[data-id="{b}"]')
    # Deben aparecer 2 en la lista de seleccionadas
    page.wait_for_function("document.querySelectorAll('#sl-selected li button[data-rm]').length === 2",
                           timeout=5000)

    page.click("#sl-save")

    # Vuelve a la rejilla y aparece la tarjeta del repertorio
    page.wait_for_selector(".song-card", timeout=8000)
    assert "Bolo E2E" in page.inner_text("#setlist-grid")

    # Abrir el repertorio → lista ordenada con las dos canciones + "Reproducir todo"
    page.click('.song-card .card-main[data-act="open"]')
    page.wait_for_selector("#sl-playall", timeout=8000)
    detalle = page.inner_text("#setlist-detail")
    assert "SL Cancion Uno" in detalle and "SL Cancion Dos" in detalle
