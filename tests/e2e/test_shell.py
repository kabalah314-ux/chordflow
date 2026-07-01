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


def test_shell_sin_margen_blanco_del_body(page, live_server, api):
    """El body se resetea a margin:0 en shell.css incluso en páginas que NO cargan style.css
    (agenda/finanzas/chat/inicio) → desaparece el marco/línea clara del margen por defecto (8px).
    Además el fondo va en `html` Y en `body`: si el rebote de scroll (overscroll de macOS) o un hueco
    dejan ver el `<html>`, debe ser oscuro y no el blanco por defecto → el marco no reaparece nunca."""
    page.goto(live_server + "/static/agenda.html", wait_until="networkidle")
    page.wait_for_selector(".bf-sidebar", timeout=8000)
    assert page.evaluate("getComputedStyle(document.body).margin") == "0px"
    # El <html> tiene fondo propio (no transparente) y coincide con el del body (ambos var(--bf-bg)).
    html_bg = page.evaluate("getComputedStyle(document.documentElement).backgroundColor")
    body_bg = page.evaluate("getComputedStyle(document.body).backgroundColor")
    assert html_bg not in ("rgba(0, 0, 0, 0)", "transparent", "rgb(255, 255, 255)")
    assert html_bg == body_bg


def test_shell_drawer_movil_abre_y_cierra(page, live_server, api):
    """En móvil el lateral es un DRAWER: oculto por defecto, se abre con ☰ y se cierra tocando el
    backdrop (en vez de la barra inferior anterior)."""
    page.set_viewport_size({"width": 390, "height": 780})
    page.goto(live_server + "/static/agenda.html", wait_until="networkidle")
    page.wait_for_selector(".bf-hamburger", timeout=8000)
    # Cerrado: el ☰ se ve y el shell no está en "nav-open"
    assert page.is_visible(".bf-hamburger")
    assert not page.evaluate("document.querySelector('.bf-shell').classList.contains('bf-nav-open')")
    # Abrir con ☰ → drawer completo (marca + nav)
    page.click(".bf-hamburger")
    page.wait_for_selector(".bf-shell.bf-nav-open", timeout=4000)
    assert "BandFlow" in page.inner_text(".bf-sidebar")
    # Cerrar tocando el backdrop
    page.click(".bf-backdrop", position={"x": 360, "y": 400})
    page.wait_for_function(
        "!document.querySelector('.bf-shell').classList.contains('bf-nav-open')", timeout=4000)


def test_shell_toggle_tema(page, live_server, api):
    page.goto(live_server + "/static/app.html", wait_until="networkidle")
    page.wait_for_selector("#bf-theme-btn", timeout=8000)
    # Por defecto oscuro (sin data-theme); el toggle pone tema claro y vuelve.
    assert page.get_attribute("html", "data-theme") is None
    page.click("#bf-theme-btn")
    assert page.get_attribute("html", "data-theme") == "light"
    page.click("#bf-theme-btn")
    assert page.get_attribute("html", "data-theme") is None


def test_shell_afinador_en_menu_justo_bajo_inicio(page, live_server, api):
    """T-161: el item "Afinador" vive en la nav principal, justo debajo de "Inicio", y navega
    a la página standalone."""
    page.goto(live_server + "/static/app.html", wait_until="networkidle")
    page.wait_for_selector(".bf-sidebar", timeout=8000)
    labels = page.eval_on_selector_all(
        ".bf-sidebar-nav > *", "els => els.map(e => e.textContent.trim())")
    idx_inicio = next(i for i, t in enumerate(labels) if "Inicio" in t)
    assert "Afinador" in labels[idx_inicio + 1], f"Afinador no está justo debajo de Inicio: {labels}"
    page.click('.bf-sidebar a.bf-nav-item:has-text("Afinador")')
    page.wait_for_url("**/afinador.html", timeout=8000)
    assert page.url.endswith("afinador.html")


def test_afinador_pagina_standalone_detecta_sin_boton(page, live_server, api):
    """T-161: en afinador.html no hay #btn-tuner (panel ya visible) y la detección de tono
    (función pura, sin micro real) sigue funcionando igual que en el player."""
    page.goto(live_server + "/static/afinador.html", wait_until="networkidle")
    page.wait_for_selector("#tuner-panel", timeout=8000)
    assert page.query_selector("#btn-tuner") is None
    assert page.is_visible("#tuner-panel")
    freq = page.evaluate("""() => {
        const sr = 44100, N = 2048, f = 440;
        const buf = new Float32Array(N);
        for (let i = 0; i < N; i++) buf[i] = Math.sin(2 * Math.PI * f * i / sr);
        return window.bfDetectPitch(buf, sr);
    }""")
    assert abs(freq - 440) < 8, f"detección de 440 Hz incorrecta: {freq}"
