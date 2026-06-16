"""
E2E del app shell (Fase 13, T-074 — contexto TÚ).

`app.html` monta el lateral de BandFlow vía `shell.js`: marca, navegación con item activo,
items "Pronto" para páginas aún no construidas, tarjeta de perfil y toggle de tema.
"""

import pytest

pytestmark = pytest.mark.e2e


def test_shell_lateral_aparece_con_marca_y_nav(page, live_server, api):
    page.goto(live_server + "/static/app.html", wait_until="networkidle")
    page.wait_for_selector(".bf-sidebar", timeout=8000)
    nav = page.inner_text(".bf-sidebar")
    assert "BandFlow" in nav                       # wordmark de marca
    for label in ("Inicio", "Biblioteca", "Bandas", "Perfil"):
        assert label in nav, f"falta el item de nav {label}"
    # En app.html el item activo es Inicio
    activo = page.inner_text('.bf-nav-item[aria-current="page"]')
    assert "Inicio" in activo


def test_shell_navega_entre_secciones(page, live_server, api):
    page.goto(live_server + "/static/app.html", wait_until="networkidle")
    page.wait_for_selector(".bf-sidebar", timeout=8000)
    page.click('.bf-sidebar a.bf-nav-item:has-text("Bandas")')
    page.wait_for_url("**/bands.html", timeout=8000)
    assert page.url.endswith("bands.html")


def test_shell_agenda_navega(page, live_server, api):
    # Agenda ya es una página real (T-078): el item del lateral navega.
    page.goto(live_server + "/static/app.html", wait_until="networkidle")
    page.wait_for_selector(".bf-sidebar", timeout=8000)
    page.click('.bf-sidebar a.bf-nav-item:has-text("Agenda")')
    page.wait_for_url("**/agenda.html", timeout=8000)
    assert page.url.endswith("agenda.html")


def test_shell_toggle_tema(page, live_server, api):
    page.goto(live_server + "/static/app.html", wait_until="networkidle")
    page.wait_for_selector("#bf-theme-btn", timeout=8000)
    # Por defecto oscuro (sin data-theme); el toggle pone tema claro y vuelve.
    assert page.get_attribute("html", "data-theme") is None
    page.click("#bf-theme-btn")
    assert page.get_attribute("html", "data-theme") == "light"
    page.click("#bf-theme-btn")
    assert page.get_attribute("html", "data-theme") is None
