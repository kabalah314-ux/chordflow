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


def test_buscador_biblioteca_legible_en_claro(page, live_server, api):
    """T-V5-01: `.search-box` antes tenía fondo negro hardcodeado (rgba(0,0,0,.5)) → en modo claro
    quedaba una barra oscura con texto oscuro (invisible). Tras tokenizar, el fondo del buscador
    adapta al tema y NO es casi-negro en claro."""
    page.goto(live_server + "/static/library.html", wait_until="networkidle")
    page.wait_for_selector("#search-input", timeout=8000)

    def bg():
        return page.evaluate(
            "() => getComputedStyle(document.getElementById('search-input')).backgroundColor")

    dark_bg = bg()
    page.evaluate("document.documentElement.dataset.theme = 'light'")
    light_bg = bg()
    assert dark_bg != light_bg, f"el buscador no adapta al claro ({dark_bg} -> {light_bg})"
    # En claro, el fondo debe ser CLARO (suma RGB alta), no la barra negra de antes.
    rgb = page.evaluate("""() => {
        const c = getComputedStyle(document.getElementById('search-input')).backgroundColor;
        const m = c.match(/\\d+/g).map(Number);
        return m[0] + m[1] + m[2];
    }""")
    assert rgb > 600, f"el buscador sigue oscuro en modo claro (suma RGB {rgb})"
