"""
E2E V3-F7 (oEmbed) — Carátula del vídeo de referencia al pegar el enlace en el editor.

Al pegar un enlace de YouTube en "Enlace de referencia", aparece su carátula (miniatura determinista
de img.youtube.com, sin red ni CORS). Un enlace que no es de YouTube no muestra nada.
"""

import pytest

pytestmark = pytest.mark.e2e


def test_caratula_youtube_aparece_al_pegar_el_enlace(page, live_server):
    page.goto(live_server + "/static/editor.html", wait_until="networkidle")
    # Editor en blanco → sin carátula.
    assert page.locator("#reference-preview").is_hidden()

    page.fill("#reference-url", "https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    img = page.wait_for_selector("#reference-preview .ref-thumb img", timeout=8000)
    assert img.get_attribute("src") == "https://img.youtube.com/vi/dQw4w9WgXcQ/hqdefault.jpg"

    # La forma corta youtu.be también funciona.
    page.fill("#reference-url", "https://youtu.be/abc123XYZ_-")
    page.wait_for_function(
        "document.querySelector('#reference-preview .ref-thumb img')?.src.includes('abc123XYZ_-')",
        timeout=8000)

    # Un enlace que no es de YouTube oculta la carátula.
    page.fill("#reference-url", "https://example.com/no-es-video")
    page.wait_for_selector("#reference-preview .ref-thumb", state="detached", timeout=8000)
    assert page.locator("#reference-preview").is_hidden()
