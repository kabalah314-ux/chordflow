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


# ─── Foto → partitura con IA de visión (T-V5-11, beta) ─────────────────────────


def test_import_photo_devuelve_texto(client, monkeypatch):
    """POST /import/photo con imagen válida → 200 con el texto (IA de visión mockeada)."""
    from src.api import import_router

    monkeypatch.setattr(
        import_router, "extract_chords_from_image", lambda img: "Verso:\nAm  C\nhola foto"
    )
    r = client.post("/import/photo", json={"image": "data:image/png;base64,iVBORw0KGgo="})
    assert r.status_code == 200, r.text
    assert "hola foto" in r.json()["raw_text"]


def test_import_photo_error_se_traduce_a_502(client, monkeypatch):
    """Un ImportError_ (foto ilegible, IA de visión caída...) → 502 con el mensaje de usuario."""
    from src.api import import_router
    from src.services.importer import ImportError_

    def boom(img):
        raise ImportError_("No encontré una partitura de acordes en esa foto.")

    monkeypatch.setattr(import_router, "extract_chords_from_image", boom)
    r = client.post("/import/photo", json={"image": "data:image/png;base64,iVBORw0KGgo="})
    assert r.status_code == 502
    assert "foto" in r.json()["detail"]


def test_import_photo_sin_token_da_401(client, monkeypatch):
    from src.services import auth

    monkeypatch.setattr(auth, "TEST_MODE", False)
    r = client.post("/import/photo", json={"image": "data:image/png;base64,iVBORw0KGgo="})
    assert r.status_code == 401


def test_extract_chords_from_image_rechaza_lo_que_no_es_imagen(monkeypatch):
    """Con la clave puesta, una entrada que NO es un data URL de imagen → ImportError_ SIN tocar la red
    (el `_http_post_json` mockeado no debe llegar a llamarse)."""
    from src.services import importer
    from src.services.importer import ImportError_

    monkeypatch.setattr(importer.settings, "openrouter_api_key", "test-key")
    monkeypatch.setattr(
        importer,
        "_http_post_json",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("no debe llamar a la red")),
    )
    for bad in ("esto no es una imagen", "data:text/plain;base64,QQ==", ""):
        with pytest.raises(ImportError_):
            importer.extract_chords_from_image(bad)


# ─── Buscar canción por nombre (T-162) ─────────────────────────────────────────


