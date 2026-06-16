"""
E2E de Finanzas agregadas (`finanzas.html`, Fase 13, T-079).

Muestra mi saldo en cada banda (positivo = me deben; negativo = debo).
"""

import pytest

pytestmark = pytest.mark.e2e


def test_finanzas_muestra_saldo_por_banda(page, live_server, api):
    bid = api.post("/bands/", json={"name": "Banda Cuentas"}).json()["id"]
    api.post(f"/bands/{bid}/transactions",
             json={"type": "expense", "description": "Local", "amount": "50.00", "paid_by_fund": True})

    page.goto(live_server + "/static/finanzas.html", wait_until="networkidle")
    page.wait_for_selector("#finanzas-list", timeout=8000)
    lista = page.inner_text("#finanzas-list")
    assert "Banda Cuentas" in lista
    assert "€" in lista
