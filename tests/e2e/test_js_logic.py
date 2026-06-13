"""
Verificación de la lógica JS pura ejecutándola en el navegador (J1, J2).
Se navega al editor (que carga editor.js + score_render.js) y se evalúan las
funciones globales `parseRawText` y `transposeChord` con page.evaluate.
"""

import pytest

pytestmark = pytest.mark.e2e


@pytest.fixture()
def js_page(page, live_server):
    page.goto(live_server + "/static/editor.html", wait_until="networkidle")
    return page


def test_parser_detecta_acordes_y_secciones(js_page):
    raw = "Verso 1:\nAm        C\nHola que tal amigo\n"
    sections = js_page.evaluate("(t) => parseRawText(t)", raw)
    assert len(sections) == 1
    assert sections[0]["name"] == "Verso 1"
    nombres = [c["chord_name"] for line in sections[0]["lines"] for c in line["chords"]]
    assert "Am" in nombres and "C" in nombres


def test_transpose_sube_y_baja_semitonos(js_page):
    assert js_page.evaluate("transposeChord('Am', 2)") == "Bm"
    assert js_page.evaluate("transposeChord('C', 1)") == "C#"
    assert js_page.evaluate("transposeChord('G/B', 2)") == "A/C#"  # preserva el bajo
    assert js_page.evaluate("transposeChord('F#m7', -1)") == "Fm7"  # preserva el sufijo
