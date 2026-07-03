"""
E2E T-V5-04 — Tema coherente.

- El editor y la página de invitación (join) respetan el tema claro/oscuro elegido en el shell
  (misma clave localStorage `bf-theme`), aunque no lleven el lateral.
- El reproductor (`index.html`) es "modo escenario" y se queda SIEMPRE oscuro (decisión D-EST-2):
  no aplica el tema aunque el usuario lo tenga en claro.
- Los botones legacy convergen al look del sistema SOLO en las páginas marcadas (editor/join),
  nunca en el reproductor (que comparte esas clases con la joya).
- Los badges de estado de evento usan tokens semánticos (adaptan al tema), no verdes/rojos fijos.
"""

import pytest

pytestmark = pytest.mark.e2e


def _theme(page):
    return page.evaluate("() => document.documentElement.getAttribute('data-theme')")


def test_editor_respeta_el_tema_claro(page, live_server):
    page.goto(live_server + "/static/editor.html", wait_until="networkidle")
    assert _theme(page) in (None, ""), "por defecto el editor arranca oscuro (sin data-theme)"

    # El usuario eligió claro en el shell → al volver al editor, este lo aplica.
    page.evaluate("localStorage.setItem('bf-theme','light')")
    page.reload(wait_until="networkidle")
    assert _theme(page) == "light", "el editor no aplicó el tema claro elegido en el shell"

    # Y el cristal de la top-bar se aclara (--bg-panel deja de ser oscuro fijo).
    rgb = page.evaluate("""() => {
        const c = getComputedStyle(document.querySelector('.top-bar')).backgroundColor;
        const m = c.match(/\\d+/g).map(Number);
        return m[0] + m[1] + m[2];
    }""")
    assert rgb > 500, f"la barra del editor sigue oscura en modo claro (suma RGB {rgb})"


def test_join_respeta_el_tema_claro(page, live_server):
    page.goto(live_server + "/static/join.html", wait_until="networkidle")
    page.evaluate("localStorage.setItem('bf-theme','light')")
    page.reload(wait_until="networkidle")
    assert _theme(page) == "light", "la página de invitación no aplicó el tema claro"


def test_reproductor_siempre_oscuro(page, live_server):
    # Aunque el usuario tenga el tema claro guardado, el player NO lo aplica (D-EST-2).
    page.goto(live_server + "/static/index.html", wait_until="networkidle")
    page.evaluate("localStorage.setItem('bf-theme','light')")
    page.reload(wait_until="networkidle")
    assert _theme(page) in (
        None,
        "",
    ), "el reproductor NO debe aplicar el tema claro (siempre oscuro)"


def test_botones_legacy_convergen_solo_en_el_editor(page, live_server):
    # En el editor, el botón primario adopta el radio del sistema (--bf-radius = 10px), no la píldora.
    page.goto(live_server + "/static/editor.html", wait_until="networkidle")
    r_editor = page.evaluate(
        "() => getComputedStyle(document.getElementById('btn-save')).borderTopLeftRadius"
    )
    assert r_editor == "10px", f"el botón del editor no convergió al sistema (radio {r_editor})"

    # En el reproductor comparte la clase pero NO lleva el override → conserva su forma de píldora.
    page.goto(live_server + "/static/index.html", wait_until="networkidle")
    r_player = page.evaluate(
        "() => getComputedStyle(document.getElementById('btn-play-pause')).borderTopLeftRadius"
    )
    assert r_player != "10px", f"el reproductor no debe converger (radio {r_player})"


def test_ev_status_usa_tokens_semanticos(page, live_server):
    # Inyectamos un badge de estado (editor.html carga style.css) y comprobamos que su color CAMBIA
    # con el tema → está tokenizado (--bf-success), no es el verde hardcodeado de antes.
    page.goto(live_server + "/static/editor.html", wait_until="networkidle")
    page.evaluate("""() => {
        const s = document.createElement('span');
        s.className = 'ev-status ev-status--confirmed';
        s.id = '__evtest'; s.textContent = 'ok';
        document.body.appendChild(s);
    }""")

    def color():
        return page.evaluate("() => getComputedStyle(document.getElementById('__evtest')).color")

    dark = color()
    page.evaluate("document.documentElement.dataset.theme = 'light'")
    light = color()
    assert dark != light, f"el color de ev-status no adapta al tema (sigue hardcodeado: {dark})"
