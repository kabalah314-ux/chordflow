"""
Tests de la agenda — eventos + asistencia (Fase 10).

Crear (solo admin), listar/ver (miembros), asistencia voy/no voy, concierto con setlist (solo
conciertos, de la banda), editar/borrar (admin) y aislamiento (ajeno→404).
"""

import contextlib

import pytest

from src.main import app
from src.services.auth import get_current_user
from src.services.db import SessionLocal
from src.services.models import BandMembership
from tests.conftest import sample_song_payload

pytestmark = pytest.mark.unit

ADMIN = "00000000-0000-0000-0000-000000000000"
MEMBER = "22222222-2222-2222-2222-222222222222"
GUEST = "33333333-3333-3333-3333-333333333333"
STRANGER = "99999999-9999-9999-9999-999999999999"


@contextlib.contextmanager
def acting_as(user_id):
    app.dependency_overrides[get_current_user] = lambda: user_id
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def _band(client):
    bid = client.post("/bands/", json={"name": "Banda Agenda"}).json()["id"]
    db = SessionLocal()
    try:
        db.add_all([
            BandMembership(band_id=bid, user_id=MEMBER, role="member", status="active"),
            BandMembership(band_id=bid, user_id=GUEST, role="guest", status="active"),
        ])
        db.commit()
    finally:
        db.close()
    return bid


def test_admin_crea_evento_miembro_no(client):
    bid = _band(client)
    r = client.post(f"/bands/{bid}/events/",
                    json={"type": "rehearsal", "title": "Ensayo jueves",
                          "starts_at": "2026-07-02T20:00:00"})
    assert r.status_code == 201, r.text
    assert r.json()["type"] == "rehearsal" and r.json()["status"] == "confirmed"

    # Un miembro NO puede crear (solo admin)
    with acting_as(MEMBER):
        assert client.post(f"/bands/{bid}/events/",
                           json={"type": "other", "title": "X"}).status_code == 403


def test_listar_y_marcar_asistencia(client):
    bid = _band(client)
    eid = client.post(f"/bands/{bid}/events/",
                      json={"type": "rehearsal", "title": "Ensayo"}).json()["id"]

    # Un miembro lista (200) y marca "voy"
    with acting_as(MEMBER):
        lst = client.get(f"/bands/{bid}/events/").json()
        assert len(lst) == 1 and lst[0]["my_status"] is None
        r = client.put(f"/bands/{bid}/events/{eid}/attendance", json={"status": "yes"})
        assert r.status_code == 200 and r.json()["my_status"] == "yes"
        # Cambiar de idea
        r = client.put(f"/bands/{bid}/events/{eid}/attendance", json={"status": "maybe"})
        assert r.json()["my_status"] == "maybe"

    # El detalle (para un admin) muestra la asistencia del miembro
    att = client.get(f"/bands/{bid}/events/{eid}").json()["attendance"]
    assert any(a["user_id"] == MEMBER and a["status"] == "maybe" for a in att)

    # La LISTA también surte la asistencia de todos (para mostrar confirmados en la agenda, #4),
    # no solo el detalle.
    lst_att = client.get(f"/bands/{bid}/events/").json()[0]["attendance"]
    assert any(a["user_id"] == MEMBER and a["status"] == "maybe" for a in lst_att)


def test_guest_puede_marcar_asistencia(client):
    bid = _band(client)
    eid = client.post(f"/bands/{bid}/events/", json={"type": "concert", "title": "Bolo"}).json()["id"]
    with acting_as(GUEST):
        assert client.put(f"/bands/{bid}/events/{eid}/attendance",
                          json={"status": "yes"}).status_code == 200


def test_setlist_solo_en_conciertos_y_de_la_banda(client):
    bid = _band(client)
    # setlist de la banda (necesita una canción del repertorio)
    sid_song = client.post(f"/bands/{bid}/songs/", json=sample_song_payload()).json()["id"]
    setlist_id = client.post(f"/bands/{bid}/setlists/",
                             json={"name": "SL", "song_ids": [sid_song]}).json()["id"]

    # Concierto con setlist → OK
    r = client.post(f"/bands/{bid}/events/",
                    json={"type": "concert", "title": "Concierto", "setlist_id": setlist_id})
    assert r.status_code == 201 and r.json()["setlist_id"] == setlist_id

    # Setlist en un ensayo → 400
    assert client.post(f"/bands/{bid}/events/",
                       json={"type": "rehearsal", "title": "E", "setlist_id": setlist_id}
                       ).status_code == 400

    # Setlist de OTRA banda → 400
    otra = client.post("/bands/", json={"name": "Otra"}).json()["id"]
    s2_song = client.post(f"/bands/{otra}/songs/", json=sample_song_payload()).json()["id"]
    s2 = client.post(f"/bands/{otra}/setlists/", json={"name": "S2", "song_ids": [s2_song]}).json()["id"]
    assert client.post(f"/bands/{bid}/events/",
                       json={"type": "concert", "title": "C", "setlist_id": s2}).status_code == 400


def test_editar_y_borrar_evento_solo_admin(client):
    bid = _band(client)
    eid = client.post(f"/bands/{bid}/events/", json={"type": "rehearsal", "title": "E"}).json()["id"]

    r = client.patch(f"/bands/{bid}/events/{eid}", json={"title": "Ensayo movido", "status": "cancelled"})
    assert r.status_code == 200 and r.json()["title"] == "Ensayo movido" and r.json()["status"] == "cancelled"

    with acting_as(MEMBER):  # miembro no edita ni borra
        assert client.patch(f"/bands/{bid}/events/{eid}", json={"title": "X"}).status_code == 403
        assert client.delete(f"/bands/{bid}/events/{eid}").status_code == 403

    assert client.delete(f"/bands/{bid}/events/{eid}").status_code == 204
    assert all(e["id"] != eid for e in client.get(f"/bands/{bid}/events/").json())


def test_aislamiento_un_ajeno_no_ve_ni_toca_la_agenda(client):
    bid = _band(client)
    eid = client.post(f"/bands/{bid}/events/", json={"type": "rehearsal", "title": "E"}).json()["id"]
    with acting_as(STRANGER):
        assert client.get(f"/bands/{bid}/events/").status_code == 404
        assert client.post(f"/bands/{bid}/events/", json={"type": "other", "title": "X"}).status_code == 404
        assert client.get(f"/bands/{bid}/events/{eid}").status_code == 404
        assert client.put(f"/bands/{bid}/events/{eid}/attendance", json={"status": "yes"}).status_code == 404
        assert client.delete(f"/bands/{bid}/events/{eid}").status_code == 404
