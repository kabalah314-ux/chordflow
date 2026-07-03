"""
E2E T-V5-05 — Detalles de pulido.

- El avatar de cada conversación del Chat va coloreado por banda (`bandColor`), como el lateral.
- Los resultados de la búsqueda de importación son focables por teclado (tabindex/role) y se activan
  con Enter, con foco visible.
- La aguja del afinador está atenuada en reposo (no finge "afinado") y sin copy redundante.
- La página pública de evento siempre ofrece un CTA de registro/vuelta a la app.
"""

import json

import pytest

pytestmark = pytest.mark.e2e


def test_chat_avatar_coloreado_por_banda(page, live_server, api):
    api.post("/bands/", json={"name": "Banda Color"})
    page.goto(live_server + "/static/chat.html", wait_until="networkidle")
    page.wait_for_selector("#chat-list .bf-avatar", timeout=8000)
    # bandColor pone un `background` inline (hsl); el navegador lo serializa a rgb. Basta con que
    # exista un background inline (un avatar sin colorear no lo tiene) → coloreado por banda.
    bg = page.evaluate("() => document.querySelector('#chat-list .bf-avatar').style.background")
    assert bg, f"el avatar del chat no está coloreado por banda (background inline vacío: {bg!r})"


def test_resultados_de_importacion_focables_por_teclado(page, live_server):
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
                        }
                    ]
                }
            ),
        ),
    )
    page.route(
        "**/import/",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({"raw_text": "Verso:\nAm C\nHola teclado"}),
        ),
    )

    page.fill("#import-search", "wonderwall")
    page.click("#btn-import-search")
    page.wait_for_selector(".import-search-item", timeout=8000)
    item = page.locator(".import-search-item").first
    assert item.get_attribute("tabindex") == "0"
    # Patrón listbox/option → conserva la semántica de lista para lectores de pantalla.
    assert item.get_attribute("role") == "option"
    assert page.get_attribute("#import-search-results", "role") == "listbox"

    # Activación por teclado: foco + Enter dispara el import (rellena la URL elegida).
    item.focus()
    page.keyboard.press("Enter")
    page.wait_for_function(
        "document.getElementById('import-url').value.includes('cifraclub')", timeout=8000
    )


def test_aguja_afinador_atenuada_en_reposo(page, live_server):
    page.goto(live_server + "/static/afinador.html", wait_until="networkidle")
    page.wait_for_selector("#tuner-needle", timeout=8000)
    op = page.evaluate("() => getComputedStyle(document.getElementById('tuner-needle')).opacity")
    assert float(op) < 1.0, f"la aguja del afinador no está atenuada en reposo (opacity {op})"
    # Y no queda el mensaje redundante con el botón "Activar micrófono".
    msg = page.inner_text("#tuner-msg")
    assert "activar el micrófono" not in msg.lower(), f"copy redundante en el afinador: {msg!r}"


def test_evento_publico_tiene_cta(page, live_server):
    # Sin id → 'evento no disponible', pero SIEMPRE con el CTA de registro (gancho viral).
    page.goto(live_server + "/static/evento.html", wait_until="networkidle")
    page.wait_for_selector(".pub-cta__btn", timeout=8000)
    assert "BandFlow" in page.inner_text(".pub-cta__btn")
