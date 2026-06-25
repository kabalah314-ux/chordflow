"""
E2E T-133 — Tarjeta de canción con ▶ flotante + franja de color por fuente.

Cada tarjeta de la Biblioteca gana un botón ▶ (revelado en hover, abajo-dcha) que abre el reproductor,
y una franja de color por fuente (`--card-accent`: acento si es personal, color de banda si no).
"""

import pytest

from tests.conftest import sample_song_payload, wipe_songs

pytestmark = pytest.mark.e2e


def test_card_play_y_franja_de_color(page, live_server, api):
    wipe_songs(api)
    sid = api.post("/songs/", json=sample_song_payload(title="Cancion Play")).json()["id"]

    page.goto(live_server + "/static/library.html", wait_until="networkidle")
    page.wait_for_selector('.song-card:has-text("Cancion Play")', timeout=8000)
    card = page.locator('.song-card:has-text("Cancion Play")')

    # El ▶ existe y la franja de color (--card-accent) está puesta.
    assert card.locator(".card-play").count() == 1
    accent = card.evaluate("el => el.style.getPropertyValue('--card-accent')")
    assert accent != "", "no se asignó --card-accent a la tarjeta"

    # El badge de fuente sigue siendo texto (regresión test_library).
    assert "Personal" in card.inner_text()

    # Clic en ▶ → abre el reproductor de esa canción.
    card.hover()
    card.locator(".card-play").click()
    page.wait_for_url(f"**/index.html?songId={sid}", timeout=8000)
