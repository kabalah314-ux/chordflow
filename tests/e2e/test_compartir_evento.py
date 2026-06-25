"""
E2E V3-F7 — Compartir un evento por enlace público (unlisted).

Desde la agenda de la banda (admin), el menú "⋯" comparte el evento → pasa a `unlisted`, aparece la
insignia 🔗 y se genera el enlace. La página pública `evento.html` (SIN login) muestra la info no
sensible y nunca el caché/contacto. Cierra el primer efecto-red (D1).
"""

import pytest

pytestmark = pytest.mark.e2e


def _concert(api, bid):
    return api.post(f"/bands/{bid}/events/", json={
        "type": "concert", "title": "Bolo Compartible", "starts_at": "2099-10-10T21:00:00",
        "fee": "750.00", "contact_name": "Promotor Privado", "contact_phone": "600999888",
    }).json()["id"]


def test_compartir_evento_desde_la_agenda_genera_unlisted(page, live_server, api):
    bid = api.post("/bands/", json={"name": "Banda Share"}).json()["id"]
    eid = _concert(api, bid)

    page.goto(live_server + f"/static/band.html?id={bid}", wait_until="networkidle")
    page.click('.bf-tab[data-tab="agenda"]')
    li = page.locator(f'.setlist-song[data-id="{eid}"]')
    li.wait_for(timeout=8000)

    # Abrir el menú "⋯" y compartir.
    li.locator('[data-act="more"]').click()
    li.locator('[data-act="share"]').click()

    # El modal con el enlace aparece (clipboard puede fallar en headless: el modal sale igual).
    page.wait_for_selector(".modal-overlay .share-link", timeout=8000)
    assert "/static/evento.html?id=" in page.inner_text(".modal-overlay .share-link")
    page.click('.modal-overlay [data-act="ok"]')

    # El backend lo marcó unlisted.
    ev = next(e for e in api.get(f"/bands/{bid}/events/").json() if e["id"] == eid)
    assert ev["visibility"] == "unlisted"

    # Tras el re-render, la insignia 🔗 está visible en la fila.
    page.wait_for_selector(f'.setlist-song[data-id="{eid}"] .ev-shared', timeout=8000)


def test_pagina_publica_muestra_info_segura_sin_login(page, live_server, api):
    bid = api.post("/bands/", json={"name": "Banda Pública E2E"}).json()["id"]
    eid = _concert(api, bid)
    api.patch(f"/bands/{bid}/events/{eid}", json={"visibility": "unlisted"})

    page.goto(live_server + f"/static/evento.html?id={eid}", wait_until="networkidle")
    page.wait_for_selector(".pub-title", timeout=8000)

    txt = page.inner_text(".pub-card")
    assert "Bolo Compartible" in txt
    assert "Banda Pública E2E" in txt
    # Nada sensible: ni caché ni contacto.
    assert "750" not in txt and "Promotor Privado" not in txt and "600999888" not in txt
    # El reclamo viral está presente.
    assert "BandFlow" in page.inner_text(".pub-brand")


def test_evento_privado_no_es_accesible_por_la_pagina_publica(page, live_server, api):
    bid = api.post("/bands/", json={"name": "Banda Privada E2E"}).json()["id"]
    eid = _concert(api, bid)   # private por defecto

    page.goto(live_server + f"/static/evento.html?id={eid}", wait_until="networkidle")
    page.wait_for_selector(".pub-title", timeout=8000)
    assert "no disponible" in page.inner_text(".pub-card").lower()
