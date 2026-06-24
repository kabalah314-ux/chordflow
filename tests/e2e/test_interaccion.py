"""
E2E T-127 — Estados de interacción: lo clicable lo parece (hover/foco/transición).

Se verifica el hover de `.bf-list-item` (antes sin afordancia). El foco accesible (`:focus-visible`)
y la animación de modales se añaden por CSS con guard de `prefers-reduced-motion`.
"""

import pytest

from tests.conftest import wipe_bands

pytestmark = pytest.mark.e2e


def test_bf_list_item_hover_cambia_fondo(page, live_server, api):
    # Sin bandas → el Inicio muestra "Primeros pasos" con filas `.bf-list-item`.
    wipe_bands(api)
    page.goto(live_server + "/static/app.html", wait_until="networkidle")
    page.wait_for_selector("#home-onboarding .bf-list-item", timeout=8000)
    item = page.locator("#home-onboarding .bf-list-item").first

    def bg():
        return item.evaluate("el => getComputedStyle(el).backgroundColor")

    before = bg()
    item.hover()
    page.wait_for_timeout(250)  # dejar correr la transición
    after = bg()
    assert before != after, f"el hover de .bf-list-item no cambia el fondo ({before} -> {after})"
