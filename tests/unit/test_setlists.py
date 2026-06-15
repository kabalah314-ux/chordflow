"""
Tests de la API de repertorios/setlists (Fase 5).
CRUD + orden + filtrado de canciones ajenas/borradas + soft delete.
"""

import pytest

from tests.conftest import sample_song_payload

pytestmark = pytest.mark.unit


def _crear_cancion(client, title):
    return client.post("/songs/", json=sample_song_payload(title=title)).json()["id"]


def test_crud_setlist(client):
    a = _crear_cancion(client, "Cancion A")
    b = _crear_cancion(client, "Cancion B")

    # Crear con dos canciones en orden B, A
    r = client.post("/setlists/", json={"name": "Mi bolo", "song_ids": [b, a]})
    assert r.status_code == 201, r.text
    sl = r.json()
    sid = sl["id"]
    assert sl["name"] == "Mi bolo"
    assert [i["song_id"] for i in sl["items"]] == [b, a]
    assert [i["position"] for i in sl["items"]] == [0, 1]
    assert sl["items"][0]["title"] == "Cancion B"

    # Listar
    lst = client.get("/setlists/").json()
    assert len(lst) == 1 and lst[0]["song_count"] == 2

    # Detalle
    det = client.get(f"/setlists/{sid}").json()
    assert [i["song_id"] for i in det["items"]] == [b, a]

    # Reordenar + renombrar (PATCH)
    r = client.patch(f"/setlists/{sid}", json={"name": "Bolo finde", "song_ids": [a, b]})
    assert r.status_code == 200
    assert r.json()["name"] == "Bolo finde"
    assert [i["song_id"] for i in r.json()["items"]] == [a, b]

    # Borrar (soft)
    assert client.delete(f"/setlists/{sid}").status_code == 204
    assert client.get(f"/setlists/{sid}").status_code == 404
    assert client.get("/setlists/").json() == []


def test_filtra_canciones_no_validas(client):
    a = _crear_cancion(client, "Real")
    r = client.post("/setlists/", json={"name": "X", "song_ids": [a, "id-inventado-1234"]})
    assert r.status_code == 201
    # La canción inexistente se descarta; solo queda la real.
    assert [i["song_id"] for i in r.json()["items"]] == [a]


def test_cancion_borrada_no_aparece_en_el_setlist(client):
    a = _crear_cancion(client, "Se borrara")
    b = _crear_cancion(client, "Se queda")
    sid = client.post("/setlists/", json={"name": "L", "song_ids": [a, b]}).json()["id"]
    # Soft-delete de la canción A
    client.delete(f"/songs/{a}")
    det = client.get(f"/setlists/{sid}").json()
    assert [i["song_id"] for i in det["items"]] == [b]


def test_setlist_validacion_nombre(client):
    assert client.post("/setlists/", json={"name": "", "song_ids": []}).status_code == 422


def test_setlist_sin_token_da_401(client, monkeypatch):
    from src.services import auth
    monkeypatch.setattr(auth, "TEST_MODE", False)
    assert client.get("/setlists/").status_code == 401
