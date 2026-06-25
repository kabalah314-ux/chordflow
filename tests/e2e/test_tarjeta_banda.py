"""
E2E T-132 — Tarjeta de banda rica en "Mis bandas".

Cada banda muestra avatar de color + iniciales, rol/miembros/nº de canciones y (si lo hay) el próximo
evento. Se conservan los selectores `.song-card`/`.card-main[data-act="open"]` que usan los tests.
"""

import pytest

from tests.conftest import sample_song_payload

pytestmark = pytest.mark.e2e


def test_tarjeta_banda_avatar_y_song_count(page, live_server, api):
    bid = api.post("/bands/", json={"name": "Banda Tarjeta"}).json()["id"]
    api.post(f"/bands/{bid}/songs/", json=sample_song_payload(title="Una Cancion"))

    page.goto(live_server + "/static/bands.html", wait_until="networkidle")
    page.wait_for_selector('.song-card:has-text("Banda Tarjeta")', timeout=8000)
    card = page.locator('.song-card:has-text("Banda Tarjeta")')

    # Avatar de color con inicial y el contador de canciones.
    assert card.locator(".bf-avatar").count() == 1
    assert "1 canción" in card.inner_text()

    # Sigue abriéndose (selector intacto).
    card.locator('.card-main[data-act="open"]').click()
    page.wait_for_url("**/band.html?id=*", timeout=8000)
