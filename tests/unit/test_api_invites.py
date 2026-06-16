"""
Tests de invitaciones por código (Fase 7, T-053).

Generar (admin), previsualizar, aceptar (entra como member/guest), caducada/agotada, ya-miembro,
y aislamiento (solo admin genera). El que acepta es un usuario distinto (override de auth).
"""

import contextlib
from datetime import timedelta

import pytest

from src.main import app
from src.services.auth import get_current_user
from src.services.db import SessionLocal
from src.services.models import BandInvite, _utcnow

pytestmark = pytest.mark.unit

JOINER = "44444444-4444-4444-4444-444444444444"
OTHER = "55555555-5555-5555-5555-555555555555"
STRANGER = "99999999-9999-9999-9999-999999999999"


@contextlib.contextmanager
def acting_as(user_id):
    app.dependency_overrides[get_current_user] = lambda: user_id
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def _new_band(client):
    return client.post("/bands/", json={"name": "Los Tres"}).json()["id"]


def test_generar_y_aceptar_invitacion(client):
    bid = _new_band(client)
    inv = client.post(f"/bands/{bid}/invites", json={"role_to_grant": "member"})
    assert inv.status_code == 201, inv.text
    code = inv.json()["code"]
    assert code and inv.json()["used_count"] == 0

    # Previsualizar (sin login de banda) muestra nombre y validez
    prev = client.get(f"/invites/{code}").json()
    assert prev["band_name"] == "Los Tres" and prev["valid"] is True
    assert prev["role_to_grant"] == "member"

    # Otro usuario acepta → entra como member
    with acting_as(JOINER):
        r = client.post(f"/invites/{code}/accept")
        assert r.status_code == 201, r.text
        assert r.json()["role"] == "member" and r.json()["status"] == "active"
        # y ya puede ver la banda
        assert client.get(f"/bands/{bid}").status_code == 200

    # El uso quedó consumido
    assert client.get(f"/invites/{code}").json()  # sigue accesible
    assert client.get(f"/bands/{bid}/invites").json()[0]["used_count"] == 1


def test_aceptar_dos_veces_da_409(client):
    bid = _new_band(client)
    code = client.post(f"/bands/{bid}/invites", json={}).json()["code"]
    with acting_as(JOINER):
        assert client.post(f"/invites/{code}/accept").status_code == 201
        assert client.post(f"/invites/{code}/accept").status_code == 409  # ya es miembro


def test_invitacion_caducada(client):
    bid = _new_band(client)
    code = client.post(f"/bands/{bid}/invites", json={}).json()["code"]
    # Forzar caducidad en el pasado
    db = SessionLocal()
    try:
        inv = db.query(BandInvite).filter(BandInvite.code == code).first()
        inv.expires_at = _utcnow().replace(tzinfo=None) - timedelta(hours=1)
        db.commit()
    finally:
        db.close()
    assert client.get(f"/invites/{code}").json()["valid"] is False
    with acting_as(JOINER):
        assert client.post(f"/invites/{code}/accept").status_code == 400


def test_invitacion_agotada_por_max_uses(client):
    bid = _new_band(client)
    code = client.post(f"/bands/{bid}/invites", json={"max_uses": 1}).json()["code"]
    with acting_as(JOINER):
        assert client.post(f"/invites/{code}/accept").status_code == 201  # 1er uso (agota)
    with acting_as(OTHER):
        assert client.post(f"/invites/{code}/accept").status_code == 400  # agotada


def test_solo_admin_genera_invitaciones(client):
    bid = _new_band(client)
    with acting_as(STRANGER):  # ajeno → 404 (ni siquiera ve la banda)
        assert client.post(f"/bands/{bid}/invites", json={}).status_code == 404


def test_codigo_inexistente_da_404(client):
    assert client.get("/invites/no-existe").status_code == 404
    with acting_as(JOINER):
        assert client.post("/invites/no-existe/accept").status_code == 404
