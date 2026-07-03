"""
E2E T-154 — Perfil con cuerpo (parte cliente, sin Storage).

El perfil deja de ser sólo un formulario: muestra identidad — avatar de iniciales/color, mis bandas
como chips con rol (GET /bands/) e instrumentos como chips — además del formulario de edición, cuyos
ids (#pf-name/#pf-inst/#pf-save) se conservan.
"""

import pytest

from tests.conftest import wipe_bands

pytestmark = pytest.mark.e2e


def test_perfil_muestra_avatar_bandas_e_instrumentos(page, live_server, api):
    wipe_bands(api)
    # avatar_url: "" → sin foto (el perfil PERSISTE entre tests; otro test pudo dejar una foto
    # puesta — T-V5-06 — y aquí se asierta el avatar de INICIALES).
    api.put("/profile/me", json={"display_name": "Ana Músico", "instruments": ["guitarra", "voz"],
                                 "avatar_url": ""})
    api.post("/bands/", json={"name": "Banda Perfil"})   # el usuario de prueba entra como admin

    page.goto(live_server + "/static/profile.html", wait_until="networkidle")
    page.wait_for_selector(".pf-identity", timeout=8000)

    # Avatar de iniciales (T-121): "Ana Músico" → "AM".
    assert page.inner_text(".pf-identity .bf-avatar--lg").strip() == "AM"
    assert "Ana Músico" in page.inner_text(".pf-name")

    # Mis bandas: un chip con el nombre y el badge de rol Admin.
    chips = page.locator("#pf-bands .pf-band-chip")
    assert chips.count() == 1
    assert "Banda Perfil" in chips.first.inner_text()
    assert page.locator("#pf-bands .bf-badge--admin").count() == 1

    # Instrumentos como chips.
    inst = page.locator("#pf-instruments .bf-badge")
    assert inst.count() == 2
    textos = [t.strip().lower() for t in inst.all_inner_texts()]   # .bf-badge capitaliza por CSS
    assert "guitarra" in textos and "voz" in textos

    # El formulario de edición sigue ahí, prerrellenado (ids intactos).
    assert page.input_value("#pf-name") == "Ana Músico"
    assert page.input_value("#pf-inst") == "guitarra, voz"


def test_perfil_sin_bandas_muestra_estado_vacio(page, live_server, api):
    wipe_bands(api)
    api.put("/profile/me", json={"display_name": "Solo Yo", "instruments": []})

    page.goto(live_server + "/static/profile.html", wait_until="networkidle")
    page.wait_for_selector(".pf-identity", timeout=8000)

    # Sin bandas → estado vacío (helper bfEmpty), sin chips.
    assert page.locator("#pf-bands .pf-band-chip").count() == 0
    assert page.locator("#pf-bands .bf-empty").count() == 1
