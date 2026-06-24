"""
E2E T-122 — `icons.js` disponible en el reproductor y el editor.

Hasta ahora `icons.js` (que define `bfIcon`) NO se cargaba en `index.html` (player) ni en
`editor.html`; sin él no se pueden sustituir los emoji por SVG (T-123/T-124). Aquí se comprueba
que `bfIcon` es una función en ambas páginas y que devuelve un `<svg>` para los iconos nuevos.
"""

import pytest

pytestmark = pytest.mark.e2e


def test_iconos_disponibles_en_player(page, live_server):
    page.goto(live_server + "/static/index.html", wait_until="networkidle")
    assert page.evaluate("typeof bfIcon") == "function"
    # Un icono nuevo del reproductor (play) devuelve SVG.
    assert "<svg" in page.evaluate("bfIcon('play')")
    # Varios de los añadidos en T-122 existen (no caen al fallback 'music').
    for name in ("pause", "stop", "save", "printer", "mic", "maximize", "trash", "x"):
        assert "<svg" in page.evaluate("(n) => bfIcon(n)", name)


def test_iconos_disponibles_en_editor(page, live_server):
    page.goto(live_server + "/static/editor.html", wait_until="networkidle")
    assert page.evaluate("typeof bfIcon") == "function"
    assert "<svg" in page.evaluate("bfIcon('edit')")
