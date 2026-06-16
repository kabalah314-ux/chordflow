"""
E2E del dashboard de Inicio (`app.html`, Fase 13, T-076).

Muestra próximos eventos + últimos mensajes de mis bandas, cada uno con su etiqueta de banda.
"""

import pytest

pytestmark = pytest.mark.e2e


def test_home_muestra_eventos_y_mensajes(page, live_server, api):
    bid = api.post("/bands/", json={"name": "Banda Inicio"}).json()["id"]
    # Fecha futura CERCANA → ordena entre los primeros (robusto al límite de 10).
    api.post(f"/bands/{bid}/events/",
             json={"type": "concert", "title": "Concierto Inicio", "starts_at": "2026-06-20T21:00:00"})
    api.post(f"/bands/{bid}/messages/", json={"body": "Mensaje de inicio E2E"})

    page.goto(live_server + "/static/app.html", wait_until="networkidle")
    page.wait_for_selector("#home-events", timeout=8000)
    assert "Próximos eventos" in page.inner_text("#home")
    assert "Concierto Inicio" in page.inner_text("#home-events")
    assert "Banda Inicio" in page.inner_text("#home-events")   # etiqueta de banda
    assert "Mensaje de inicio E2E" in page.inner_text("#home-messages")
