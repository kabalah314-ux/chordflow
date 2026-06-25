"""
E2E T-146 — Banda(s) en el lateral.

Bajo "Bandas" en el shell aparecen mis bandas con avatar de color; un clic abre `band.html?id=`.
"""

import pytest

pytestmark = pytest.mark.e2e


def test_banda_en_lateral(page, live_server, api):
    bid = api.post("/bands/", json={"name": "Banda Lateral"}).json()["id"]

    page.goto(live_server + "/static/app.html", wait_until="networkidle")
    page.wait_for_selector("#bf-bands-subnav .bf-subnav-item", timeout=8000)
    item = page.locator(f'#bf-bands-subnav a[href="band.html?id={bid}"]')
    assert item.count() == 1
    assert "Banda Lateral" in item.inner_text()
    assert item.locator(".bf-avatar").count() == 1   # avatar de color

    item.click()
    page.wait_for_url(f"**/band.html?id={bid}", timeout=8000)
