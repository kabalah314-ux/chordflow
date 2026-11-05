"""
E2E de responsive (móvil/tablet) y PWA (Fase 5).

- Responsive: en un viewport de móvil, las páginas no deben tener scroll HORIZONTAL
  (síntoma típico de layout desbordado en pantallas estrechas).
- PWA: el manifest, el service worker y los iconos se sirven, y las páginas lo enlazan.
"""

import pytest

pytestmark = pytest.mark.e2e

PAGINAS = ["/static/login.html", "/static/library.html", "/static/editor.html",
           "/static/index.html"]


@pytest.mark.parametrize("path", PAGINAS)
def test_sin_scroll_horizontal_en_movil(page, live_server, path):
    page.set_viewport_size({"width": 390, "height": 844})  # ~iPhone 12/13
    page.goto(live_server + path, wait_until="networkidle")
    page.wait_for_timeout(200)
    overflow = page.evaluate(
        "() => document.documentElement.scrollWidth - document.documentElement.clientWidth")
    assert overflow <= 2, f"{path} desborda horizontalmente en móvil ({overflow}px)"


def test_pwa_assets_servidos(api):
    """manifest.json, sw.js e iconos se sirven (200)."""
    m = api.get("/static/manifest.json")
    assert m.status_code == 200
    assert m.json()["name"] == "BandFlow"   # rebranding T-082
    assert api.get("/static/sw.js").status_code == 200
    assert api.get("/static/icons/icon-192.png").status_code == 200


def test_paginas_enlazan_el_manifest(page, live_server):
    page.goto(live_server + "/static/library.html", wait_until="networkidle")
    assert page.locator('link[rel="manifest"]').count() == 1
    assert page.locator('meta[name="theme-color"]').count() == 1


# T-V6-58: el resto de páginas del shell y las públicas, también sin scroll horizontal a 390 px.
PAGINAS_V6 = ["/static/app.html", "/static/agenda.html", "/static/finanzas.html", "/static/chat.html",
              "/static/bands.html", "/static/red.html", "/static/profile.html", "/static/afinador.html",
              "/static/setlists.html", "/static/bienvenida.html?ver", "/static/legal.html"]


@pytest.mark.parametrize("path", PAGINAS_V6)
def test_sin_scroll_horizontal_en_movil_v6(page, live_server, path):
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(live_server + path, wait_until="networkidle")
    page.wait_for_timeout(300)
    overflow = page.evaluate(
        "() => document.documentElement.scrollWidth - document.documentElement.clientWidth")
    assert overflow <= 2, f"{path} desborda horizontalmente en móvil ({overflow}px)"
