"""
E2E del editor: la vista previa renderiza al pegar (E1) y guardar redirige (E2).
"""

import json
import struct
import zlib

import pytest

from tests.conftest import SAMPLE_RAW, wipe_songs


def _png_bytes(width=2, height=2):
    """PNG RGB mínimo pero VÁLIDO (CRCs correctos) para que createImageBitmap lo decodifique en el
    test de foto→partitura (T-V5-11). Un base64 fijo daba 'source image could not be decoded'."""

    def chunk(typ, data):
        body = typ + data
        return (
            struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)
        )

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)  # 8-bit, RGB
    raw = b"".join(
        b"\x00" + b"\xff\x00\x00" * width for _ in range(height)
    )  # filtro 0 + píxeles rojos
    idat = zlib.compress(raw)
    return sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")


_PNG_1x1 = _png_bytes()

pytestmark = pytest.mark.e2e


def test_importar_desde_url_rellena_el_editor(page, live_server):
    """El botón 'Importar con IA' llama a /import y rellena el textarea + la vista previa
    (T-045). Mockeamos la respuesta del backend con Playwright para no depender de la IA real."""
    page.goto(live_server + "/static/editor.html", wait_until="networkidle")

    raw = "Verso:\nAm        C\nHola mundo de prueba"
    page.route(
        "**/import/",
        lambda route: route.fulfill(
            status=200, content_type="application/json", body=json.dumps({"raw_text": raw})
        ),
    )

    page.fill("#import-url", "https://www.lacuerda.net/cualquier-cancion")
    page.click("#btn-import")

    page.wait_for_function(
        "document.getElementById('raw-text').value.includes('Hola mundo')", timeout=8000
    )
    page.wait_for_selector(
        "#preview-content .chord-container, #preview-content .chord-pill", timeout=8000
    )


def test_buscar_cancion_por_nombre_rellena_url_e_importa(page, live_server):
    """T-162: escribir un nombre en el buscador pinta tarjetas de resultados; elegir una rellena
    el campo de URL y dispara el import normal (mockeamos ambas llamadas con Playwright)."""
    page.goto(live_server + "/static/editor.html", wait_until="networkidle")

    page.route(
        "**/import/search**",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "results": [
                        {
                            "title": "Wonderwall",
                            "artist": "Oasis",
                            "url": "https://www.cifraclub.com/oasis/wonderwall/",
                            "source": "CifraClub",
                        },
                    ]
                }
            ),
        ),
    )
    raw = "Verso:\nAm        C\nHola desde la búsqueda"
    page.route(
        "**/import/",
        lambda route: route.fulfill(
            status=200, content_type="application/json", body=json.dumps({"raw_text": raw})
        ),
    )

    page.fill("#import-search", "wonderwall")
    page.click("#btn-import-search")
    page.wait_for_selector(".import-search-item", timeout=8000)
    assert "Wonderwall" in page.inner_text(".import-search-item")

    page.click(".import-search-item")
    page.wait_for_function(
        "document.getElementById('import-url').value.includes('cifraclub')", timeout=8000
    )
    page.wait_for_function(
        "document.getElementById('raw-text').value.includes('Hola desde la búsqueda')", timeout=8000
    )


def test_buscar_cancion_sin_resultados_muestra_mensaje(page, live_server):
    page.goto(live_server + "/static/editor.html", wait_until="networkidle")
    page.route(
        "**/import/search**",
        lambda route: route.fulfill(
            status=200, content_type="application/json", body=json.dumps({"results": []})
        ),
    )
    page.fill("#import-search", "cancion que no existe")
    page.click("#btn-import-search")
    page.wait_for_selector(".import-search-empty", timeout=8000)


def test_importar_desde_foto_rellena_el_editor(page, live_server):
    """T-V5-11: elegir una foto → POST /import/photo (IA de visión mockeada) → rellena el textarea
    y la vista previa. La imagen se redimensiona en el cliente antes de enviarse."""
    page.goto(live_server + "/static/editor.html", wait_until="networkidle")
    raw = "Verso:\nAm        C\nHola desde la foto"
    page.route(
        "**/import/photo",
        lambda route: route.fulfill(
            status=200, content_type="application/json", body=json.dumps({"raw_text": raw})
        ),
    )

    page.set_input_files(
        "#import-photo",
        files=[{"name": "hoja.png", "mimeType": "image/png", "buffer": _PNG_1x1}],
    )
    page.wait_for_function(
        "document.getElementById('raw-text').value.includes('Hola desde la foto')", timeout=8000
    )
    page.wait_for_selector(
        "#preview-content .chord-container, #preview-content .chord-pill", timeout=8000
    )


def test_preview_renderiza_secciones_y_acordes(page, live_server):
    page.goto(live_server + "/static/editor.html", wait_until="networkidle")
    page.fill("#raw-text", SAMPLE_RAW)
    page.wait_for_timeout(300)  # updatePreview corre en el evento input
    preview = page.inner_text("#preview-content")
    # inner_text refleja el text-transform:uppercase del CSS en .section-name,
    # por eso comparamos insensible a mayúsculas.
    assert "verso 1" in preview.lower()  # sección detectada
    assert "Am" in preview  # acorde detectado
    assert "Hola mundo" in preview  # letra emparejada


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
