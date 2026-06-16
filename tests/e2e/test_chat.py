"""
E2E del Chat agregado (`chat.html`, Fase 13, T-080).

Lista una conversación por banda (chat general) con el último mensaje; entrar abre el chat de la banda.
"""

import pytest

pytestmark = pytest.mark.e2e


def test_chat_lista_conversaciones_por_banda(page, live_server, api):
    bid = api.post("/bands/", json={"name": "Banda Charla"}).json()["id"]
    api.post(f"/bands/{bid}/messages/", json={"body": "Hola desde el chat agregado"})

    page.goto(live_server + "/static/chat.html", wait_until="networkidle")
    page.wait_for_selector("#chat-list", timeout=8000)
    lista = page.inner_text("#chat-list")
    assert "Banda Charla" in lista
    assert "Hola desde el chat agregado" in lista
