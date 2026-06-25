"""
E2E T-142 — Estados vacíos con CTA.

`bfEmpty(..., { cta: { label, href } })` añade un botón de acción claro. Las vistas agregadas
(agenda/finanzas) sin bandas muestran el vacío con un CTA a "Bandas".
"""

import pytest

from tests.conftest import wipe_bands

pytestmark = pytest.mark.e2e


def test_agenda_vacia_con_cta(page, live_server, api):
    wipe_bands(api)   # sin bandas → /me/events vacío → estado vacío con CTA
    page.goto(live_server + "/static/agenda.html", wait_until="networkidle")
    page.wait_for_selector("#agenda .bf-empty", timeout=8000)
    cta = page.locator("#agenda .bf-empty__cta")
    assert cta.count() == 1
    assert cta.get_attribute("href") == "bands.html"
    assert "Bandas" in cta.inner_text()
