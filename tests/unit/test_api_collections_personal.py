"""
Tests de las colecciones PERSONALES (equivalente personal de los Repertorios de banda, T-114).
CRUD owner-scoped + solo mis canciones personales + aislamiento (ajeno → 404).
"""

import contextlib

import pytest

from src.main import app
from src.services.auth import get_current_user
from tests.conftest import sample_song_payload

pytestmark = pytest.mark.unit

STRANGER = "99999999-9999-9999-9999-999999999999"


@contextlib.contextmanager
def acting_as(user_id):
    app.dependency_overrides[get_current_user] = lambda: user_id
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def _song(client, title):
    return client.post("/songs/", json=sample_song_payload(title=title)).json()["id"]


def test_crud_coleccion_personal(client):
    a = _song(client, "Cancion A")
    b = _song(client, "Cancion B")

    # Crear con dos canciones
    r = client.post("/collections/", json={"name": "Acustico", "song_ids": [a, b]})
    assert r.status_code == 201, r.text
    col = r.json()
    cid = col["id"]
    assert col["name"] == "Acustico" and col["band_id"] is None
    assert [i["song_id"] for i in col["items"]] == [a, b]

    # Listar (resumen) + detalle
    lst = client.get("/collections/").json()
    assert len(lst) == 1 and lst[0]["song_count"] == 2 and lst[0]["band_id"] is None
    assert client.get(f"/collections/{cid}").status_code == 200

    # Renombrar + cambiar canciones
    r2 = client.patch(f"/collections/{cid}", json={"name": "Canero", "song_ids": [b]})
    assert r2.status_code == 200 and r2.json()["name"] == "Canero"
    assert [i["song_id"] for i in r2.json()["items"]] == [b]

    # Borrar (soft) → desaparece
    assert client.delete(f"/collections/{cid}").status_code == 204
    assert client.get(f"/collections/{cid}").status_code == 404
    assert client.get("/collections/").json() == []


def test_coleccion_personal_solo_mis_canciones(client):
    a = _song(client, "Mia")
    # Una canción de OTRO usuario no entra en mi colección
    with acting_as(STRANGER):
        ajena = client.post("/songs/", json=sample_song_payload(title="Ajena")).json()["id"]
    r = client.post("/collections/", json={"name": "X", "song_ids": [a, ajena, "inventada-123"]})
    assert r.status_code == 201
    assert [i["song_id"] for i in r.json()["items"]] == [a]


def test_aislamiento_coleccion_personal_ajena_404(client):
    a = _song(client, "Mia")
    cid = client.post("/collections/", json={"name": "Privada", "song_ids": [a]}).json()["id"]
    with acting_as(STRANGER):
        assert client.get("/collections/").json() == []
        assert client.get(f"/collections/{cid}").status_code == 404
        assert client.patch(f"/collections/{cid}", json={"name": "Hack"}).status_code == 404
        assert client.delete(f"/collections/{cid}").status_code == 404
