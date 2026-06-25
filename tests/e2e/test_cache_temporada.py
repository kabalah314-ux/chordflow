"""
E2E T-152 — Caché por temporada (agregación por fechas).

La sección Finanzas de la banda añade un resumen "Por temporada": agrega los movimientos por año
natural (ingresos / gastos / neto) en el cliente, sin backend nuevo. Con movimientos en dos
temporadas, la agregación las separa correctamente y las ordena de la más reciente a la más antigua.
"""

import pytest

from tests.conftest import TEST_USER_ID

pytestmark = pytest.mark.e2e


def _seed(api, bid, **kw):
    r = api.post(f"/bands/{bid}/transactions", json=kw)
    assert r.status_code == 201, r.text
    return r.json()


def test_cache_por_temporada_separa_dos_temporadas(page, live_server, api):
    bid = api.post("/bands/", json={"name": "Banda Temporadas"}).json()["id"]
    # Temporada 2024: un ingreso de 500.
    _seed(api, bid, type="income", description="Bolo 2024", amount="500.00",
          paid_by=TEST_USER_ID, date="2024-08-15T21:00:00")
    # Temporada 2025: ingreso 800 y gasto 300 → neto 500.
    _seed(api, bid, type="income", description="Bolo 2025", amount="800.00",
          paid_by=TEST_USER_ID, date="2025-06-10T21:00:00")
    _seed(api, bid, type="expense", description="Local 2025", amount="300.00",
          paid_by=TEST_USER_ID, date="2025-06-11T10:00:00")

    page.goto(live_server + f"/static/band.html?id={bid}", wait_until="networkidle")
    page.click('.bf-tab[data-tab="finanzas"]')
    page.wait_for_selector("#b-seasons li", timeout=8000)

    rows = page.locator("#b-seasons li")
    assert rows.count() == 2, "deben aparecer dos temporadas"

    # Ordenadas de la más reciente a la más antigua.
    primera = rows.nth(0).inner_text()
    segunda = rows.nth(1).inner_text()
    assert "Temporada 2025" in primera and "500.00" in primera   # neto 800−300
    assert "Temporada 2024" in segunda and "500.00" in segunda   # neto 500−0


def test_aggregacion_pura_por_temporada(page, live_server, api):
    """La función pura bfFinanceBySeason separa por año y calcula ingresos/gastos/neto."""
    bid = api.post("/bands/", json={"name": "Banda Pura"}).json()["id"]
    page.goto(live_server + f"/static/band.html?id={bid}", wait_until="networkidle")
    page.wait_for_function("typeof window.bfFinanceBySeason === 'function'", timeout=8000)

    result = page.evaluate(
        """() => window.bfFinanceBySeason([
            { type: 'income',  amount: '500.00', date: '2024-08-15T21:00:00' },
            { type: 'income',  amount: '800.00', date: '2025-06-10T21:00:00' },
            { type: 'expense', amount: '300.00', date: '2025-06-11T10:00:00' },
            { type: 'expense', amount: '50.00' }   // sin fecha → se ignora
        ])"""
    )
    assert [s["year"] for s in result] == [2025, 2024]   # descendente
    by_year = {s["year"]: s for s in result}
    assert by_year[2025]["income"] == 800 and by_year[2025]["expense"] == 300
    assert by_year[2025]["net"] == 500
    assert by_year[2024]["income"] == 500 and by_year[2024]["net"] == 500
