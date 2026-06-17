"""
E2E de la biblioteca global (Explorar) — `biblioteca-global.html` (V3-F9, T-103).

Buscar en el catálogo, el reclamo "ponla aquí" y abrir el detalle (preview + importar + valorar).
"""

import pytest

from tests.conftest import sample_song_payload

pytestmark = pytest.mark.e2e


def _publish(api, title="Wonderwall", artist="Oasis"):
    p = sample_song_payload(title=title)
    p["artist"] = artist
    sid = api.post("/songs/", json=p).json()["id"]
    api.post("/catalog/publish", json={"song_id": sid})


def test_explorar_busca_y_abre_detalle(page, live_server, api):
    _publish(api, "Wonderwall", "Oasis")
    page.goto(live_server + "/static/biblioteca-global.html", wait_until="networkidle")
    page.wait_for_selector("#cat-results", timeout=8000)

    # El reclamo "ponla aquí" lleva al editor.
    assert page.locator('a[href="editor.html"]').count() >= 1

    # Buscar y ver el resultado.
    page.fill("#cat-search", "wonder")
    page.click("#cat-search-btn")
    page.wait_for_selector("#cat-results [data-score]", timeout=8000)
    assert "Wonderwall" in page.inner_text("#cat-results")

    # Abrir el detalle: banner + importar + valoración por estrellas.
    page.click("#cat-results [data-score]")
    page.wait_for_selector("#cat-back", timeout=8000)
    assert "Wonderwall" in page.inner_text(".bf-band-banner")
    assert page.locator("#cat-import").count() == 1
    assert page.locator("#cat-stars [data-star]").count() == 5


def test_explorar_en_el_lateral(page, live_server, api):
    # "Explorar" es un item del lateral del shell y navega a la biblioteca global.
    page.goto(live_server + "/static/app.html", wait_until="networkidle")
    page.wait_for_selector(".bf-sidebar", timeout=8000)
    page.click('.bf-sidebar a.bf-nav-item:has-text("Explorar")')
    page.wait_for_url("**/biblioteca-global.html", timeout=8000)
    assert page.url.endswith("biblioteca-global.html")
