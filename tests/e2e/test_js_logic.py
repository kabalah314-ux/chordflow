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


def test_parser_detecta_tablatura(js_page):
    """Un bloque de tablatura ASCII se reconoce como UNA línea type 'tab' con el contenido
    multilínea preservado en content (UI de tablaturas)."""
    raw = (
        "Riff:\n"
        "e|---0---3---|\n"
        "B|---1---1---|\n"
        "G|---0---0---|\n"
        "D|---2---2---|\n"
    )
    sections = js_page.evaluate("(t) => parseRawText(t)", raw)
    assert len(sections) == 1
    tabs = [ln for ln in sections[0]["lines"] if ln["type"] == "tab"]
    assert len(tabs) == 1, "las 4 cuerdas consecutivas deben ser UNA sola línea tab"
    assert "e|---0---3---|" in tabs[0]["content"]
    assert tabs[0]["content"].count("\n") == 3  # 4 cuerdas → 3 saltos de línea
    assert all(ln["type"] != "lyric" for ln in sections[0]["lines"])  # no se cuela como letra


def test_istabline_no_colisiona_con_letra_ni_acordes(js_page):
    """isTabLine distingue una cuerda de tab de letra/acordes/intro (no falsos positivos)."""
    assert js_page.evaluate("isTabLine('e|---0---3---|')") is True
    assert js_page.evaluate("isTabLine('E|-5-7-8-----|')") is True
    assert js_page.evaluate("isTabLine('Hola mundo --- adios')") is False  # letras de palabra
    assert js_page.evaluate("isTabLine('Am        C')") is False           # línea de acordes
    assert js_page.evaluate("isTabLine(': F#m : C#7 :')") is False         # intro


def test_render_pinta_tablatura_segura(js_page):
    """renderScoreInto pinta una línea 'tab' como <pre class='line-tab'> con el texto literal
    y escapa cualquier inyección (usa textContent, no innerHTML)."""
    result = js_page.evaluate(
        """() => {
            window.__tx = 0;
            const el = document.createElement('div');
            const song = { sections: [ { name: 'R', lines: [ {
                type: 'tab',
                content: 'e|--0--<img src=x onerror=\\"window.__tx=1\\">--|'
            } ] } ] };
            renderScoreInto(el, song, 0);
            document.body.appendChild(el);
            const pre = el.querySelector('pre.line-tab');
            return { hasPre: !!pre, hasImg: !!el.querySelector('img'),
                     text: pre ? pre.textContent : '', html: el.innerHTML };
        }"""
    )
    assert result["hasPre"] is True
    assert result["hasImg"] is False
    assert "e|--0--" in result["text"]
    assert "&lt;img" in result["html"]
    assert js_page.evaluate("window.__tx") == 0


def test_tablatura_roundtrip_editor(js_page):
    """songToRawText(parse(x)) reproduce la tab y re-parsear da el mismo bloque: necesario para
    EDITAR una canción con tablatura sin perderla."""
    raw = "Riff:\ne|---0---3---|\nB|---1---1---|"
    out = js_page.evaluate(
        """(t) => {
            const sections = parseRawText(t);
            const back = songToRawText({ sections });
            const reparsed = parseRawText(back);
            const tabs = reparsed[0].lines.filter(l => l.type === 'tab');
            return { n_tabs: tabs.length, content: tabs[0] ? tabs[0].content : '' };
        }""",
        raw,
    )
    assert out["n_tabs"] == 1
    assert "e|---0---3---|" in out["content"]
    assert "B|---1---1---|" in out["content"]


def test_ischord_reconoce_acordes_extendidos(js_page):
    """El parser reconoce acordes con extensiones de 2 cifras y alteraciones encadenadas
    que el regex viejo NO captaba (T-020): add11, maj13, sus2, m7b5, 7sus4."""
    validos = ["Am", "F#m7", "C#7", "G/B", "Bb", "Dmaj7", "Csus2", "Cadd9",
               "Cadd11", "Cmaj13", "Em7b5", "A7sus4", "C/F#", "C13"]
    for ch in validos:
        assert js_page.evaluate("(c) => isChord(c)", ch) is True, f"{ch} debería ser acorde"

    # Palabras normales que NO deben colarse como acordes.
    no_validos = ["Hola", "Bad", "Age", "Casa", "Dios", "Feo"]
    for w in no_validos:
        assert js_page.evaluate("(c) => isChord(c)", w) is False, f"{w} no es acorde"


def test_transpose_sube_y_baja_semitonos(js_page):
    assert js_page.evaluate("transposeChord('Am', 2)") == "Bm"
    assert js_page.evaluate("transposeChord('C', 1)") == "C#"
    assert js_page.evaluate("transposeChord('G/B', 2)") == "A/C#"  # preserva el bajo
    assert js_page.evaluate("transposeChord('F#m7', -1)") == "Fm7"  # preserva el sufijo


def test_transpose_respeta_bemoles(js_page):
    """Un acorde con bemol se transpone a teclas negras CON bemoles, no sostenidos (T-018):
    antes `Bb`+3 daba `C#`; ahora da `Db`. Las raíces sostenidas/naturales siguen en sostenidos."""
    # Raíz con bemol → escala de bemoles
    assert js_page.evaluate("transposeChord('Bb', 3)") == "Db"   # antes: C#
    assert js_page.evaluate("transposeChord('Eb', -2)") == "Db"
    assert js_page.evaluate("transposeChord('Bbm7', 3)") == "Dbm7"  # preserva sufijo
    # Naturales que caen en negra → sostenidos (sin cambio de comportamiento)
    assert js_page.evaluate("transposeChord('C', 3)") == "D#"
    # Cada parte conserva su estilo: bajo en bemol sigue en bemol
    assert js_page.evaluate("transposeChord('F/Bb', 3)") == "G#/Db"


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
