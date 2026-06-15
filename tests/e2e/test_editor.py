"""
E2E del editor: la vista previa renderiza al pegar (E1) y guardar redirige (E2).
"""

import json

import pytest

from tests.conftest import SAMPLE_RAW, wipe_songs

pytestmark = pytest.mark.e2e


def test_importar_desde_url_rellena_el_editor(page, live_server):
    """El botón 'Importar con IA' llama a /import y rellena el textarea + la vista previa
    (T-045). Mockeamos la respuesta del backend con Playwright para no depender de la IA real."""
    page.goto(live_server + "/static/editor.html", wait_until="networkidle")

    raw = "Verso:\nAm        C\nHola mundo de prueba"
    page.route("**/import/", lambda route: route.fulfill(
        status=200, content_type="application/json",
        body=json.dumps({"raw_text": raw})))

    page.fill("#import-url", "https://www.lacuerda.net/cualquier-cancion")
    page.click("#btn-import")

    page.wait_for_function("document.getElementById('raw-text').value.includes('Hola mundo')",
                           timeout=8000)
    page.wait_for_selector("#preview-content .chord-container, #preview-content .chord-pill",
                           timeout=8000)


def test_preview_renderiza_secciones_y_acordes(page, live_server):
    page.goto(live_server + "/static/editor.html", wait_until="networkidle")
    page.fill("#raw-text", SAMPLE_RAW)
    page.wait_for_timeout(300)  # updatePreview corre en el evento input
    preview = page.inner_text("#preview-content")
    # inner_text refleja el text-transform:uppercase del CSS en .section-name,
    # por eso comparamos insensible a mayúsculas.
    assert "verso 1" in preview.lower()  # sección detectada
    assert "Am" in preview               # acorde detectado
    assert "Hola mundo" in preview       # letra emparejada


def test_guardar_redirige_al_reproductor(page, live_server, api):
    wipe_songs(api)
    page.goto(live_server + "/static/editor.html", wait_until="networkidle")
    page.fill("#title", "Cancion Editor E2E")
    page.fill("#raw-text", SAMPLE_RAW)
    page.click("#btn-save")
    page.wait_for_url("**/index.html?songId=*", timeout=8000)
    assert "songId=" in page.url
    # Y la canción quedó guardada
    titulos = [s["title"] for s in api.get("/songs/").json()]
    assert "Cancion Editor E2E" in titulos
