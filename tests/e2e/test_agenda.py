"""
E2E de la Agenda agregada (`agenda.html`, Fase 13, T-078).

Lista los eventos de TODAS mis bandas (próximos + pasados) con etiqueta de banda y filtro.
"""

import pytest

pytestmark = pytest.mark.e2e


def test_agenda_agrega_proximos_y_pasados_con_filtro(page, live_server, api):
    b1 = api.post("/bands/", json={"name": "Banda Agenda A"}).json()["id"]
    b2 = api.post("/bands/", json={"name": "Banda Agenda B"}).json()["id"]
    api.post(f"/bands/{b1}/events/",
             json={"type": "concert", "title": "Bolo Futuro A", "starts_at": "2099-01-01T21:00:00"})
    api.post(f"/bands/{b1}/events/",
             json={"type": "rehearsal", "title": "Ensayo Pasado A", "starts_at": "2000-01-01T19:00:00"})
    api.post(f"/bands/{b2}/events/",
             json={"type": "concert", "title": "Bolo Futuro B", "starts_at": "2099-02-02T21:00:00"})

    page.goto(live_server + "/static/agenda.html", wait_until="networkidle")
    page.wait_for_selector("#agenda-upcoming", timeout=8000)

    # Próximos de AMBAS bandas, con etiqueta; el pasado aparece en su sección
    upcoming = page.inner_text("#agenda-upcoming")
    assert "Bolo Futuro A" in upcoming and "Bolo Futuro B" in upcoming
    assert "Banda Agenda A" in upcoming and "Banda Agenda B" in upcoming
    page.wait_for_selector("#agenda-past", timeout=8000)
    assert "Ensayo Pasado A" in page.inner_text("#agenda-past")

    # Filtro por banda B: solo sus eventos
    page.click(f'#agenda-filters [data-band="{b2}"]')
    page.wait_for_function(
        "!document.querySelector('#agenda-upcoming').innerText.includes('Bolo Futuro A')", timeout=8000)
    assert "Bolo Futuro B" in page.inner_text("#agenda-upcoming")


def test_agenda_agregada_muestra_confirmados(page, live_server, api):
    """La agenda agregada muestra los confirmados de cada evento (✅ nombre), como la de banda."""
    api.put("/profile/me", json={"display_name": "Ana E2E"})
    bid = api.post("/bands/", json={"name": "Banda Conf Agg"}).json()["id"]
    eid = api.post(f"/bands/{bid}/events/",
                   json={"type": "concert", "title": "Bolo Confirmado Agg",
                         "starts_at": "2099-06-06T21:00:00"}).json()["id"]
    api.put(f"/bands/{bid}/events/{eid}/attendance", json={"status": "yes"})

    page.goto(live_server + "/static/agenda.html", wait_until="networkidle")
    fila = '#agenda-upcoming a:has-text("Bolo Confirmado Agg")'
    page.wait_for_selector(fila + " .ev-attendees", timeout=8000)
    linea = page.inner_text(fila + " .ev-attendees")
    assert "✅" in linea and "Ana E2E" in linea
