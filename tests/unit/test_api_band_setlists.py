"""
Tests de setlists de banda (Fase 9, T-061).

Crear/listar/editar/borrar setlists de banda sacados del repertorio; separación con los personales;
solo canciones del repertorio de la banda; reproductor por pertenencia; guest no edita; aislamiento.
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


def _band_with_repertoire(client, n=2):
    bid = client.post("/bands/", json={"name": "Banda SL"}).json()["id"]
    db = SessionLocal()
    try:
        db.add_all([
            BandMembership(band_id=bid, user_id=MEMBER, role="member", status="active"),
            BandMembership(band_id=bid, user_id=GUEST, role="guest", status="active"),
        ])
        db.commit()
    finally:
        db.close()
    song_ids = [client.post(f"/bands/{bid}/songs/", json=sample_song_payload(title=f"BS{i}"))
                .json()["id"] for i in range(n)]
    return bid, song_ids


def test_crear_setlist_de_banda_desde_el_repertorio(client):
    bid, songs = _band_with_repertoire(client)
    r = client.post(f"/bands/{bid}/setlists/", json={"name": "Bolo Banda", "song_ids": songs[::-1]})
    assert r.status_code == 201, r.text
    sl = r.json()
    assert sl["band_id"] == bid
    assert [i["song_id"] for i in sl["items"]] == songs[::-1]  # respeta el orden

    # Aparece en los setlists de banda, NO en los personales
    assert any(s["id"] == sl["id"] for s in client.get(f"/bands/{bid}/setlists/").json())
    assert all(s["id"] != sl["id"] for s in client.get("/setlists/").json())


def test_no_admite_canciones_fuera_del_repertorio(client):
    bid, songs = _band_with_repertoire(client)
    personal = client.post("/songs/", json=sample_song_payload(title="Ajena")).json()["id"]
    sl = client.post(f"/bands/{bid}/setlists/",
                     json={"name": "Mixto", "song_ids": [songs[0], personal]}).json()
    # La canción personal (fuera del repertorio) se filtra
    assert [i["song_id"] for i in sl["items"]] == [songs[0]]


def test_reproductor_accede_al_setlist_de_banda_segun_pertenencia(client):
    bid, songs = _band_with_repertoire(client)
    sid = client.post(f"/bands/{bid}/setlists/", json={"name": "B", "song_ids": songs}).json()["id"]
    with acting_as(MEMBER):
        assert client.get(f"/setlists/{sid}").status_code == 200      # reproductor (ruta común)
    with acting_as(STRANGER):
        assert client.get(f"/setlists/{sid}").status_code == 404


def test_guest_no_edita_pero_ve(client):
    bid, songs = _band_with_repertoire(client)
    sid = client.post(f"/bands/{bid}/setlists/", json={"name": "B", "song_ids": songs}).json()["id"]
    with acting_as(GUEST):
        assert client.get(f"/bands/{bid}/setlists/{sid}").status_code == 200
        assert client.patch(f"/bands/{bid}/setlists/{sid}", json={"name": "X"}).status_code == 403
        assert client.post(f"/bands/{bid}/setlists/", json={"name": "Y"}).status_code == 403


def test_editar_y_borrar_setlist_de_banda(client):
    bid, songs = _band_with_repertoire(client)
    sid = client.post(f"/bands/{bid}/setlists/", json={"name": "B", "song_ids": songs}).json()["id"]
    # Reordenar + renombrar
    r = client.patch(f"/bands/{bid}/setlists/{sid}",
                     json={"name": "Bolo finde", "song_ids": songs[::-1]})
    assert r.status_code == 200
    assert r.json()["name"] == "Bolo finde"
    assert [i["song_id"] for i in r.json()["items"]] == songs[::-1]
    # Borrar (soft delete)
    assert client.delete(f"/bands/{bid}/setlists/{sid}").status_code == 204
    assert all(s["id"] != sid for s in client.get(f"/bands/{bid}/setlists/").json())


def test_aislamiento_un_ajeno_no_ve_ni_toca_setlists_de_banda(client):
    bid, songs = _band_with_repertoire(client)
    sid = client.post(f"/bands/{bid}/setlists/", json={"name": "B", "song_ids": songs}).json()["id"]
    with acting_as(STRANGER):
        assert client.get(f"/bands/{bid}/setlists/").status_code == 404
        assert client.post(f"/bands/{bid}/setlists/", json={"name": "Z"}).status_code == 404
        assert client.get(f"/bands/{bid}/setlists/{sid}").status_code == 404
        assert client.delete(f"/bands/{bid}/setlists/{sid}").status_code == 404
