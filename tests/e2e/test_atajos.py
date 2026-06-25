"""
E2E T-141 — Hoja de atajos del reproductor.

Un botón "?" abre un modal con los atajos de teclado (espacio, av/re pág, esc). Se cierra con Esc.
"""

import pytest

from tests.conftest import sample_song_payload, wipe_songs

pytestmark = pytest.mark.e2e


def test_atajos_modal(page, live_server, api):
    wipe_songs(api)
    sid = api.post("/songs/", json=sample_song_payload(title="Cancion Atajos")).json()["id"]
    page.goto(live_server + f"/static/index.html?songId={sid}", wait_until="networkidle")
    page.wait_for_selector(".chord-container, .chord-pill", timeout=8000)

    page.click("#btn-shortcuts")
    page.wait_for_selector(".modal-card", timeout=5000)
    txt = page.inner_text(".modal-card")
    assert "Atajos" in txt and "Reproducir" in txt and "Modo Directo" in txt

    # Se cierra con Esc.
    page.keyboard.press("Escape")
    page.wait_for_selector(".modal-overlay", state="detached", timeout=5000)
