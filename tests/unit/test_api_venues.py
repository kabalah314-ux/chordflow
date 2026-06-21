"""
Tests de salas reutilizables — Venue (Fase 14, T-116).

Crear/editar/borrar (solo admin), listar/ver (miembros), enlazar una sala a un concierto
(`Event.venue_id` + `venue_name` en la agenda), validaciones (solo conciertos, sala de la banda) y
aislamiento por ruta (ajeno→404).
"""

import contextlib

import pytest

from src.main import app
from src.services.auth import get_current_user
from src.services.db import SessionLocal
from src.services.models import BandMembership

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
    bid = client.post("/bands/", json={"name": "Banda Salas"}).json()["id"]
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


def test_admin_crea_sala_miembro_no(client):
    bid = _band(client)
    r = client.post(f"/bands/{bid}/venues/", json={
        "name": "Sala Apolo", "city": "Barcelona", "capacity": 600, "contact": "Técnico Joan"})
    assert r.status_code == 201, r.text
    v = r.json()
    assert v["name"] == "Sala Apolo" and v["capacity"] == 600 and v["band_id"] == bid

    # Un miembro y un guest NO pueden crear (solo admin)
    with acting_as(MEMBER):
        assert client.post(f"/bands/{bid}/venues/", json={"name": "X"}).status_code == 403
    with acting_as(GUEST):
        assert client.post(f"/bands/{bid}/venues/", json={"name": "Y"}).status_code == 403


def test_miembro_lista_y_ve(client):
    bid = _band(client)
    vid = client.post(f"/bands/{bid}/venues/", json={"name": "Razzmatazz"}).json()["id"]
    with acting_as(MEMBER):
        assert any(v["id"] == vid for v in client.get(f"/bands/{bid}/venues/").json())
        assert client.get(f"/bands/{bid}/venues/{vid}").status_code == 200


def test_editar_y_borrar_sala_solo_admin(client):
    bid = _band(client)
    vid = client.post(f"/bands/{bid}/venues/", json={"name": "Sala vieja"}).json()["id"]
    r = client.patch(f"/bands/{bid}/venues/{vid}", json={"name": "Sala nueva", "capacity": 250})
    assert r.status_code == 200 and r.json()["name"] == "Sala nueva" and r.json()["capacity"] == 250
    with acting_as(MEMBER):
        assert client.patch(f"/bands/{bid}/venues/{vid}", json={"name": "Z"}).status_code == 403
        assert client.delete(f"/bands/{bid}/venues/{vid}").status_code == 403
    # Soft delete por el admin → desaparece de la lista
    assert client.delete(f"/bands/{bid}/venues/{vid}").status_code == 204
    assert all(v["id"] != vid for v in client.get(f"/bands/{bid}/venues/").json())


def test_enlazar_sala_a_concierto(client):
    bid = _band(client)
    vid = client.post(f"/bands/{bid}/venues/", json={"name": "Sala Apolo"}).json()["id"]
    # Crear un concierto con la sala → el detalle y la lista traen venue_id + venue_name
    ev = client.post(f"/bands/{bid}/events/",
                     json={"type": "concert", "title": "Bolo", "venue_id": vid}).json()
    assert ev["venue_id"] == vid and ev["venue_name"] == "Sala Apolo"
    summ = client.get(f"/bands/{bid}/events/").json()[0]
    assert summ["venue_name"] == "Sala Apolo"


def test_sala_solo_en_conciertos_y_de_la_banda(client):
    bid = _band(client)
    vid = client.post(f"/bands/{bid}/venues/", json={"name": "Sala"}).json()["id"]
    # En un ensayo no se puede adjuntar sala → 400
    assert client.post(f"/bands/{bid}/events/",
                       json={"type": "rehearsal", "title": "E", "venue_id": vid}).status_code == 400
    # Una sala de OTRA banda → 400
    otra = client.post("/bands/", json={"name": "Otra"}).json()["id"]
    vid2 = client.post(f"/bands/{otra}/venues/", json={"name": "Ajena"}).json()["id"]
    assert client.post(f"/bands/{bid}/events/",
                       json={"type": "concert", "title": "C", "venue_id": vid2}).status_code == 400


def test_aislamiento_un_ajeno_no_ve_ni_toca_las_salas(client):
    bid = _band(client)
    vid = client.post(f"/bands/{bid}/venues/", json={"name": "S"}).json()["id"]
    with acting_as(STRANGER):
        assert client.get(f"/bands/{bid}/venues/").status_code == 404
        assert client.post(f"/bands/{bid}/venues/", json={"name": "Z"}).status_code == 404
        assert client.get(f"/bands/{bid}/venues/{vid}").status_code == 404
        assert client.patch(f"/bands/{bid}/venues/{vid}", json={"name": "Z"}).status_code == 404
        assert client.delete(f"/bands/{bid}/venues/{vid}").status_code == 404
