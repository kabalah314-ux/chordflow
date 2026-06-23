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


def test_editar_repertorio_personal_con_nota(page, live_server, api):
    """Editar un repertorio personal desde la UI: el botón ✏️ abre el editor prerrellenado y permite
    poner una nota por canción; al guardar (PATCH) el detalle la muestra."""
    a = api.post("/songs/", json=sample_song_payload(title="SL Edit Cancion")).json()["id"]
    sid = api.post("/setlists/", json={"name": "Repertorio Original",
                                       "items": [{"song_id": a, "note": None}]}).json()["id"]

    page.goto(live_server + "/static/setlists.html", wait_until="networkidle")
    page.wait_for_selector('.song-card:has-text("Repertorio Original")', timeout=8000)
    page.click('.song-card:has-text("Repertorio Original") [data-act="edit"]')
    page.wait_for_selector("#sl-name", timeout=8000)
    assert page.input_value("#sl-name") == "Repertorio Original"

    # Poner una nota por canción (prerrellenada vacía) y renombrar
    page.wait_for_selector('#sl-selected .sl-note', timeout=5000)
    page.fill('#sl-selected .sl-note', "capo 2 acustica")
    page.fill("#sl-name", "Repertorio Editado")
    page.click("#sl-save")
    page.wait_for_selector('.song-card:has-text("Repertorio Editado")', timeout=8000)

    # Persistió vía PATCH (nombre + nota)
    det = api.get(f"/setlists/{sid}").json()
    assert det["name"] == "Repertorio Editado"
    assert det["items"][0]["note"] == "capo 2 acustica"

    # El detalle muestra la nota
    page.click('.song-card:has-text("Repertorio Editado") .card-main[data-act="open"]')
    page.wait_for_selector("#setlist-detail .setlist-song", timeout=8000)
    assert "capo 2 acustica" in page.inner_text("#setlist-detail")
