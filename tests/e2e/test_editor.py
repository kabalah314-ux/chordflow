"""
E2E del editor: la vista previa renderiza al pegar (E1) y guardar redirige (E2).
"""

import pytest

from tests.conftest import SAMPLE_RAW, wipe_songs

pytestmark = pytest.mark.e2e


def test_preview_renderiza_secciones_y_acordes(page, live_server):
    page.goto(live_server + "/static/editor.html", wait_until="networkidle")
    page.fill("#raw-text", SAMPLE_RAW)
    page.wait_for_timeout(300)  # updatePreview corre en el evento input
    preview = page.inner_text("#preview-content")
    assert "Verso 1" in preview          # sección detectada
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
