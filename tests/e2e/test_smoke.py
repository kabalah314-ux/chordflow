"""
Smoke E2E: la app arranca y las páginas cargan sin errores de JS (S1),
y /config responde con test_mode (S3).
"""

import time

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

    Determinista (T-042). Dos carreras que antes hacían este test flaky:
    1. La caché de `/config`: si `networkidle` salta antes de que `_cfg` esté cacheada,
       sobreescribir `fetch` rompe `getConfig()` y `getToken()` lanzaría antes del 401.
       → lo evitamos calentando la caché con un `getToken()` real previo.
    2. `login.js` rebota a `library.html` cuando HAY sesión (modo test → siempre la hay),
       así que exigir *quedarse* en login.html era una carrera contra ese rebote.
       → comprobamos que la navegación de apiFetch PASÓ por login.html (aunque rebote)."""
    page.goto(live_server + "/static/library.html", wait_until="networkidle")
    page.evaluate("async () => { await getToken(); }")  # caché de config con fetch REAL

    navegaciones = []
    page.on("framenavigated", lambda f: navegaciones.append(f.url))

    page.evaluate("() => { window.fetch = async () => new Response('{}', {status: 401}); }")
    page.evaluate("() => { apiFetch('/songs/'); }")

    # Esperar a que la navegación pase por login.html (login.js puede rebotar después).
    deadline = time.time() + 5
    while time.time() < deadline and not any("login.html" in u for u in navegaciones):
        page.wait_for_timeout(50)
    assert any("login.html" in u for u in navegaciones), (
        f"apiFetch no redirigió a login tras un 401; navegaciones vistas: {navegaciones}")