def test_import_search_devuelve_candidatos(client, monkeypatch):
    """GET /import/search?q=... → 200 con la lista de candidatos (búsqueda mockeada)."""
    from src.api import import_router

    candidatos = [
        {
            "title": "Wonderwall",
            "artist": "Oasis",
            "url": "https://www.cifraclub.com/oasis/wonderwall/",
            "source": "CifraClub",
        },
        {
            "title": "Wonderwall (acústica)",
            "artist": "Oasis",
            "url": "https://www.lacuerda.net/oasis/wonderwall.html",
            "source": "LaCuerda",
        },
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


def test_search_song_usa_parsers_propios_sin_llamar_a_la_ia(monkeypatch):
    """T-163: si los parsers propios (sin IA) encuentran resultados, `search_song` no debe tocar
    ni `_fetch_via_jina` ni OpenRouter — la ruta gratis es la primaria, la IA es solo red de
    seguridad."""
    from src.services import importer

    def fake_fetch_raw_html(url):
        assert "wonderwall" in url.lower() or "exp=wonderwall" in url.lower()
        return "<html>fake</html>"

    def boom(*a, **kw):
        raise AssertionError("no debería llamar a la IA si los parsers propios ya respondieron")

    monkeypatch.setattr(importer, "_fetch_raw_html", fake_fetch_raw_html)
    monkeypatch.setattr(importer, "_fetch_via_jina", boom)
    monkeypatch.setattr(importer, "_rank_search_results", boom)
    # search_song llama a los parsers a través del registro _SITE_ADAPTERS (referencias
    # capturadas al definir el dict) — hay que parchear ahí, no el nombre suelto del módulo.
    fake_adapters = {
        "cifraclub.com": {
            **importer._SITE_ADAPTERS["cifraclub.com"],
            "parse_search": lambda page, query: [
                {
                    "title": "Wonderwall",
                    "artist": "Oasis",
                    "url": "https://www.cifraclub.com/oasis/wonderwall/",
                    "source": "CifraClub",
                }
            ],
        },
        "lacuerda.net": {
            **importer._SITE_ADAPTERS["lacuerda.net"],
            "parse_search": lambda page, query: [],
        },
    }
    monkeypatch.setattr(importer, "_SITE_ADAPTERS", fake_adapters)

    results = importer.search_song("wonderwall")
    assert len(results) == 1
    assert results[0]["title"] == "Wonderwall"


def test_search_song_cae_a_ia_si_los_parsers_no_encuentran_nada(monkeypatch):
    """Si ningún parser propio da resultados (sitio caído, estructura cambiada...), cae al
    flujo con IA de siempre — sin romper para el usuario."""
    from src.services import importer

    # HTML sin ninguno de los patrones esperados: los parsers reales devuelven [] solos.
    monkeypatch.setattr(importer, "_fetch_raw_html", lambda url: "<html>sin resultados</html>")

    llm_called_with = []

    def fake_search_via_llm(query):
        llm_called_with.append(query)
        return [
            {"title": "Wonderwall", "artist": "Oasis", "url": "https://x.com/w", "source": "web"}
        ]

    monkeypatch.setattr(importer, "_search_song_via_llm", fake_search_via_llm)

    results = importer.search_song("wonderwall")
    assert llm_called_with == ["wonderwall"]
    assert len(results) == 1


def test_search_song_query_vacia_no_llama_a_nada(monkeypatch):
    from src.services import importer

    def boom(*a, **kw):
        raise AssertionError("no debería llamar a la red con query vacía")

    monkeypatch.setattr(importer, "_fetch_raw_html", boom)
    monkeypatch.setattr(importer, "_fetch_via_jina", boom)
    assert importer.search_song("   ") == []


def test_search_song_via_llm_todos_los_sitios_fallan_da_import_error(monkeypatch):
    """El fallback con IA (`_search_song_via_llm`) sigue lanzando ImportError_ si ningún sitio
    responde — mismo contrato que antes de T-163."""
    from src.services import importer

    def fake_fetch_via_jina(url):
        raise RuntimeError("red caída")

    monkeypatch.setattr(importer, "_fetch_via_jina", fake_fetch_via_jina)
    with pytest.raises(importer.ImportError_):
        importer._search_song_via_llm("wonderwall")


def test_extract_json_array_ignora_code_fences():
    from src.services.importer import _extract_json_array

    texto = '```json\n[{"title": "X", "artist": "Y", "url": "https://a.com"}]\n```'
    data = _extract_json_array(texto)
    assert data == [{"title": "X", "artist": "Y", "url": "https://a.com"}]
    assert _extract_json_array("no hay json aquí") == []


# ─── Parsers propios sin IA — CifraClub/LaCuerda (T-163) ───────────────────────
# Fixtures recortadas pero fieles: fragmentos reales de las páginas de CifraClub/LaCuerda
# (estructura verificada a mano, no inventada) para que los tests validen el parser de verdad.

CC_SEARCH_HTML = """
<li class="QDh1y"><div class="JknkR"><a href="/aerosmith/i-dont-wanna-miss-thing/">
<img alt="Portada de la canción &quot;I Don't Want to Miss a Thing&quot;, de Aerosmith"></a></div></li>
<li class="QDh1y"><div class="JknkR"><a href="/oasis/wonderwall/"><div class="ZOQ tileHorizontal-song TGdHp">
<img alt="Portada de la canción &quot;Wonderwall&quot;, de Oasis"></div></a></div></li>
"""

CC_SONG_HTML = (
    '<article data-chord-container="true" class="XjgwI"><pre class="_crVx" style="font-size:1.4rem">'
    '<div>[Intro] <b data-chord-name="Em7" data-chord-scope-id="inline-chord-0">Em7</b>  '
    '<b data-chord-name="G" data-chord-scope-id="inline-chord-1">G</b></div>\n'
    "<div>[Primera Parte]</div>\n"
    '<div><b data-chord-name="Em7" data-chord-scope-id="inline-chord-2">Em7</b>           '
    '<b data-chord-name="G" data-chord-scope-id="inline-chord-3">G</b></div>\n'
    "<div>    Today is gonna be the day</div>\n"
    "<div>That they&#x27;re gonna</div>\n"
    "</pre></article>"
)

LC_SEARCH_HTML = """
<table id=s_main onclick='chOpen(event)'><col width=25%><col width=75%>
<tr><td>
<a href="/caligaris/">Los Caligaris</A></TD><td><ul class=b_main id=b_main0>
<li id='r000' lcd='RR-12'><a href="javascript:">El Oasis</a></li>
</ul></td></tr>
<tr><td>
<a href="/suenio_inmoral/">Sueño Inmoral</A></TD><td><ul class=b_main id=b_main1>
<li id='r001' lcd='R-1'><a href="javascript:">Oasis</a></li>
</ul></td></tr></table>
<script>
var hds=['caligaris','suenio_inmoral'];
var fns=['oasis','oasis_de_agua_fresca'];
var NMAX=15;
</script>
"""

LC_SONG_HTML = (
    "<pre><A>A</A>          <A>C</A>      <A>G</A>\n"
    "Te sugiero no movernos\n"
    "<A>A</A>\n"
    "de esta habitación.\n"
    "</pre></div></li>"
)


def test_parse_cifraclub_search_filtra_por_relevancia():
    from src.services.importer import _parse_cifraclub_search

    results = _parse_cifraclub_search(CC_SEARCH_HTML, "wonderwall")
    assert len(results) == 1
    assert results[0] == {
        "title": "Wonderwall",
        "artist": "Oasis",
        "url": "https://www.cifraclub.com/oasis/wonderwall/",
        "source": "CifraClub",
    }


def test_parse_cifraclub_search_sin_query_no_filtra():
    from src.services.importer import _parse_cifraclub_search

    results = _parse_cifraclub_search(CC_SEARCH_HTML, "")
    assert len(results) == 2


def test_parse_cifraclub_song_extrae_acordes_y_secciones():
    from src.services.importer import _parse_cifraclub_song

    text = _parse_cifraclub_song(CC_SONG_HTML)
    assert text is not None
    assert "Primera Parte:" in text  # [Primera Parte] -> "Primera Parte:"
    assert "Em7           G" in text  # el <b data-chord-name> se sustituye por el nombre
    assert "Today is gonna be the day" in text
    assert "That they're gonna" in text  # &#x27; desescapado
    assert "<b" not in text and "<div" not in text


def test_parse_cifraclub_song_sin_acordes_devuelve_none():
    from src.services.importer import _parse_cifraclub_song

    assert _parse_cifraclub_song("<html><body>nada de acordes aquí</body></html>") is None


def test_parse_lacuerda_search_respeta_el_orden_invertido_de_fns():
    """El nombre real de la canción (para la URL) va en `fns`, pero en orden INVERSO al de las
    filas/`hds` — verificado con una canción real (acordes.lacuerda.net/suenio_inmoral/oasis
    responde 200). Esta fixture reproduce exactamente ese caso: fila 0 (Caligaris/El Oasis) debe
    emparejar con fns[1]='oasis_de_agua_fresca', NO con fns[0]='oasis'."""
    from src.services.importer import _parse_lacuerda_search

    results = _parse_lacuerda_search(LC_SEARCH_HTML, "oasis")
    assert len(results) == 2
    assert results[0]["artist"] == "Los Caligaris"
    assert results[0]["title"] == "El Oasis"
    assert results[0]["url"] == "https://acordes.lacuerda.net/caligaris/oasis_de_agua_fresca"
    assert results[1]["artist"] == "Sueño Inmoral"
    assert results[1]["url"] == "https://acordes.lacuerda.net/suenio_inmoral/oasis"


def test_parse_lacuerda_search_longitudes_no_cuadran_devuelve_vacio():
    """Si `hds`/`fns` no cuadran en longitud con las filas, no arriesga un enlace equivocado."""
    from src.services.importer import _parse_lacuerda_search

    html_roto = LC_SEARCH_HTML.replace(
        "var fns=['oasis','oasis_de_agua_fresca'];", "var fns=['oasis'];"
    )
    assert _parse_lacuerda_search(html_roto, "oasis") == []


def test_parse_lacuerda_song_extrae_acordes():
    from src.services.importer import _parse_lacuerda_song

    text = _parse_lacuerda_song(LC_SONG_HTML)
    assert text is not None
    assert "A          C      G" in text
    assert "Te sugiero no movernos" in text
    assert "de esta habitación." in text
    assert "<A>" not in text


def test_parse_lacuerda_song_sin_acordes_devuelve_none():
    from src.services.importer import _parse_lacuerda_song

    assert _parse_lacuerda_song("<pre>solo texto sin acordes</pre>") is None


def test_adapter_for_host_reconoce_dominio_y_subdominio():
    from src.services.importer import _adapter_for_host

    assert _adapter_for_host("www.cifraclub.com") is not None
    assert _adapter_for_host("cifraclub.com") is not None
    assert _adapter_for_host("acordes.lacuerda.net") is not None
    assert _adapter_for_host("www.ultimate-guitar.com") is None


def test_import_from_url_usa_parser_propio_sin_llamar_a_la_ia(monkeypatch):
    """T-163: si el dominio tiene parser propio y consigue extraer texto, `import_from_url` no
    debe tocar `fetch_page_text`/`extract_chords` (la IA)."""
    from src.services import importer

    monkeypatch.setattr(importer, "_fetch_raw_html", lambda url: CC_SONG_HTML)

    def boom(*a, **kw):
        raise AssertionError("no debería llamar a la IA si el parser propio ya extrajo la letra")

    monkeypatch.setattr(importer, "fetch_page_text", boom)
    monkeypatch.setattr(importer, "extract_chords", boom)

    text = importer.import_from_url("https://www.cifraclub.com/oasis/wonderwall/")
    assert "Today is gonna be the day" in text


def test_import_from_url_cae_a_ia_si_el_parser_no_extrae_nada(monkeypatch):
    from src.services import importer

    monkeypatch.setattr(importer, "_fetch_raw_html", lambda url: "<html>sin acordes</html>")
    monkeypatch.setattr(importer, "fetch_page_text", lambda url: "texto crudo de la página")
    monkeypatch.setattr(
        importer, "extract_chords", lambda text: "Verso:\nAm  C\nresultado de la IA"
    )

    text = importer.import_from_url("https://www.cifraclub.com/oasis/wonderwall/")
    assert text == "Verso:\nAm  C\nresultado de la IA"


def test_import_from_url_sin_adaptador_va_directo_a_ia(monkeypatch):
    """Un dominio sin parser propio (p. ej. Ultimate Guitar) sigue el flujo de siempre, sin
    tocar `_fetch_raw_html`."""
    from src.services import importer

    def boom(*a, **kw):
        raise AssertionError("no debería intentar el fetch crudo para un dominio sin adaptador")

    monkeypatch.setattr(importer, "_fetch_raw_html", boom)
    monkeypatch.setattr(importer, "fetch_page_text", lambda url: "texto crudo")
    monkeypatch.setattr(importer, "extract_chords", lambda text: "resultado IA")

    text = importer.import_from_url("https://tabs.ultimate-guitar.com/x")
    assert text == "resultado IA"
