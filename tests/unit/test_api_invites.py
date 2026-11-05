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


def test_invitacion_por_defecto_caduca_y_tiene_cupo(client):
    """T-V6-08 (S-07): sin parámetros, la invitación caduca a los 7 días y admite 20 usos."""
    bid = _new_band(client)
    inv = client.post(f"/bands/{bid}/invites", json={}).json()
    assert inv["max_uses"] == 20
    assert inv["expires_at"] is not None


def test_admin_revoca_invitacion(client):
    """T-V6-08: una invitación revocada deja de valer y el ajeno no puede revocar."""
    bid = _new_band(client)
    inv = client.post(f"/bands/{bid}/invites", json={}).json()
    with acting_as(STRANGER):
        assert client.delete(f"/bands/{bid}/invites/{inv['id']}").status_code == 404
    assert client.delete(f"/bands/{bid}/invites/{inv['id']}").status_code == 204
    prev = client.get(f"/invites/{inv['code']}").json()
    assert prev["valid"] is False and prev["reason"] == "revocada"
    with acting_as(JOINER):
        assert client.post(f"/invites/{inv['code']}/accept").status_code == 400
    assert client.delete(f"/bands/{bid}/invites/no-existe").status_code == 404


def test_invitacion_es_un_escaparate_sin_datos_privados(client):
    """T-V6-80: la previsualización muestra miembros, canciones y el próximo evento PÚBLICO (nunca
    uno privado), sin caché ni contactos."""
    bid = _new_band(client)
    client.post(f"/bands/{bid}/songs/", json={"title": "Tema 1"})
    priv = client.post(f"/bands/{bid}/events/", json={
        "type": "concert", "title": "Bolo privado", "starts_at": "2099-01-01T21:00:00",
        "fee": "999.00", "contact_phone": "600000000"}).json()
    pub = client.post(f"/bands/{bid}/events/", json={
        "type": "concert", "title": "Bolo abierto", "starts_at": "2099-02-01T21:00:00"}).json()
    client.patch(f"/bands/{bid}/events/{pub['id']}", json={"visibility": "public"})
    code = client.post(f"/bands/{bid}/invites", json={"role_to_grant": "member"}).json()["code"]
    with acting_as(STRANGER):
        prev = client.get(f"/invites/{code}").json()
    assert prev["member_count"] == 1 and prev["song_count"] == 1
    assert prev["next_public_event"]["title"] == "Bolo abierto"
    body = str(prev)
    assert priv["id"] not in body and "999" not in body and "600000000" not in body
