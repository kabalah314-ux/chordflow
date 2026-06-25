"""
E2E T-150 — Modo claro a la par (remate en legacy).

Tras hacer que los tokens de texto/fondo de `style.css` hereden de `bf-*` (como T-120 hizo con el
acento), el contenido legacy (p. ej. las tarjetas de la Biblioteca) adapta texto y fondo al modo claro.
"""

import pytest

from tests.conftest import sample_song_payload

pytestmark = pytest.mark.e2e


def test_tarjeta_legacy_adapta_al_claro(page, live_server, api):
    api.post("/songs/", json=sample_song_payload(title="Light Mode Song"))
    page.goto(live_server + "/static/library.html", wait_until="networkidle")
    page.wait_for_selector(".song-card", timeout=8000)

    def color():
        return page.evaluate("() => getComputedStyle(document.querySelector('.song-card')).color")

    def bg():
        return page.evaluate(
            "() => getComputedStyle(document.querySelector('.song-card')).backgroundColor")

    dark_c, dark_bg = color(), bg()
    page.evaluate("document.documentElement.dataset.theme = 'light'")
    light_c, light_bg = color(), bg()

    assert dark_c != light_c, f"el texto legacy no adapta al claro ({dark_c} -> {light_c})"
    assert dark_bg != light_bg, f"el fondo legacy no adapta al claro ({dark_bg} -> {light_bg})"
