"""
Tests del endpoint de importación desde URL con IA (T-045).

La llamada real a la IA/lector se MOCKEA (no se toca la red): probamos el contrato del endpoint
—auth, validación de URL, formato de respuesta y traducción de errores a mensajes de usuario—.
"""

import pytest

pytestmark = pytest.mark.unit


def test_import_devuelve_texto(client, monkeypatch):
    """POST /import/ con URL válida → 200 con el texto extraído (IA mockeada)."""
    from src.services import importer

    monkeypatch.setattr(importer, "import_from_url", lambda url: "Verso:\nAm  C\nhola mundo")
    # el router importó la función por nombre → parchear también ahí
    from src.api import import_router
    monkeypatch.setattr(import_router, "import_from_url", lambda url: "Verso:\nAm  C\nhola mundo")

    r = client.post("/import/", json={"url": "https://www.lacuerda.net/algo"})
    assert r.status_code == 200, r.text
    assert "hola mundo" in r.json()["raw_text"]


def test_import_url_invalida_da_422(client):
    """Una URL mal formada → 422 (HttpUrl la valida)."""
    assert client.post("/import/", json={"url": "no-soy-una-url"}).status_code == 422
    assert client.post("/import/", json={}).status_code == 422


def test_import_error_se_traduce_a_502(client, monkeypatch):
    """Un ImportError_ (página no legible, IA caída...) → 502 con el mensaje de usuario."""
    from src.api import import_router
    from src.services.importer import ImportError_

    def boom(url):
        raise ImportError_("No encontré una partitura de acordes en esa página.")

    monkeypatch.setattr(import_router, "import_from_url", boom)
    r = client.post("/import/", json={"url": "https://example.com/x"})
    assert r.status_code == 502
    assert "partitura" in r.json()["detail"]


def test_import_sin_token_da_401(client, monkeypatch):
    """El endpoint exige auth como el resto. Forzamos validación real (TEST_MODE off)."""
    from src.services import auth

    monkeypatch.setattr(auth, "TEST_MODE", False)
    r = client.post("/import/", json={"url": "https://example.com/x"})
    assert r.status_code == 401
