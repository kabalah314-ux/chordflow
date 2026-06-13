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


def test_render_escapa_letra_y_acorde_maliciosos(js_page):
    """XSS (J3 / T-002): la letra y el chord_name del usuario no deben inyectar
    HTML ni ejecutar JS. Renderizamos una canción con payloads y verificamos que
    quedan escapados y que el onerror nunca se dispara."""
    result = js_page.evaluate(
        """() => {
            window.__xss = 0;
            const el = document.createElement('div');
            const song = { sections: [ { name: 'S', lines: [ {
                type: 'lyric',
                content: '<img src=x onerror=\\"window.__xss=1\\">hola',
                chords: [ { chord_name: '<b>A</b>', char_position: 0, id: 'c1' } ]
            } ] } ] };
            renderScoreInto(el, song, 0);
            document.body.appendChild(el);
            return {
                hasImg: !!el.querySelector('img'),
                hasBold: !!el.querySelector('b'),
                html: el.innerHTML,
                text: el.textContent,
            };
        }"""
    )
    assert result["hasImg"] is False          # no se creó un <img> real
    assert result["hasBold"] is False          # el chord_name no inyectó <b>
    assert "&lt;img" in result["html"]         # la letra quedó escapada
    assert "<img" not in result["html"]
    assert js_page.evaluate("window.__xss") == 0   # el onerror nunca se ejecutó
    assert "hola" in result["text"]            # la letra se conserva literal


def test_popup_diagrama_escapa_nombre_malicioso(page, live_server):
    """El popup de diagramas de acorde escapa el nombre (XSS de 2º orden, T-026).
    renderChordDiagramSVG vive en chord_shapes.js, que carga index.html."""
    page.goto(live_server + "/static/index.html", wait_until="networkidle")
    res = page.evaluate(
        """() => {
            window.__x = 0;
            const html = renderChordDiagramSVG(null, '<img src=x onerror=\\"window.__x=1\\">');
            const d = document.createElement('div');
            d.innerHTML = html;
            document.body.appendChild(d);
            return { hasImg: !!d.querySelector('img'), html };
        }"""
    )
    assert res["hasImg"] is False
    assert "&lt;img" in res["html"]
    assert page.evaluate("window.__x") == 0
