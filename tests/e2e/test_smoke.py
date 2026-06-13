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
