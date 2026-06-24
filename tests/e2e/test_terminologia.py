"""
E2E T-126 — Terminología: la pestaña se llama "Repertorio" (= pool + colecciones) y la sección
temática interna "Colecciones". La clave `data-tab="repertorio"` y los ids NO cambian.
"""

import pytest

pytestmark = pytest.mark.e2e


def test_terminologia_repertorio_colecciones(page, live_server, api):
    bid = api.post("/bands/", json={"name": "Banda Terminologia"}).json()["id"]
    page.goto(live_server + f"/static/band.html?id={bid}", wait_until="networkidle")

    # La pestaña conserva data-tab="repertorio" (clave intacta) y su label visible es "Repertorio".
    page.wait_for_selector('.bf-tab[data-tab="repertorio"]', timeout=8000)
    tab = page.locator('.bf-tab[data-tab="repertorio"]')
    assert tab.inner_text().strip() == "Repertorio"

    tab.click()
    page.wait_for_selector("#b-new-collection", state="visible", timeout=8000)
    panel = page.locator('[data-panel="repertorio"]')
    # La sección temática se llama "Colecciones" y el botón "Nueva colección".
    assert "Colecciones" in panel.inner_text()
    assert "Nueva colección" in page.locator("#b-new-collection").inner_text()
    # El pool sigue siendo "Todas las canciones" (no se renombró).
    assert "Todas las canciones" in panel.inner_text()
