"""
Tests de gestión de membresía de banda (Fase 7, T-052).

Listar miembros (con nombre real), cambiar rol, baja blanda + reactivar, salvaguarda de "nunca sin
admin" y aislamiento (ajeno→404). El admin es el usuario de prueba (creador); el 2º miembro se
siembra directo en BD (el alta por invitación llega en T-053).
"""

import contextlib

import pytest

from src.main import app
from src.services.auth import get_current_user
from src.services.db import SessionLocal
from src.services.models import BandMembership, MusicianProfile

pytestmark = pytest.mark.unit

ADMIN = "00000000-0000-0000-0000-000000000000"  # = TEST_USER_ID (creador)
MEMBER = "22222222-2222-2222-2222-222222222222"
STRANGER = "99999999-9999-9999-9999-999999999999"


@contextlib.contextmanager
def acting_as(user_id):
    app.dependency_overrides[get_current_user] = lambda: user_id
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def _band_with_member(client):
    """Crea una banda (TEST_USER = admin) y siembra un 2º miembro con perfil."""
    bid = client.post("/bands/", json={"name": "Los Tres"}).json()["id"]
    db = SessionLocal()
    try:
        db.add(MusicianProfile(id=MEMBER, display_name="Ana Bajo"))
        db.add(BandMembership(band_id=bid, user_id=MEMBER, role="member", status="active"))
        db.commit()
    finally:
        db.close()
    return bid


def test_listar_miembros_muestra_nombre_real(client):
    bid = _band_with_member(client)
    members = client.get(f"/bands/{bid}/members").json()
    assert len(members) == 2
    ana = next(m for m in members if m["user_id"] == MEMBER)
    assert ana["display_name"] == "Ana Bajo"  # no un UUID
    assert ana["role"] == "member"


def test_cambiar_rol_de_miembro(client):
    bid = _band_with_member(client)
    r = client.patch(f"/bands/{bid}/members/{MEMBER}", json={"role": "admin"})
    assert r.status_code == 200
    assert r.json()["role"] == "admin"


def test_baja_blanda_corta_acceso_pero_conserva_historico(client):
    bid = _band_with_member(client)
    # Baja del miembro
    r = client.delete(f"/bands/{bid}/members/{MEMBER}")
    assert r.status_code == 200
    assert r.json()["status"] == "left"
    assert r.json()["left_at"] is not None

    # Sigue en el histórico (lista de miembros)
    assert any(m["user_id"] == MEMBER for m in client.get(f"/bands/{bid}/members").json())

    # Pero pierde el acceso: como ese miembro, la banda ya no es accesible
    with acting_as(MEMBER):
        assert client.get(f"/bands/{bid}").status_code == 404

    # Reactivar → recupera acceso
    assert client.post(f"/bands/{bid}/members/{MEMBER}/reactivate").status_code == 200
    with acting_as(MEMBER):
        assert client.get(f"/bands/{bid}").status_code == 200


def test_no_se_puede_dejar_la_banda_sin_admin(client):
    bid = _band_with_member(client)  # ADMIN es el único admin
    # Degradar al único admin → 400
    assert client.patch(f"/bands/{bid}/members/{ADMIN}", json={"role": "member"}).status_code == 400
    # Dar de baja al único admin → 400
    assert client.delete(f"/bands/{bid}/members/{ADMIN}").status_code == 400


def test_aislamiento_un_ajeno_no_gestiona_miembros(client):
    bid = _band_with_member(client)
    with acting_as(STRANGER):
        assert client.get(f"/bands/{bid}/members").status_code == 404
        assert client.patch(f"/bands/{bid}/members/{MEMBER}", json={"role": "admin"}).status_code == 404
        assert client.delete(f"/bands/{bid}/members/{MEMBER}").status_code == 404


def test_un_miembro_normal_no_puede_cambiar_roles(client):
    bid = _band_with_member(client)
    with acting_as(MEMBER):  # es miembro activo, pero no admin
        assert client.patch(f"/bands/{bid}/members/{ADMIN}", json={"role": "member"}).status_code == 403
