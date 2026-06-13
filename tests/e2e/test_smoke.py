"""
Smoke E2E: la app arranca y las páginas cargan sin errores de JS (S1),
y /config responde con test_mode (S3).
"""

import pytest

pytestmark = pytest.mark.e2e


def test_config_expone_test_mode(api):
    r = api.get("/config")
    assert r.status_code == 200
    assert r.json().get("test_mode") is True


@pytest.mark.parametrize("path", [
    "/static/login.html",
    "/static/library.html",
    "/static/editor.html",
])
def test_paginas_cargan_sin_errores_js(page, live_server, path):
    errores = []
    page.on("pageerror", lambda exc: errores.append(str(exc)))
    page.goto(live_server + path, wait_until="networkidle")
    assert errores == [], f"Errores JS en {path}: {errores}"


def test_apifetch_redirige_a_login_en_401(page, live_server):
    """Si una llamada autenticada devuelve 401, apiFetch lleva al login (T-006).
    La config ya está cacheada tras cargar la página, así que sobreescribir fetch
    solo afecta a la llamada a la API, no a getToken()."""
    page.goto(live_server + "/static/library.html", wait_until="networkidle")
    # Forzar que cualquier fetch posterior devuelva 401
    page.evaluate("() => { window.fetch = async () => new Response('{}', {status: 401}); }")
    page.evaluate("() => { apiFetch('/songs/'); }")
    page.wait_for_url("**/login.html", timeout=5000)
    assert page.url.endswith("login.html")
