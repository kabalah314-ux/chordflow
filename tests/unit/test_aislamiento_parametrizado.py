"""
Gate de aislamiento multi-tenant (V3-F3, T-098).

La "regla de oro" del giro V2/V3: CADA ruta de banda valida pertenencia+rol y filtra por `band_id`.
Cada router tiene además su test de aislamiento propio; este test es un **gate transversal**: recorre
una a una las rutas de banda y exige que un **usuario ajeno** reciba 403/404. Si alguien añade una
ruta de banda y olvida el guard `require_band_member`/`require_band_admin`, este test lo caza.
"""

import contextlib

import pytest

from src.main import app
from src.services.auth import get_current_user

pytestmark = pytest.mark.unit

STRANGER = "99999999-9999-9999-9999-999999999999"


@contextlib.contextmanager
def acting_as(user_id):
    app.dependency_overrides[get_current_user] = lambda: user_id
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_current_user, None)


# (método, plantilla de ruta). El {bid} se rellena con una banda real creada por su dueño.
BAND_ROUTES = [
    ("GET", "/bands/{bid}"),
    ("PATCH", "/bands/{bid}"),
    ("DELETE", "/bands/{bid}"),
    ("GET", "/bands/{bid}/members"),
    ("GET", "/bands/{bid}/songs/"),
    ("POST", "/bands/{bid}/songs/"),
    ("GET", "/bands/{bid}/setlists/"),
    ("GET", "/bands/{bid}/collections/"),
    ("POST", "/bands/{bid}/collections/"),
    ("GET", "/bands/{bid}/events/"),
    ("POST", "/bands/{bid}/events/"),
    ("GET", "/bands/{bid}/venues/"),
    ("POST", "/bands/{bid}/venues/"),
    ("GET", "/bands/{bid}/transactions"),
    ("GET", "/bands/{bid}/balances"),
    ("GET", "/bands/{bid}/settlements"),
    ("GET", "/bands/{bid}/messages"),
    ("POST", "/bands/{bid}/messages"),
    ("GET", "/bands/{bid}/tours/"),
    ("POST", "/bands/{bid}/tours/"),
]


@pytest.mark.parametrize("method,path", BAND_ROUTES)
def test_ruta_de_banda_aisla_al_ajeno(client, method, path):
    # La banda la crea su dueño (el usuario de prueba por defecto del fixture `client`).
    bid = client.post("/bands/", json={"name": "Banda Aislada"}).json()["id"]
    url = path.format(bid=bid)
    # Un usuario ajeno NUNCA debe poder tocarla: 404 (no existe para él) o 403 (sin permiso).
    with acting_as(STRANGER):
        resp = client.request(method, url, json={})
    assert resp.status_code in (403, 404), \
        f"FUGA: {method} {path} respondió {resp.status_code} a un ajeno (esperado 403/404)"
