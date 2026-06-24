"""
E2E T-120 — Acento unificado + modo claro en páginas legacy.

Tras hacer que `style.css` herede del token `--bf-primary` del design-system (que ahora cargan
también las páginas legacy), el acento es UNO solo y el modo claro funciona gratis: togglear
`data-theme="light"` cambia el color resuelto del acento (en claro el coral es distinto).

Se usa un nodo de prueba con `color: var(--accent-color)` porque `getPropertyValue('--accent-color')`
devolvería el valor SIN resolver (`var(--bf-primary, …)`); solo `getComputedStyle().color` de un
elemento real resuelve la cadena de variables al RGB final.
"""

import pytest

pytestmark = pytest.mark.e2e


def _resolved_accent(page):
    """Color RGB resuelto de --accent-color (vía un nodo de prueba reutilizado)."""
    return page.evaluate(
        "() => { let p = document.getElementById('__accent_probe');"
        " if (!p) { p = document.createElement('span'); p.id = '__accent_probe';"
        " p.style.color = 'var(--accent-color)'; document.body.appendChild(p); }"
        " return getComputedStyle(p).color; }"
    )


def test_acento_unificado_y_tema(page, live_server):
    # setlists.html es legacy (style.css) y ahora carga design-system.css (T-120).
    page.goto(live_server + "/static/setlists.html", wait_until="networkidle")

    # 1) El design-system está cargado → la var --bf-primary resuelve (no vacía).
    bf_primary = page.evaluate(
        "getComputedStyle(document.documentElement).getPropertyValue('--bf-primary').trim()"
    )
    assert bf_primary != "", "design-system.css no se cargó en la página legacy (--bf-primary vacío)"

    # 2) El acento resuelve al coral del token (no al verde-menta muerto ni a transparente).
    dark = _resolved_accent(page)
    assert dark == "rgb(255, 107, 74)", f"El acento no hereda del token coral: {dark}"

    # 3) Togglear a modo claro → el acento CAMBIA (en claro es un coral distinto, #ee5530).
    page.evaluate("document.documentElement.dataset.theme = 'light'")
    light = _resolved_accent(page)
    assert light != dark, f"El modo claro no cambia el acento (oscuro={dark}, claro={light})"
    assert light == "rgb(238, 85, 48)", f"El acento en claro no es el esperado: {light}"
