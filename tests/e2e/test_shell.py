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


def test_shell_nav_usa_iconos_svg(page, live_server, api):
    # T-085 (V3-F1): los emojis del lateral se reemplazaron por iconos SVG (Lucide auto-alojado).
    page.goto(live_server + "/static/app.html", wait_until="networkidle")
    page.wait_for_selector(".bf-sidebar", timeout=8000)
    # Cada item de navegación pinta su icono como <svg> dentro de .bf-nav-icon
    svg_icons = page.query_selector_all(".bf-sidebar .bf-nav-item .bf-nav-icon svg")
    assert len(svg_icons) >= 7, f"esperaba ≥7 iconos SVG en la nav, hay {len(svg_icons)}"
    # El helper global existe y devuelve un <svg>
    assert page.evaluate("typeof window.bfIcon === 'function'"), "falta el helper global bfIcon"
    assert "<svg" in page.evaluate("window.bfIcon('home')"), "bfIcon no devuelve un SVG"


def test_ui_helper_empty_state(page, live_server, api):
    # T-087 (V3-F1): bfEmpty genera el componente de estado vacío (.bf-empty de T-084) con icono SVG.
    # Lo usan las vistas agregadas (Inicio/Agenda/Finanzas/Chat) cuando no hay datos.
    page.goto(live_server + "/static/app.html", wait_until="networkidle")
    page.wait_for_selector(".bf-sidebar", timeout=8000)
    html = page.evaluate(
        "window.bfEmpty('calendar', 'Nada por aquí', 'Sin contenido. <a href=\"bands.html\">Crear</a>.')")
    assert "bf-empty" in html, "bfEmpty no usa el componente .bf-empty"
    assert "<svg" in html, "bfEmpty no incluye el icono SVG"
    assert "Nada por aquí" in html and "bands.html" in html


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
