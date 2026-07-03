"""
Tests de identidad con imágenes (T-V5-06, Supabase Storage).

El Storage real no se toca (la subida es client-side): aquí se prueba el CONTRATO de la API que
guarda/sirve las URLs — `cover_url` de banda (PATCH admin), la validación de URL de imagen segura
(https, sin caracteres que escapen de src/url()) y el avatar del músico en la lista de miembros.
"""

import contextlib

import pytest

from src.main import app
from src.services.auth import get_current_user

pytestmark = pytest.mark.unit

TEST_USER = "00000000-0000-0000-0000-000000000000"
STRANGER = "99999999-9999-9999-9999-999999999999"
IMG = "https://fwynfifvtthtpzpejfhb.supabase.co/storage/v1/object/public/media/u/x.jpg"


@contextlib.contextmanager
def acting_as(user_id):
    app.dependency_overrides[get_current_user] = lambda: user_id
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_patch_cover_url_de_banda(client):
    """El admin guarda el fondo de cabecera; se devuelve en GET (banner con cover)."""
    bid = client.post("/bands/", json={"name": "Con Fondo"}).json()["id"]
    r = client.patch(f"/bands/{bid}", json={"cover_url": IMG})
    assert r.status_code == 200, r.text
    assert r.json()["cover_url"] == IMG
    assert client.get(f"/bands/{bid}").json()["cover_url"] == IMG


def test_cover_url_solo_admin_y_aislada(client):
    """Regla de oro: un ajeno no puede tocar (ni ver) la banda → 403/404."""
    bid = client.post("/bands/", json={"name": "Privada"}).json()["id"]
    with acting_as(STRANGER):
        r = client.patch(f"/bands/{bid}", json={"cover_url": IMG})
        assert r.status_code in (403, 404), r.text


@pytest.mark.parametrize("mala", [
    "http://insegura.com/x.jpg",              # sin https
    'https://a.com/x.jpg"onerror="alert(1)',  # comilla: escape de atributo src
    "https://a.com/x.jpg)*{background:red}",  # paréntesis: escape de url() en CSS
    "javascript:alert(1)",                    # esquema peligroso
])
def test_urls_de_imagen_invalidas_dan_422(client, mala):
    bid = client.post("/bands/", json={"name": "Estricta"}).json()["id"]
    assert client.patch(f"/bands/{bid}", json={"cover_url": mala}).status_code == 422
    assert client.patch(f"/bands/{bid}", json={"avatar_url": mala}).status_code == 422
    assert client.put("/profile/me", json={"avatar_url": mala}).status_code == 422


def test_avatar_del_perfil_llega_a_la_lista_de_miembros(client):
    """La foto del músico (avatar_url del perfil) sale en GET /bands/{id}/members → miembros
    con cara, no letras."""
    client.put("/profile/me", json={"display_name": "Oscar", "avatar_url": IMG})
    bid = client.post("/bands/", json={"name": "Con Caras"}).json()["id"]
    yo = next(m for m in client.get(f"/bands/{bid}/members").json()
              if m["user_id"] == TEST_USER)
    assert yo["avatar_url"] == IMG


def test_avatar_url_vacio_se_normaliza_a_none(client):
    """Enviar '' (borrar la foto) guarda NULL, no cadena vacía."""
    client.put("/profile/me", json={"avatar_url": IMG})
    r = client.put("/profile/me", json={"avatar_url": ""})
    assert r.status_code == 200
    assert r.json()["avatar_url"] is None
