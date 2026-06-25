"""
E2E T-134 — Agenda más limpia: el borrar se mueve a un menú "⋯".

La fila de evento mantiene visibles los botones de asistencia, el hilo y el estado de booking; solo
el BORRAR (data-act="del") se esconde tras un menú "⋯" para reducir ruido. Ningún e2e usa ese borrar.
"""

import pytest

pytestmark = pytest.mark.e2e


def test_agenda_menu_oculta_borrar(page, live_server, api):
    bid = api.post("/bands/", json={"name": "Banda Agenda Menu"}).json()["id"]
    api.post(f"/bands/{bid}/events/",
             json={"type": "concert", "title": "Bolo Menu", "starts_at": "2099-08-08T20:00:00"})

    page.goto(live_server + f"/static/band.html?id={bid}", wait_until="networkidle")
    page.click('.bf-tab[data-tab="agenda"]')
    page.wait_for_selector('.setlist-song:has-text("Bolo Menu")', timeout=8000)
    row = page.locator('.setlist-song:has-text("Bolo Menu")')

    # Los botones de asistencia siguen visibles fuera del menú.
    assert row.locator(".att-btn").count() == 3
    # El borrar arranca OCULTO (dentro del menú ⋯).
    assert row.locator(".ev-more-menu").get_attribute("hidden") is not None
    assert row.locator('[data-act="del"]').is_visible() is False

    # Abrir el ⋯ revela el borrar.
    row.locator('[data-act="more"]').click()
    page.wait_for_selector('.setlist-song:has-text("Bolo Menu") [data-act="del"]',
                           state="visible", timeout=5000)
