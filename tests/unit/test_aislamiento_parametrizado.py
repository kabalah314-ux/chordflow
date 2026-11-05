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
    ("GET", "/bands/{bid}/summary"),
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


# ── T-V6-27: gate DERIVADO de `app.routes` ────────────────────────────────────
# La lista manual de arriba se queda corta en cuanto alguien añade una ruta. Aquí se recorren TODAS
# las rutas registradas que llevan `{band_id}` y se exige que un ajeno reciba 403/404. Los demás
# parámetros de ruta se rellenan con un id inexistente (el guard de banda debe saltar antes).
def _band_routes_from_app():
    from fastapi.routing import APIRoute

    out = []
    for r in app.routes:
        # Las rutas /public/* son otro plano (sin sesión, proyección segura): tienen sus tests.
        if isinstance(r, APIRoute) and "{band_id}" in r.path and not r.path.startswith("/public/"):
            for m in sorted(r.methods - {"HEAD", "OPTIONS"}):
                out.append((m, r.path))
    return out


DERIVED = _band_routes_from_app()


def test_el_gate_derivado_cubre_rutas():
    # Si esto baja de golpe, alguien ha cambiado el prefijo y el gate dejaría de vigilar.
    assert len(DERIVED) >= 60, len(DERIVED)


@pytest.mark.parametrize("method,path", DERIVED)
def test_toda_ruta_de_banda_aisla_al_ajeno(client, method, path):
    import re

    bid = client.post("/bands/", json={"name": "Banda Gate"}).json()["id"]
    url = re.sub(r"\{(\w+)\}", lambda m: bid if m.group(1) == "band_id"
                 else "00000000-1111-2222-3333-444444444444", path)
    with acting_as(STRANGER):
        resp = client.request(method, url, json={})
    assert resp.status_code in (403, 404), \
        f"FUGA: {method} {path} respondió {resp.status_code} a un ajeno (esperado 403/404)"
