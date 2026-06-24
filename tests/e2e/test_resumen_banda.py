"""
E2E T-130 — Resumen de banda útil (Opción B, dos columnas).

La pestaña Resumen (activa por defecto) pinta el dashboard desde GET /bands/{id}/summary:
próximo evento (con "¿Vas?"), último mensaje, mi saldo y contadores. Reemplaza el bloque estático.
"""

import pytest

pytestmark = pytest.mark.e2e


def test_resumen_banda_dashboard(page, live_server, api):
    bid = api.post("/bands/", json={"name": "Banda Resumen UI"}).json()["id"]
    api.post(f"/bands/{bid}/events/",
             json={"type": "concert", "title": "Bolo Resumen UI", "starts_at": "2099-07-07T21:00:00"})

    page.goto(live_server + f"/static/band.html?id={bid}", wait_until="networkidle")
    # El Resumen carga (rejilla de dos columnas), no el "Cargando…" estático.
    page.wait_for_selector(".bs-summary", timeout=8000)
    txt = page.inner_text("#b-summary")
    assert "Próximo evento" in txt and "Bolo Resumen UI" in txt
    assert "Tu saldo" in txt

    # data-tab="resumen" intacto.
    assert page.locator('.bf-tab[data-tab="resumen"]').count() == 1

    # "¿Vas?" tiene los 3 botones y marcar "Voy" se refleja (recarga del resumen).
    assert page.locator("#bs-att .att-btn").count() == 3
    page.click('#bs-att [data-att="yes"]')
    page.wait_for_selector('#bs-att [data-att="yes"].active', timeout=8000)

    # Un acceso rápido a otra pestaña funciona (la pestaña Chat se activa).
    page.click('#b-summary [data-go="chat"]')
    assert page.get_attribute('.bf-tab[data-tab="chat"]', "aria-selected") == "true"
