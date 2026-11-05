"""
E2E V6-F9 — Funciones de banda en el espacio de banda: pizarra (Resumen), semáforo de preparación
(Repertorio), votación de fechas (Agenda + página pública votar.html) y hoja del bolo (bolo.html).
"""

import pytest

pytestmark = pytest.mark.e2e


def test_pizarra_en_resumen(page, live_server, api):
    bid = api.post("/bands/", json={"name": "Banda Pizarra E2E"}).json()["id"]
    page.goto(live_server + f"/static/band.html?id={bid}", wait_until="networkidle")
    page.wait_for_selector("#bt-board #bt-note-input", timeout=8000)
    page.fill("#bt-note-input", "Comprar cuerdas del 10")
    page.click("#bt-note-add button[type=submit]")
    page.wait_for_selector("#bt-board .bt-note:has-text('Comprar cuerdas del 10')", timeout=8000)
    # Marcar como hecha → desaparece de la lista de pendientes
    page.click("#bt-board .bt-note [data-act='done']")
    page.wait_for_selector("#bt-board .bt-note", state="detached", timeout=8000)


def test_semaforo_en_repertorio(page, live_server, api):
    bid = api.post("/bands/", json={"name": "Banda Semáforo E2E"}).json()["id"]
    sid = api.post(f"/bands/{bid}/songs/", json={"title": "Tema Semáforo"}).json()["id"]
    page.goto(live_server + f"/static/band.html?id={bid}", wait_until="networkidle")
    page.click('.bf-tab[data-tab="repertorio"]')
    btn = f'#b-repertoire li[data-id="{sid}"] .bt-status'
    page.wait_for_selector(btn, timeout=8000)
    assert page.get_attribute(btn, "data-status") == "pending"
    page.click(btn)
    page.wait_for_function(
        f"document.querySelector('{btn}').dataset.status === 'improving'", timeout=8000)
    page.wait_for_timeout(300)
    board = api.get(f"/bands/{bid}/song-status").json()
    assert board["mine"][0]["status"] == "improving"
    assert page.locator("#bt-rep-progress .bt-progress").count() == 1


def test_votacion_publica_sin_cuenta(page, live_server, api):
    bid = api.post("/bands/", json={"name": "Banda Votación E2E"}).json()["id"]
    poll = api.post(f"/bands/{bid}/polls", json={
        "title": "Ensayo votado E2E",
        "options": [{"starts_at": "2099-03-03T19:00:00"}, {"starts_at": "2099-03-05T19:00:00"}],
    }).json()

    # En la Agenda aparece el bloque de votaciones con la de la banda
    page.goto(live_server + f"/static/band.html?id={bid}", wait_until="networkidle")
    page.click('.bf-tab[data-tab="agenda"]')
    page.wait_for_selector("#bt-polls .bt-poll:has-text('Ensayo votado E2E')", timeout=8000)

    # Página pública: elegir nombre y votar
    page.goto(live_server + f"/static/votar.html?t={poll['token']}", wait_until="networkidle")
    page.wait_for_selector("#vt-who", timeout=8000)
    me = poll["members"][0]["user_id"]
    page.select_option("#vt-who", me)
    first = f'.vt-opt[data-opt="{poll["options"][0]["id"]}"]'
    page.click(first + ' [data-vote="yes"]')
    page.wait_for_selector(first + ' [data-vote="yes"].bf-btn--primary', timeout=8000)
    assert "Sí 1" in page.inner_text(first)


def test_hoja_del_bolo_publica(page, live_server, api):
    bid = api.post("/bands/", json={"name": "Banda Hoja E2E"}).json()["id"]
    eid = api.post(f"/bands/{bid}/events/", json={
        "type": "concert", "title": "Bolo Hoja E2E", "starts_at": "2099-08-08T22:00:00",
        "soundcheck_at": "2099-08-08T19:30:00", "backline_notes": "Batería de la sala",
        "fee": "300.00"}).json()["id"]
    api.post(f"/bands/{bid}/events/{eid}/checklist", json={"text": "Llevar DI"})

    # Desde la agenda se abre el diálogo de la hoja
    page.goto(live_server + f"/static/band.html?id={bid}", wait_until="networkidle")
    page.click('.bf-tab[data-tab="agenda"]')
    page.click(f'#b-agenda li[data-id="{eid}"] [data-act="sheet"]')
    page.wait_for_selector(".bf-dialog #bt-s-items .bt-note:has-text('Llevar DI')", timeout=8000)
    page.keyboard.press("Escape")
    page.wait_for_selector(".bf-dialog", state="detached", timeout=4000)

    tok = api.post(f"/bands/{bid}/events/{eid}/sheet-token").json()["token"]
    page.goto(live_server + f"/static/bolo.html?t={tok}", wait_until="networkidle")
    page.wait_for_selector(".pub-title", timeout=8000)
    txt = page.inner_text("#pub-card")
    assert "Bolo Hoja E2E" in txt and "Batería de la sala" in txt and "Llevar DI" in txt
    assert "300" not in txt


def test_gastos_fijos_y_modo_ensayo(page, live_server, api):
    bid = api.post("/bands/", json={"name": "Banda Fijos E2E"}).json()["id"]
    me = next(m for m in api.get(f"/bands/{bid}/members").json() if m["is_me"])["user_id"]
    api.post(f"/bands/{bid}/recurring", json={"description": "Local E2E", "amount": "90.00",
                                              "paid_by": me, "day_of_month": 1})
    sid = api.post(f"/bands/{bid}/songs/", json={"title": "Tema Ensayo E2E"}).json()["id"]
    api.put(f"/bands/{bid}/songs/{sid}/status", json={"status": "improving"})

    page.goto(live_server + f"/static/band.html?id={bid}", wait_until="networkidle")
    # Modo ensayo desde el Resumen: la canción "mejorando" sale sugerida
    page.click("#bt-start-reh")
    page.wait_for_selector(".bf-dialog .bt-reh-item:has-text('Tema Ensayo E2E')", timeout=8000)
    page.click(".bf-dialog .bt-reh-item [data-act='toggle']")
    page.wait_for_timeout(1300)
    page.fill("#bt-reh-notes", "Cerrar el final")
    page.click('.bf-dialog [data-bfd-act="1"]')
    page.wait_for_selector(".bf-dialog", state="detached", timeout=8000)
    page.wait_for_timeout(500)
    msgs = api.get(f"/bands/{bid}/messages/").json()
    assert any("Resumen del ensayo" in m["body"] for m in msgs)

    # Gastos fijos en Finanzas: "Registrar" crea el movimiento
    page.click('.bf-tab[data-tab="finanzas"]')
    page.wait_for_selector("#bt-recurring [data-act='log']", timeout=8000)
    page.click("#bt-recurring [data-act='log']")
    page.wait_for_selector("#bt-recurring [data-act='log']", state="detached", timeout=8000)
    assert len(api.get(f"/bands/{bid}/transactions").json()) == 1

    # Material de una canción desde el Repertorio (añadir un enlace)
    page.click('.bf-tab[data-tab="repertorio"]')
    page.click(f'#b-repertoire li[data-id="{sid}"] [data-act="att"]')
    page.wait_for_selector(".bf-dialog #bt-att-url", timeout=8000)
    page.fill("#bt-att-url", "https://example.com/partitura.pdf")
    page.fill("#bt-att-title", "Partitura E2E")
    page.click("#bt-att-link")
    page.wait_for_selector(".bf-dialog .bt-att:has-text('Partitura E2E')", timeout=8000)
