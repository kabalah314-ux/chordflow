"""
E2E V6-F9b — Explorar como hub de la red: bolos abiertos (postularse desde la UI), directorio de
salas, ficha pública y "Mis perfiles" con las candidaturas recibidas.
"""

import pytest

pytestmark = pytest.mark.e2e


def _setup(api):
    bid = api.post("/bands/", json={"name": "Banda Red E2E"}).json()["id"]
    venue = api.post("/me/pro-profiles", json={
        "kind": "venue", "name": "Sala Red E2E", "zone": "Lleida", "capacity": 90,
        "styles": ["blues"], "phone": "611222333"}).json()
    call = api.post(f"/me/pro-profiles/{venue['id']}/gig-calls", json={
        "title": "Bolo de blues E2E", "starts_at": "2099-10-10T21:30:00", "deal_type": "door",
        "styles": ["blues"]}).json()
    return bid, venue, call


def test_postularse_desde_bolos_abiertos(page, live_server, api):
    bid, venue, call = _setup(api)
    page.goto(live_server + "/static/red.html#bolos", wait_until="networkidle")
    card = f'.rd-call[data-call="{call["id"]}"]'
    page.wait_for_selector(card, timeout=8000)
    assert "Sala Red E2E" in page.inner_text(card)
    page.click(card + ' [data-act="apply"]')
    page.wait_for_selector(".bf-dialog #rd-a-band", timeout=8000)
    page.select_option("#rd-a-band", bid)
    page.fill("#rd-a-msg", "Tocamos blues del Delta")
    page.click('.bf-dialog [data-bfd-act="1"]')
    page.wait_for_selector(card + " .bf-badge", timeout=8000)
    apps = api.get(f"/bands/{bid}/gig-applications").json()
    assert apps[0]["message"] == "Tocamos blues del Delta"

    # La sala lo ve en Mis perfiles → Candidaturas (1) y en Mensajes
    page.goto(live_server + "/static/red.html#mios", wait_until="networkidle")
    page.wait_for_selector(f'[data-own-call="{call["id"]}"] [data-act="apps"]', timeout=8000)
    assert "(1)" in page.inner_text(f'[data-own-call="{call["id"]}"] [data-act="apps"]')
    page.goto(live_server + "/static/red.html#mensajes", wait_until="networkidle")
    page.wait_for_selector(".rd-msg", timeout=8000)
    assert "Tocamos blues del Delta" in page.inner_text("#rd-msgs")


def test_directorio_y_ficha_publica(page, live_server, api):
    _, venue, _ = _setup(api)
    page.goto(live_server + "/static/red.html#salas", wait_until="networkidle")
    page.fill("#rd-zone", "lleida")
    page.wait_for_selector(f'a.rd-pro[href="ficha.html?id={venue["id"]}"]', timeout=8000)
    page.click(f'a.rd-pro[href="ficha.html?id={venue["id"]}"]')
    page.wait_for_selector(".pub-title", timeout=8000)
    txt = page.inner_text("#pub-card")
    assert "Sala Red E2E" in txt and "Bolo de blues E2E" in txt
    # Es mi ficha: se ofrece editar; el teléfono lo ve el dueño
    assert page.locator('a[href="red.html#mios"]').count() == 1
