"""
Tests del repertorio de banda (Fase 8, T-058).

Añadir/copiar/listar/quitar canciones de banda, separación con las personales, copia independiente,
acceso del reproductor a miembros, edición por miembro/guest y aislamiento (ajeno→404).
"""

import contextlib

import pytest

from src.main import app
from src.services.auth import get_current_user
from src.services.db import SessionLocal
from src.services.models import BandMembership
from tests.conftest import sample_song_payload

pytestmark = pytest.mark.unit

ADMIN = "00000000-0000-0000-0000-000000000000"  # TEST_USER_ID (creador)
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
    bid = client.post("/bands/", json={"name": "Repertorio Band"}).json()["id"]
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


def test_crear_cancion_de_banda_y_no_aparece_en_personales(client):
    bid = _band(client)
    r = client.post(f"/bands/{bid}/songs/", json=sample_song_payload(title="Tema Banda"))
    assert r.status_code == 201, r.text
    assert r.json()["band_id"] == bid

    # Aparece en el repertorio de la banda
    rep = client.get(f"/bands/{bid}/songs/").json()
    assert any(s["title"] == "Tema Banda" for s in rep)
    # Pero NO en mis canciones personales
    personales = client.get("/songs/").json()
    assert all(s["title"] != "Tema Banda" for s in personales)


def test_copiar_personal_a_banda_es_independiente(client):
    bid = _band(client)
    personal_id = client.post("/songs/", json=sample_song_payload(title="Mi Tema")).json()["id"]

    r = client.post(f"/bands/{bid}/songs/copy", json={"song_id": personal_id})
    assert r.status_code == 201, r.text
    copia = r.json()
    assert copia["band_id"] == bid and copia["id"] != personal_id
    assert copia["title"] == "Mi Tema"
    assert len(copia["sections"]) == 1  # copió la estructura

    # Editar la copia de banda NO toca la personal
    body = sample_song_payload(title="Mi Tema (banda)")
    assert client.put(f"/songs/{copia['id']}", json=body).status_code == 200
    assert client.get(f"/songs/{personal_id}").json()["title"] == "Mi Tema"  # intacta


def test_reproductor_accede_a_cancion_de_banda_segun_pertenencia(client):
    bid = _band(client)
    sid = client.post(f"/bands/{bid}/songs/", json=sample_song_payload(title="X")).json()["id"]

    # Un miembro la abre por la ruta del reproductor
    with acting_as(MEMBER):
        assert client.get(f"/songs/{sid}").status_code == 200
    # Un ajeno NO (404, no se revela)
    with acting_as(STRANGER):
        assert client.get(f"/songs/{sid}").status_code == 404


def test_miembro_edita_repertorio_guest_no(client):
    bid = _band(client)
    sid = client.post(f"/bands/{bid}/songs/", json=sample_song_payload(title="Y")).json()["id"]
    body = sample_song_payload(title="Y editada")
    with acting_as(MEMBER):
        assert client.put(f"/songs/{sid}", json=body).status_code == 200
    with acting_as(GUEST):
        assert client.put(f"/songs/{sid}", json=body).status_code == 403   # guest no edita
        assert client.get(f"/songs/{sid}").status_code == 200              # pero sí lee


def test_quitar_cancion_del_repertorio(client):
    bid = _band(client)
    sid = client.post(f"/bands/{bid}/songs/", json=sample_song_payload(title="Z")).json()["id"]
    assert client.delete(f"/bands/{bid}/songs/{sid}").status_code == 204
    assert all(s["id"] != sid for s in client.get(f"/bands/{bid}/songs/").json())
    assert client.get(f"/songs/{sid}").status_code == 404


def test_aislamiento_repertorio_un_ajeno_no_ve_ni_toca(client):
    bid = _band(client)
    sid = client.post(f"/bands/{bid}/songs/", json=sample_song_payload(title="Secreta")).json()["id"]
    with acting_as(STRANGER):
        assert client.get(f"/bands/{bid}/songs/").status_code == 404
        assert client.post(f"/bands/{bid}/songs/", json=sample_song_payload()).status_code == 404
        assert client.post(f"/bands/{bid}/songs/copy", json={"song_id": sid}).status_code == 404
        assert client.delete(f"/bands/{bid}/songs/{sid}").status_code == 404
