"""
E2E T-151 — Accesibilidad (remate de V4-F5).

Cubre los cuatro frentes de la tarea sin depender de un motor externo (axe), en línea
con el estilo del resto de la suite (selectores + getComputedStyle):
  1. aria-label en los botones solo-icono generados por JS (play/pin/thread).
  2. Todo botón del reproductor (la joya, la pantalla más densa en iconos) tiene nombre accesible.
  3. Contraste AA de los grises secundarios (--bf-text-faint sobre --bf-bg).
  4. Foco de teclado visible en los controles legacy.
"""

import pytest

from tests.conftest import sample_song_payload, wipe_songs

pytestmark = pytest.mark.e2e


# WCAG 2.1: ratio de contraste a partir de dos colores hex, calculado en el navegador.
_CONTRAST_JS = """
() => {
  const cs = getComputedStyle(document.documentElement);
  const hex = (v) => {
    const h = cs.getPropertyValue(v).trim().replace('#', '');
    return [0, 2, 4].map(i => parseInt(h.substr(i, 2), 16));
  };
  const lin = (c) => { c /= 255; return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); };
  const lum = (rgb) => 0.2126 * lin(rgb[0]) + 0.7152 * lin(rgb[1]) + 0.0722 * lin(rgb[2]);
  const a = lum(hex('--bf-text-faint')), b = lum(hex('--bf-bg'));
  const [hi, lo] = a > b ? [a, b] : [b, a];
  return (hi + 0.05) / (lo + 0.05);
}
"""


def test_play_de_setlist_tiene_aria_label(page, live_server, api):
    """El botón ▶ de cada setlist es solo-icono: debe llevar aria-label, no solo title."""
    a = api.post("/songs/", json=sample_song_payload(title="A11y Song")).json()["id"]
    api.post("/setlists/", json={"name": "A11y SL", "items": [{"song_id": a, "note": None}]})

    page.goto(live_server + "/static/setlists.html", wait_until="networkidle")
    page.wait_for_selector('.song-card:has-text("A11y SL")', timeout=8000)
    page.locator('.song-card:has-text("A11y SL")').first.click()

    play = page.wait_for_selector('.setlist-item-btn[data-act="play"]', timeout=8000)
    assert play.get_attribute("aria-label") == "Reproducir"


def test_contraste_de_grises_secundarios_es_AA(page, live_server, api):
    """--bf-text-faint sobre el fondo de la app cumple AA para texto normal (≥4.5:1)."""
    page.goto(live_server + "/static/setlists.html", wait_until="networkidle")
    ratio = page.evaluate(_CONTRAST_JS)
    assert ratio >= 4.5, f"contraste --bf-text-faint/--bf-bg = {ratio:.2f}:1 (< 4.5 AA)"


def test_botones_del_reproductor_tienen_nombre_accesible(page, live_server, api):
    """Cada <button> del reproductor expone un nombre accesible (aria-label, texto o title)."""
    wipe_songs(api)
    sid = api.post("/songs/", json=sample_song_payload(title="A11y Player")).json()["id"]
    page.goto(live_server + f"/static/index.html?songId={sid}", wait_until="networkidle")
    page.wait_for_selector(".chord-container, .chord-pill", timeout=8000)

    sin_nombre = page.evaluate(
        """() => [...document.querySelectorAll('button')]
              .filter(b => !((b.getAttribute('aria-label') || '').trim()
                          || (b.textContent || '').trim()
                          || (b.getAttribute('title') || '').trim()))
              .map(b => b.id || b.className)"""
    )
    assert sin_nombre == [], f"botones sin nombre accesible: {sin_nombre}"


def test_foco_de_teclado_es_visible_en_los_controles_del_lateral(page, live_server, api):
    """El toggle de tema del lateral (nuevo en T-151) tiene una regla :focus-visible con outline."""
    page.goto(live_server + "/static/app.html", wait_until="networkidle")
    btn = page.wait_for_selector("#bf-theme-btn", timeout=8000)
    assert btn is not None

    # Buscar en las hojas de estilo una regla :focus-visible que case con el botón y pinte outline.
    tiene_foco = page.evaluate(
        """() => {
            const el = document.querySelector('#bf-theme-btn');
            for (const sheet of document.styleSheets) {
                let rules; try { rules = sheet.cssRules; } catch (e) { continue; }
                for (const r of rules) {
                    if (!r.selectorText || !r.selectorText.includes(':focus-visible')) continue;
                    const base = r.selectorText.replace(/:focus-visible/g, '');
                    const casa = base.split(',').some(sel => {
                        try { return el.matches(sel.trim()); } catch (e) { return false; }
                    });
                    const out = (r.style.outline || r.style.outlineStyle || '').toLowerCase();
                    if (casa && out && out !== 'none') return true;
                }
            }
            return false;
        }"""
    )
    assert tiene_foco, "#bf-theme-btn no tiene regla :focus-visible con outline"
