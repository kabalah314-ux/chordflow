"""
E2E T-145 — Duplicar un setlist.

El botón "duplicar" de la tarjeta crea una copia ("<nombre> (copia)") con las mismas canciones.
"""

import pytest

from tests.conftest import sample_song_payload

pytestmark = pytest.mark.e2e


def test_duplicar_setlist(page, live_server, api):
    a = api.post("/songs/", json=sample_song_payload(title="Dup Song")).json()["id"]
    api.post("/setlists/", json={"name": "Original SL", "items": [{"song_id": a, "note": None}]})

    page.goto(live_server + "/static/setlists.html", wait_until="networkidle")
    page.wait_for_selector('.song-card:has-text("Original SL")', timeout=8000)
    card = page.locator('.song-card:has-text("Original SL")').first
    card.hover()
    card.locator('[data-act="dup"]').click()

    page.wait_for_selector('.song-card:has-text("Original SL (copia)")', timeout=8000)
    # La copia tiene el mismo contenido (vía API).
    copia = next(s for s in api.get("/setlists/").json() if s["name"] == "Original SL (copia)")
    items = api.get(f"/setlists/{copia['id']}").json()["items"]
    assert [it["song_id"] for it in items] == [a]
