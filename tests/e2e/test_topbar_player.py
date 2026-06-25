"""
E2E T-138 — Top-bar del reproductor ordenada (3 zonas + separadores, sin estilos inline).

Los botones de herramienta pasan de estilos inline a la clase `.tool-btn`, agrupados en 3 zonas
(transporte/tempo · herramientas · navegación). Se conservan ids y aria-labels (el motor no se toca).
"""

import pytest

from tests.conftest import sample_song_payload, wipe_songs

pytestmark = pytest.mark.e2e


def test_topbar_player_ordenada(page, live_server, api):
    wipe_songs(api)
    sid = api.post("/songs/", json=sample_song_payload(title="Cancion Topbar")).json()["id"]
    page.goto(live_server + f"/static/index.html?songId={sid}", wait_until="networkidle")
    page.wait_for_selector(".chord-container, .chord-pill", timeout=8000)

    # 3 zonas agrupadas.
    assert page.locator(".top-bar .tb-zone").count() == 3
    # Los botones de herramienta usan .tool-btn.
    assert page.locator("#btn-tuner.tool-btn").count() == 1
    assert page.locator("#btn-print.tool-btn").count() == 1
    # btn-tuner ya no lleva fondo inline (movido a la clase).
    assert "background" not in (page.get_attribute("#btn-tuner", "style") or "")
    # aria-labels intactos (regresión).
    assert page.get_attribute("#btn-key-save", "aria-label") == "Guardar tono"
    assert page.get_attribute("#btn-tuner", "aria-label") == "Afinador"
    # Y los iconos SVG siguen pintándose (T-123): cada herramienta tiene su <svg>.
    assert page.locator("#btn-tuner svg").count() == 1
