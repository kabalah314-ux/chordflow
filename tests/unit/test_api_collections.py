"""
Tests de repertorios de banda — colecciones temáticas (T-114).

Crear/listar/editar/borrar colecciones de canciones del repertorio; solo canciones del repertorio de
la banda; guest no edita pero ve; soft delete; aislamiento por ruta; diferenciación de los setlists.
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


def _band_with_repertoire(client, n=3):
    bid = client.post("/bands/", json={"name": "Banda Col"}).json()["id"]
    db = SessionLocal()
    try:
        db.add_all([
            BandMembership(band_id=bid, user_id=MEMBER, role="member", status="active"),
            BandMembership(band_id=bid, user_id=GUEST, role="guest", status="active"),
        ])
        db.commit()
    finally:
        db.close()
    song_ids = [client.post(f"/bands/{bid}/songs/", json=sample_song_payload(title=f"BC{i}"))
                .json()["id"] for i in range(n)]
    return bid, song_ids


def test_crear_coleccion_desde_el_repertorio(client):
    bid, songs = _band_with_repertoire(client)
    r = client.post(f"/bands/{bid}/collections/",
                    json={"name": "Acústico", "song_ids": songs[:2]})
    assert r.status_code == 201, r.text
    col = r.json()
    assert col["band_id"] == bid and col["name"] == "Acústico"
    assert [i["song_id"] for i in col["items"]] == songs[:2]
    # Aparece en la lista con el recuento de canciones
    lst = client.get(f"/bands/{bid}/collections/").json()
    assert any(c["id"] == col["id"] and c["song_count"] == 2 for c in lst)


def test_una_cancion_puede_estar_en_varias_colecciones_sin_duplicar(client):
    bid, songs = _band_with_repertoire(client)
    c1 = client.post(f"/bands/{bid}/collections/",
                     json={"name": "Bodas", "song_ids": [songs[0], songs[1]]}).json()
    c2 = client.post(f"/bands/{bid}/collections/",
                     json={"name": "Cañero", "song_ids": [songs[0], songs[2]]}).json()
    # La misma canción (songs[0]) está en ambas colecciones
    assert songs[0] in [i["song_id"] for i in c1["items"]]
    assert songs[0] in [i["song_id"] for i in c2["items"]]
    # Pero NO se duplica dentro de la misma colección (uq_collection_song)
    dup = client.post(f"/bands/{bid}/collections/",
                      json={"name": "Dup", "song_ids": [songs[0], songs[0], songs[1]]}).json()
    assert [i["song_id"] for i in dup["items"]] == [songs[0], songs[1]]


def test_no_admite_canciones_fuera_del_repertorio(client):
    bid, songs = _band_with_repertoire(client)
    personal = client.post("/songs/", json=sample_song_payload(title="Ajena")).json()["id"]
    col = client.post(f"/bands/{bid}/collections/",
                      json={"name": "Mixto", "song_ids": [songs[0], personal]}).json()
    assert [i["song_id"] for i in col["items"]] == [songs[0]]  # la personal se filtra


def test_editar_renombrar_y_cambiar_canciones(client):
    bid, songs = _band_with_repertoire(client)
    cid = client.post(f"/bands/{bid}/collections/",
                      json={"name": "X", "song_ids": [songs[0]]}).json()["id"]
    r = client.patch(f"/bands/{bid}/collections/{cid}",
                     json={"name": "Acústico finde", "song_ids": [songs[2], songs[1]]})
    assert r.status_code == 200
    assert r.json()["name"] == "Acústico finde"
    assert [i["song_id"] for i in r.json()["items"]] == [songs[2], songs[1]]
    # Borrar (soft delete) → desaparece de la lista
    assert client.delete(f"/bands/{bid}/collections/{cid}").status_code == 204
    assert all(c["id"] != cid for c in client.get(f"/bands/{bid}/collections/").json())


def test_guest_no_edita_pero_ve(client):
    bid, songs = _band_with_repertoire(client)
    cid = client.post(f"/bands/{bid}/collections/",
                      json={"name": "C", "song_ids": songs}).json()["id"]
    with acting_as(GUEST):
        assert client.get(f"/bands/{bid}/collections/{cid}").status_code == 200
        assert client.patch(f"/bands/{bid}/collections/{cid}", json={"name": "X"}).status_code == 403
        assert client.post(f"/bands/{bid}/collections/", json={"name": "Y"}).status_code == 403


def test_miembro_gestiona_las_colecciones(client):
    bid, songs = _band_with_repertoire(client)
    with acting_as(MEMBER):
        r = client.post(f"/bands/{bid}/collections/", json={"name": "Del miembro", "song_ids": songs})
        assert r.status_code == 201


def test_coleccion_y_setlist_son_independientes(client):
    """Diferenciación: una colección NO es un setlist. Crear una colección no crea ningún setlist
    y viceversa (planos separados)."""
    bid, songs = _band_with_repertoire(client)
    client.post(f"/bands/{bid}/collections/", json={"name": "Solo colección", "song_ids": songs})
    client.post(f"/bands/{bid}/setlists/", json={"name": "Solo setlist", "song_ids": songs})
    cols = client.get(f"/bands/{bid}/collections/").json()
    sls = client.get(f"/bands/{bid}/setlists/").json()
    assert [c["name"] for c in cols] == ["Solo colección"]
    assert [s["name"] for s in sls] == ["Solo setlist"]


def test_aislamiento_un_ajeno_no_ve_ni_toca_las_colecciones(client):
    bid, songs = _band_with_repertoire(client)
    cid = client.post(f"/bands/{bid}/collections/",
                      json={"name": "C", "song_ids": songs}).json()["id"]
    with acting_as(STRANGER):
        assert client.get(f"/bands/{bid}/collections/").status_code == 404
        assert client.post(f"/bands/{bid}/collections/", json={"name": "Z"}).status_code == 404
        assert client.get(f"/bands/{bid}/collections/{cid}").status_code == 404
        assert client.patch(f"/bands/{bid}/collections/{cid}", json={"name": "Z"}).status_code == 404
        assert client.delete(f"/bands/{bid}/collections/{cid}").status_code == 404
