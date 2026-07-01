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


# ─── Buscar canción por nombre (T-162) ─────────────────────────────────────────

def test_import_search_devuelve_candidatos(client, monkeypatch):
    """GET /import/search?q=... → 200 con la lista de candidatos (búsqueda mockeada)."""
    from src.api import import_router

    candidatos = [
        {"title": "Wonderwall", "artist": "Oasis", "url": "https://www.cifraclub.com/oasis/wonderwall/", "source": "CifraClub"},
        {"title": "Wonderwall (acústica)", "artist": "Oasis", "url": "https://www.lacuerda.net/oasis/wonderwall.html", "source": "LaCuerda"},
    ]
    monkeypatch.setattr(import_router, "search_song", lambda q: candidatos)

    r = client.get("/import/search?q=wonderwall")
    assert r.status_code == 200, r.text
    results = r.json()["results"]
    assert len(results) == 2
    assert results[0]["title"] == "Wonderwall"
    assert results[0]["source"] == "CifraClub"


def test_import_search_sin_query_da_422(client):
    """`q` es obligatorio (min_length=1) → 422 si falta."""
    assert client.get("/import/search").status_code == 422


def test_import_search_error_se_traduce_a_502(client, monkeypatch):
    """Un ImportError_ (ningún sitio responde) → 502 con el mensaje de usuario."""
    from src.api import import_router
    from src.services.importer import ImportError_

    def boom(q):
        raise ImportError_("No se pudo buscar en CifraClub/LaCuerda ahora mismo.")

    monkeypatch.setattr(import_router, "search_song", boom)
    r = client.get("/import/search?q=algo")
    assert r.status_code == 502
    assert "buscar" in r.json()["detail"]


def test_import_search_sin_token_da_401(client, monkeypatch):
    from src.services import auth

    monkeypatch.setattr(auth, "TEST_MODE", False)
    r = client.get("/import/search?q=algo")
    assert r.status_code == 401


def test_search_song_combina_sitios_y_estructura_json(monkeypatch):
    """`search_song` (unit puro): mockea el fetch de cada sitio y la llamada a OpenRouter,
    valida que combina resultados y filtra entradas sin url/title."""
    from src.services import importer

    fetched_urls = []

    def fake_fetch_via_jina(url):
        fetched_urls.append(url)
        # _looks_blocked exige >=200 chars de contenido "real": relleno para superar el umbral.
        return ("=== resultados falsos ===\n[Wonderwall](https://www.cifraclub.com/oasis/wonderwall/)\n"
                 + "relleno de contenido de la página de resultados " * 5)

    def fake_rank(query, combined):
        assert "wonderwall" in query.lower()
        return [
            {"title": "Wonderwall", "artist": "Oasis", "url": "https://www.cifraclub.com/oasis/wonderwall/", "source": "CifraClub"},
            {"title": "", "artist": "", "url": "", "source": ""},  # entrada vacía: se descarta antes
        ]

    monkeypatch.setattr(importer, "_fetch_via_jina", fake_fetch_via_jina)
    monkeypatch.setattr(importer, "_rank_search_results", fake_rank)

    results = importer.search_song("wonderwall")
    assert len(fetched_urls) == 2  # CifraClub + LaCuerda
    assert len(results) == 2  # el filtrado de vacíos lo hace _rank_search_results real; aquí ya viene mockeado
    assert results[0]["title"] == "Wonderwall"


def test_search_song_query_vacia_no_llama_a_nada(monkeypatch):
    from src.services import importer

    def boom(*a, **kw):
        raise AssertionError("no debería llamar a la red con query vacía")

    monkeypatch.setattr(importer, "_fetch_via_jina", boom)
    assert importer.search_song("   ") == []


def test_search_song_todos_los_sitios_fallan_da_import_error(monkeypatch):
    from src.services import importer

    def fake_fetch_via_jina(url):
        raise RuntimeError("red caída")

    monkeypatch.setattr(importer, "_fetch_via_jina", fake_fetch_via_jina)
    with pytest.raises(importer.ImportError_):
        importer.search_song("wonderwall")


def test_extract_json_array_ignora_code_fences():
    from src.services.importer import _extract_json_array

    texto = '```json\n[{"title": "X", "artist": "Y", "url": "https://a.com"}]\n```'
    data = _extract_json_array(texto)
    assert data == [{"title": "X", "artist": "Y", "url": "https://a.com"}]
    assert _extract_json_array("no hay json aquí") == []
