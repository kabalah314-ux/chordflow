"""
E2E T-128 — Pestañas de banda en móvil: fade en los bordes + scroll-snap.

En un viewport estrecho las 9 pestañas desbordan; un `mask-image` con fade en ambos bordes insinúa
que hay más a los lados, y siguen clicándose. El motor/contenido no cambia.
"""

import pytest

pytestmark = pytest.mark.e2e


def test_pestanas_fade_movil(page, live_server, api):
    bid = api.post("/bands/", json={"name": "Banda Tabs"}).json()["id"]
    page.set_viewport_size({"width": 390, "height": 800})
    page.goto(live_server + f"/static/band.html?id={bid}", wait_until="networkidle")
    tabs = page.locator(".bf-tabs")
    page.wait_for_selector(".bf-tabs", timeout=8000)

    # Hay fade (mask-image) en móvil.
    mask = tabs.evaluate(
        "el => getComputedStyle(el).maskImage || getComputedStyle(el).webkitMaskImage")
    assert mask and mask != "none", f"no hay fade en las pestañas móvil: {mask!r}"

    # Y las pestañas desbordan (hay scroll horizontal).
    assert tabs.evaluate("el => el.scrollWidth > el.clientWidth"), "las pestañas no desbordan en móvil"

    # Siguen clicándose.
    page.click('.bf-tab[data-tab="agenda"]')
    assert page.get_attribute('.bf-tab[data-tab="agenda"]', "aria-selected") == "true"
