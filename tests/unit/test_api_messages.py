"""
Tests del chat de banda (Fase 12): publicar, editar el propio, borrar (autor/admin), fijar notas
(admin), hilo de evento vs chat general, y aislamiento.
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
    bid = client.post("/bands/", json={"name": "Banda Chat"}).json()["id"]
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


def test_publicar_y_listar_chat_general(client):
    bid = _band(client)
    r = client.post(f"/bands/{bid}/messages/", json={"body": "¡Hola banda!"})
    assert r.status_code == 201 and r.json()["is_mine"] is True
    with acting_as(MEMBER):
        msgs = client.get(f"/bands/{bid}/messages/").json()
        assert len(msgs) == 1 and msgs[0]["body"] == "¡Hola banda!"
        assert msgs[0]["is_mine"] is False  # es del admin


def test_guest_puede_escribir(client):
    bid = _band(client)
    with acting_as(GUEST):
        assert client.post(f"/bands/{bid}/messages/", json={"body": "soy el dep"}).status_code == 201


def test_editar_y_borrar_el_propio(client):
    bid = _band(client)
    with acting_as(MEMBER):
        mid = client.post(f"/bands/{bid}/messages/", json={"body": "v1"}).json()["id"]
        r = client.patch(f"/bands/{bid}/messages/{mid}", json={"body": "v2"})
        assert r.status_code == 200 and r.json()["body"] == "v2" and r.json()["edited_at"]
        assert client.delete(f"/bands/{bid}/messages/{mid}").status_code == 204
    assert client.get(f"/bands/{bid}/messages/").json() == []


def test_no_editar_ni_borrar_ajeno_salvo_admin(client):
    bid = _band(client)
    with acting_as(MEMBER):
        mid = client.post(f"/bands/{bid}/messages/", json={"body": "del miembro"}).json()["id"]
    with acting_as(GUEST):
        assert client.patch(f"/bands/{bid}/messages/{mid}", json={"body": "hack"}).status_code == 403
        assert client.delete(f"/bands/{bid}/messages/{mid}").status_code == 403
    # El admin sí puede borrar cualquiera
    assert client.delete(f"/bands/{bid}/messages/{mid}").status_code == 204


def test_fijar_nota_solo_admin(client):
    bid = _band(client)
    with acting_as(MEMBER):
        mid = client.post(f"/bands/{bid}/messages/", json={"body": "aviso"}).json()["id"]
        assert client.patch(f"/bands/{bid}/messages/{mid}/pin", json={"is_pinned": True}).status_code == 403
    # Admin fija → aparece arriba
    assert client.patch(f"/bands/{bid}/messages/{mid}/pin", json={"is_pinned": True}).json()["is_pinned"] is True
    client.post(f"/bands/{bid}/messages/", json={"body": "otro mensaje"})
    msgs = client.get(f"/bands/{bid}/messages/").json()
    assert msgs[0]["id"] == mid and msgs[0]["is_pinned"] is True  # fijado primero


def test_hilo_de_evento_separado_del_chat_general(client):
    bid = _band(client)
    eid = client.post(f"/bands/{bid}/events/", json={"type": "concert", "title": "Bolo"}).json()["id"]
    client.post(f"/bands/{bid}/messages/", json={"body": "general"})
    client.post(f"/bands/{bid}/messages/", json={"body": "del evento", "event_id": eid})

    general = client.get(f"/bands/{bid}/messages/").json()
    assert [m["body"] for m in general] == ["general"]
    hilo = client.get(f"/bands/{bid}/messages/?event_id={eid}").json()
    assert [m["body"] for m in hilo] == ["del evento"]

    # Mensaje a un evento de otra banda → 400
    otra = client.post("/bands/", json={"name": "Otra"}).json()["id"]
    e2 = client.post(f"/bands/{otra}/events/", json={"type": "other", "title": "X"}).json()["id"]
    assert client.post(f"/bands/{bid}/messages/", json={"body": "no", "event_id": e2}).status_code == 400


def test_aislamiento_chat(client):
    bid = _band(client)
    mid = client.post(f"/bands/{bid}/messages/", json={"body": "privado"}).json()["id"]
    with acting_as(STRANGER):
        assert client.get(f"/bands/{bid}/messages/").status_code == 404
        assert client.post(f"/bands/{bid}/messages/", json={"body": "x"}).status_code == 404
        assert client.delete(f"/bands/{bid}/messages/{mid}").status_code == 404
