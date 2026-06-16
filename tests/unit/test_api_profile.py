"""
Tests del perfil del músico (Fase 7, T-054).

GET crea el perfil vacío la primera vez; PUT lo edita; el nombre real aparece luego en la lista
de miembros de la banda (no UUIDs).
"""

import pytest

pytestmark = pytest.mark.unit

TEST_USER = "00000000-0000-0000-0000-000000000000"


def test_get_crea_perfil_vacio_la_primera_vez(client):
    r = client.get("/profile/me")
    assert r.status_code == 200
    assert r.json()["id"] == TEST_USER
    assert r.json()["display_name"] is None


def test_put_edita_el_perfil(client):
    r = client.put("/profile/me", json={
        "display_name": "Oscar Bajo",
        "instruments": ["bajo", "voz"],
    })
    assert r.status_code == 200
    body = r.json()
    assert body["display_name"] == "Oscar Bajo"
    assert body["instruments"] == ["bajo", "voz"]
    # Persiste
    assert client.get("/profile/me").json()["display_name"] == "Oscar Bajo"


def test_el_nombre_del_perfil_aparece_en_la_lista_de_miembros(client):
    client.put("/profile/me", json={"display_name": "Oscar Bajo"})
    bid = client.post("/bands/", json={"name": "Mi Banda"}).json()["id"]
    members = client.get(f"/bands/{bid}/members").json()
    yo = next(m for m in members if m["user_id"] == TEST_USER)
    assert yo["display_name"] == "Oscar Bajo"  # nombre real, no UUID
