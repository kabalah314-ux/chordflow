"""Reglas estructurales del frontend introducidas en la V6 (comprobación estática de ficheros)."""

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

STATIC = Path(__file__).resolve().parents[2] / "static"


def _html_pages():
    return sorted(p for p in STATIC.glob("*.html"))


@pytest.mark.parametrize("page", [p.name for p in _html_pages() if p.name != "index.html"])
def test_tema_se_aplica_en_head(page):
    """T-V6-14 (F-20): todas las páginas (salvo el reproductor, siempre oscuro por D-EST-2) cargan
    theme.js dentro de <head> → el tema claro se aplica antes del primer pintado, sin destello."""
    html = (STATIC / page).read_text(encoding="utf-8")
    head = html.split("</head>", 1)[0]
    assert re.search(r'<script src="theme\.js\?v=[0-9a-f]+"', head), f"{page}: falta theme.js en <head>"


def test_reproductor_no_carga_theme_js():
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    assert '<script src="theme.js' not in html


def test_404_con_marca_para_navegador_y_json_para_la_api(client):
    """T-V6-68: quien navega a una ruta que no existe ve la página 404 de BandFlow; la API sigue
    respondiendo JSON. T-V6-29: toda respuesta lleva X-Request-ID."""
    r = client.get("/no-existe-esto", headers={"Accept": "text/html"})
    assert r.status_code == 404 and "BandFlow" in r.text and "<html" in r.text
    r = client.get("/no-existe-esto", headers={"Accept": "application/json"})
    assert r.status_code == 404 and r.json()["detail"]
    assert r.headers.get("X-Request-ID")
    assert "microphone=(self)" in r.headers.get("Permissions-Policy", "")
