"""
E2E T-136 — Aprovechar el ancho en los listados (`.bf-page--wide`).

Los listados (Inicio, Bandas, Explorar, Biblioteca) usan `.bf-page--wide` (~1180px) en vez del
ancho de lectura (920px), para que las rejillas respiren. Lectura/formularios siguen a 920.
"""

import pytest

pytestmark = pytest.mark.e2e


def test_bf_page_wide_es_mas_ancho(page, live_server):
    page.goto(live_server + "/static/app.html", wait_until="networkidle")
    page.wait_for_selector(".bf-page--wide", timeout=8000)
    mw = page.evaluate(
        "() => getComputedStyle(document.querySelector('.bf-page--wide')).maxWidth")
    assert mw.endswith("px") and float(mw.replace("px", "")) > 920, f"no es más ancho: {mw}"
