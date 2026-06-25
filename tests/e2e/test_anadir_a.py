"""
E2E T-143 — "Añadir a colección" desde la tarjeta de canción.

Un botón en la tarjeta personal abre un modal con checkboxes de mis colecciones; al confirmar, la
canción se añade a las marcadas (PATCH de pertenencia).
"""

import pytest

from tests.conftest import sample_song_payload

pytestmark = pytest.mark.e2e


def test_anadir_cancion_a_coleccion(page, live_server, api):
    sid = api.post("/songs/", json=sample_song_payload(title="AddTo Song")).json()["id"]
    cid = api.post("/collections/", json={"name": "Mi Coleccion", "song_ids": []}).json()["id"]

    page.goto(live_server + "/static/library.html", wait_until="networkidle")
    page.wait_for_selector('.song-card:has-text("AddTo Song")', timeout=8000)
    card = page.locator('.song-card:has-text("AddTo Song")').first
    card.hover()
    card.locator('[data-act="add-to"]').click()

    page.wait_for_selector(".add-to-list", timeout=5000)
    page.check(f'.add-to-row input[data-cid="{cid}"]')
    page.click('.modal-card [data-act="ok"]')
    # El modal cierra y el PATCH va en segundo plano → esperar al toast de éxito antes de comprobar.
    page.wait_for_selector('.toast:has-text("Añadida")', timeout=8000)

    # La canción quedó en la colección (vía API).
    items = api.get(f"/collections/{cid}").json()["items"]
    assert [it["song_id"] for it in items] == [sid]
