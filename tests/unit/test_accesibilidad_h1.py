"""
Unit T-V5-05 — las páginas dinámicas del shell llevan un <h1> en el DOM estático.

Antes, páginas como Inicio/Agenda/Finanzas/Chat sólo tenían un <p> "Cargando…" hasta que el JS
pintaba su cabecera; el documento inicial no exponía ningún encabezado (accesibilidad, menor).
"""

import pathlib

import pytest

pytestmark = pytest.mark.unit

STATIC = pathlib.Path(__file__).resolve().parents[2] / "static"


@pytest.mark.parametrize("archivo", ["app.html", "agenda.html", "finanzas.html", "chat.html"])
def test_pagina_dinamica_tiene_h1_estatico(archivo):
    html = (STATIC / archivo).read_text(encoding="utf-8")
    assert "<h1" in html, f"{archivo} no tiene un <h1> en el DOM estático"
