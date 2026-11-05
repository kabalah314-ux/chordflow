"""T-V6-65 / T-V6-42e — exportar mis datos, salir de una banda (traspaso de admin) y borrar cuenta."""

import contextlib

import pytest

from src.main import app
from src.services.auth import get_current_user
from src.services.db import SessionLocal
from src.services.models import BandMembership

pytestmark = pytest.mark.unit

ME = "00000000-0000-0000-0000-000000000000"
OTRO = "22222222-2222-2222-2222-222222222222"
NUEVO = "88888888-8888-8888-8888-888888888888"


@contextlib.contextmanager
def acting_as(user_id):
    app.dependency_overrides[get_current_user] = lambda: user_id
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def _band_with(client, *extra):
    bid = client.post("/bands/", json={"name": "Banda Cuenta"}).json()["id"]
    db = SessionLocal()
    try:
        for uid in extra:
            db.add(BandMembership(band_id=bid, user_id=uid, role="member", status="active"))
        db.commit()
    finally:
        db.close()
    return bid


def test_exportar_mis_datos(client):
    with acting_as(NUEVO):
        client.post("/songs/", json={"title": "Mía para exportar", "sections": []})
        data = client.get("/me/export").json()
    assert any(s["title"] == "Mía para exportar" for s in data["songs"])
    assert "exported_at" in data


def test_salir_de_la_banda_exige_traspasar_el_admin(client):
    bid = _band_with(client, OTRO)
    assert client.post(f"/bands/{bid}/leave", json={}).status_code == 400
    assert client.post(f"/bands/{bid}/leave", json={"transfer_to": OTRO}).status_code == 200
    assert client.get(f"/bands/{bid}").status_code == 404   # ya no soy miembro
    with acting_as(OTRO):
        me = next(m for m in client.get(f"/bands/{bid}/members").json() if m["is_me"])
        assert me["role"] == "admin"
        # Un miembro normal sale sin más
    bid2 = _band_with(client, OTRO)
    with acting_as(OTRO):
        assert client.post(f"/bands/{bid2}/leave", json={}).status_code == 200


def test_borrar_cuenta(client):
    with acting_as(NUEVO):
        bid = client.post("/bands/", json={"name": "Banda de Nuevo"}).json()["id"]
        client.post("/songs/", json={"title": "Se borra", "sections": []})
        assert client.post("/me/delete-account", json={"confirm": "no"}).status_code == 400
        assert client.post("/me/delete-account", json={"confirm": "BORRAR"}).status_code == 200
        assert client.get("/songs/").json() == []
        assert client.get("/bands/").json() == []
        assert client.get(f"/bands/{bid}").status_code == 404
