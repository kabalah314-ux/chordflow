"""
T-V6-61/62 — Avisos in-app (evento nuevo, votación, candidatura, mensaje) y calendario .ics
(suscripción con token y evento suelto). Aislamiento: cada uno ve solo SUS avisos.
"""

import contextlib

import pytest

from src.main import app
from src.services.auth import get_current_user
from src.services.db import SessionLocal
from src.services.models import BandMembership

pytestmark = pytest.mark.unit

MEMBER = "22222222-2222-2222-2222-222222222222"
STRANGER = "99999999-9999-9999-9999-999999999999"


@contextlib.contextmanager
def acting_as(user_id):
    app.dependency_overrides[get_current_user] = lambda: user_id
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def _band(client):
    bid = client.post("/bands/", json={"name": "Banda Avisos"}).json()["id"]
    db = SessionLocal()
    try:
        db.add(BandMembership(band_id=bid, user_id=MEMBER, role="member", status="active"))
        db.commit()
    finally:
        db.close()
    return bid


def test_evento_nuevo_avisa_a_los_demas_y_se_marca_leido(client):
    bid = _band(client)
    client.post(f"/bands/{bid}/events/", json={"type": "rehearsal", "title": "Ensayo Avisado",
                                               "starts_at": "2099-01-01T19:00:00"})
    client.post(f"/bands/{bid}/polls", json={"title": "Votación Avisada",
                                             "options": [{"starts_at": "2099-02-01T19:00:00"}]})
    with acting_as(MEMBER):
        data = client.get("/me/notifications").json()
        titles = [n["title"] for n in data["items"]]
        assert any("Ensayo Avisado" in t for t in titles)
        assert any("Votación Avisada" in t for t in titles)
        assert data["unread"] >= 2
        assert client.post("/me/notifications/read-all").status_code == 204
        assert client.get("/me/notifications").json()["unread"] == 0
    # El creador no se avisa a sí mismo; un ajeno no ve nada
    assert not any("Ensayo Avisado" in n["title"] for n in client.get("/me/notifications").json()["items"])
    with acting_as(STRANGER):
        assert client.get("/me/notifications").json()["items"] == []


def test_calendario_ics_con_token_y_evento_suelto(client):
    bid = _band(client)
    ev = client.post(f"/bands/{bid}/events/", json={
        "type": "concert", "title": "Bolo; con, comas", "starts_at": "2099-03-03T21:30:00",
        "location": "Sala X"}).json()
    r = client.get(f"/bands/{bid}/events/{ev['id']}/ics")
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/calendar")
    assert "DTSTART:20990303T213000" in r.text and "Bolo\; con\\, comas" in r.text
    with acting_as(STRANGER):
        assert client.get(f"/bands/{bid}/events/{ev['id']}/ics").status_code == 404

    with acting_as(MEMBER):
        tok = client.post("/me/calendar-token").json()["token"]
    feed = client.get(f"/public/calendar/{tok}.ics")
    assert feed.status_code == 200 and "BEGIN:VCALENDAR" in feed.text and ev["id"] in feed.text
    with acting_as(MEMBER):
        client.delete("/me/calendar-token")
    assert client.get(f"/public/calendar/{tok}.ics").status_code == 404
