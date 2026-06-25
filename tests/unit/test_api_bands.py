"""
Tests de la API de bandas (Fase 7, T-051).

Happy path (crear→listar→ver→editar→borrar como creador-admin) + **aislamiento por cada ruta**
(usuario ajeno → 404): la "regla de oro" multi-tenant aplicada a las rutas reales.
El usuario actuante se cambia overrideando `get_current_user` en la app real.
"""

import contextlib

import pytest

from src.main import app
from src.services.auth import get_current_user

pytestmark = pytest.mark.unit

STRANGER = "99999999-9999-9999-9999-999999999999"


@contextlib.contextmanager
def acting_as(user_id):
    """Hace que get_current_user devuelva `user_id` mientras dure el bloque."""
    app.dependency_overrides[get_current_user] = lambda: user_id
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_list_my_bands_incluye_song_count(client):
    """T-132: GET /bands/ devuelve `song_count` = nº de canciones (activas) de la banda, agregado
    sin N+1. Recién creada → 0; tras añadir 2 canciones → 2."""
    from tests.conftest import sample_song_payload

    bid = client.post("/bands/", json={"name": "Con Canciones"}).json()["id"]
    assert client.get("/bands/").json()[0]["song_count"] == 0
    client.post(f"/bands/{bid}/songs/", json=sample_song_payload(title="A"))
    client.post(f"/bands/{bid}/songs/", json=sample_song_payload(title="B"))
    band = next(b for b in client.get("/bands/").json() if b["id"] == bid)
    assert band["song_count"] == 2


def test_crud_completo_de_banda(client):
    # Crear → el creador entra como admin
    r = client.post("/bands/", json={"name": "Los Tres", "description": "rock"})
    assert r.status_code == 201, r.text
    band = r.json()
    bid = band["id"]
    assert band["name"] == "Los Tres"

    # Aparece en "mis bandas" con rol admin y 1 miembro
    lst = client.get("/bands/").json()
    assert len(lst) == 1
    assert lst[0]["id"] == bid
    assert lst[0]["role"] == "admin"
    assert lst[0]["member_count"] == 1

    # Ver detalle
    assert client.get(f"/bands/{bid}").json()["name"] == "Los Tres"

    # Editar (admin)
    r = client.patch(f"/bands/{bid}", json={"name": "Los Cuatro"})
    assert r.status_code == 200
    assert r.json()["name"] == "Los Cuatro"

    # Borrar (soft delete) → 204; deja de aparecer y de poder verse
    assert client.delete(f"/bands/{bid}").status_code == 204
    assert client.get("/bands/").json() == []
    assert client.get(f"/bands/{bid}").status_code == 404


def test_aislamiento_por_ruta_un_ajeno_no_ve_ni_toca(client):
    bid = client.post("/bands/", json={"name": "Privada"}).json()["id"]

    with acting_as(STRANGER):
        assert client.get("/bands/").json() == []            # no es suya → no la lista
        assert client.get(f"/bands/{bid}").status_code == 404  # ver → 404
        assert client.patch(f"/bands/{bid}", json={"name": "Hackeada"}).status_code == 404
        assert client.delete(f"/bands/{bid}").status_code == 404

    # Y la banda sigue intacta para su dueño
    assert client.get(f"/bands/{bid}").json()["name"] == "Privada"


def test_no_se_puede_crear_banda_sin_nombre(client):
    assert client.post("/bands/", json={"name": ""}).status_code == 422
