"""
E2E T-148 — Tour la primera vez en un espacio de banda.

La 1ª vez aparece un aviso de bienvenida bajo las pestañas; al pulsar "Entendido" se descarta y no
vuelve (localStorage).
"""

import pytest

pytestmark = pytest.mark.e2e


def test_tour_primera_vez_y_no_repite(page, live_server, api):
    bid = api.post("/bands/", json={"name": "Banda Tour"}).json()["id"]

    page.goto(live_server + f"/static/band.html?id={bid}", wait_until="networkidle")
    page.wait_for_selector(".bf-tour-tip", timeout=8000)
    page.click("#bf-tour-ok")
    page.wait_for_selector(".bf-tour-tip", state="detached", timeout=5000)

    # Recargar: ya no aparece (persistido en localStorage).
    page.reload(wait_until="networkidle")
    page.wait_for_selector(".bf-tabs", timeout=8000)
    assert page.locator(".bf-tour-tip").count() == 0
