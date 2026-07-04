"""Importar una partitura desde una URL, y buscarla por nombre (T-045, T-162, T-163).

Dos flujos, con IA como red de seguridad en ambos:

1. **Parser propio por sitio (T-163, sin IA)**: para CifraClub y LaCuerda, cuyo HTML es lo
   bastante estable (verificado a mano) para sacar título/artista/acordes/letra con regex puro
   — sin gastar una llamada a OpenRouter ni pasar por el lector Jina. Es la ruta primaria tanto
   para buscar por nombre como para importar desde una URL de esos dos sitios.
2. **Lector + IA (flujo original)**: si el dominio no tiene parser propio, o el parser no
   encuentra nada fiable (sitio caído, estructura cambiada...), se cae a descargar el contenido
   con un lector que renderiza JS y sortea anti-bot (Jina Reader) y pedir a un modelo
   (OpenRouter, compatible OpenAI, modelo gratuito) que devuelva SOLO la partitura en el formato
   de texto que entiende el editor (`parseRawText`):

    Sección:
    Am        C        G
    Letra de la canción alineada bajo sus acordes

    (línea en blanco entre secciones)

No usa SDKs externos: todas las llamadas van por urllib (stdlib), igual que `auth_provider.py`.
La clave de OpenRouter es gratuita y va en `.env.local` (nunca al frontend).
"""

import html
import json
import logging
import re
import urllib.error
import urllib.parse
import urllib.request

from .config import settings

logger = logging.getLogger(__name__)

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124 Safari/537.36"
)


class ImportError_(Exception):
    """Error de importación con mensaje apto para mostrar al usuario."""


# Instrucción al modelo: salida en el formato del editor, sin adornos.
_SYSTEM_PROMPT = (
    "Eres un extractor de partituras de acordes. Recibes el texto crudo de una página web "
    "(de sitios como Ultimate Guitar o LaCuerda) y devuelves SOLO la canción en este formato "
    "de texto plano, sin explicaciones ni markdown:\n"
    "- Cada sección empieza con su nombre seguido de dos puntos (p. ej. 'Verso:', 'Estribillo:').\n"
    "- La línea de ACORDES va justo encima de su línea de LETRA, con los acordes alineados por "
    "posición sobre la sílaba correspondiente (usa espacios para alinear).\n"
    "- Una línea en blanco entre secciones.\n"
    "- Conserva los acordes tal cual (Am, F#m7, Csus4, G/B...). No inventes acordes ni letra.\n"
    "- Ignora anuncios, menús, comentarios y cualquier cosa que no sea la canción.\n"
    "Si la página no contiene una partitura de acordes, responde exactamente: SIN_PARTITURA"
)


def _http_post_json(url: str, payload: dict, headers: dict, timeout: float = 45.0) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def _looks_blocked(text: str) -> bool:
    """Heurística: ¿la respuesta del lector es un muro anti-bot / error / vacío, no contenido?"""
    if len(text.strip()) < 200:
        return True
    head = text[:400].lower()
    señales = (
        "just a moment",
        "error 403",
        "error 404",
        "error 429",
        "forbidden",
        "rate limit",
        "captcha",
        "are you a robot",
        "enable javascript",
    )
    return any(s in head for s in señales)


def _html_to_text(html_doc: str) -> str:
    """Convierte HTML crudo en texto legible: quita script/style, sustituye tags por saltos de
    línea/espacios, desescapa entidades y colapsa el exceso de líneas en blanco."""
    html_doc = re.sub(r"(?is)<(script|style|noscript|head)\b.*?</\1>", " ", html_doc)
    html_doc = re.sub(r"(?i)<(br|/p|/div|/li|/h[1-6]|/tr)\s*>", "\n", html_doc)
    text = re.sub(r"(?s)<[^>]+>", "", html_doc)  # quitar el resto de tags
    text = html.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _fetch_via_jina(url: str) -> str:
    headers = {"User-Agent": "ChordFlow/1.0", "Accept": "text/plain"}
    if settings.jina_api_key:  # con key, fiable también desde datacenter (Vercel)
        headers["Authorization"] = f"Bearer {settings.jina_api_key}"
    req = urllib.request.Request(settings.chordflow_reader_url + url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", "replace").strip()


def _fetch_direct(url: str) -> str:
    """Descarga directa de la página y limpieza de HTML a texto (fallback si Jina falla)."""
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=25) as resp:
        raw = resp.read().decode("utf-8", "replace")
    return _html_to_text(raw)


def _fetch_raw_html(url: str, timeout: float = 20.0) -> str:
    """Descarga directa SIN limpiar (para los parsers propios, que necesitan las etiquetas).
    CifraClub y LaCuerda no bloquean esta petición simple (verificado a mano); si algún día
    empiezan a bloquearla, los parsers de abajo devuelven None/[] y se cae al flujo con IA."""
    req = urllib.request.Request(url, headers={"User-Agent": _UA, "Referer": url})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "replace")


def fetch_page_text(url: str) -> str:
    """Obtiene el contenido legible de la página. Primero el lector Jina (texto limpio); si viene
    bloqueado/rate-limited (típico desde IPs de datacenter sin key), cae a descarga directa +
    limpieza de HTML. Trunca a `chordflow_import_max_chars`. Lanza ImportError_ si todo falla."""
    text = ""
    try:
        text = _fetch_via_jina(url)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Lector Jina falló para {url}: {e}")

    if not text or _looks_blocked(text):
        logger.info(f"Jina no usable para {url}; probando descarga directa")
        try:
            direct = _fetch_direct(url)
            if direct and not _looks_blocked(direct):
                text = direct
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Descarga directa falló para {url}: {e}")

    if not text or _looks_blocked(text):
        raise ImportError_(
            "No se pudo leer esa página (puede bloquear bots). "
            "Prueba con CifraClub/LaCuerda o pega el texto manualmente."
        )
    return text[: settings.chordflow_import_max_chars]


def extract_chords(page_text: str) -> str:
    """Pide al modelo (OpenRouter) que extraiga la partitura en el formato del editor.
    Devuelve el texto. Lanza ImportError_ si no hay clave, falla la llamada, o no hay partitura."""
    if not settings.openrouter_api_key:
        raise ImportError_("Falta configurar OPENROUTER_API_KEY en el servidor.")

    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        # Recomendado por OpenRouter para identificar la app (opcionales).
        "HTTP-Referer": "https://chordflow-ecru.vercel.app",
        "X-Title": "ChordFlow",
    }
    payload = {
        "model": settings.openrouter_model,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": page_text},
        ],
        "temperature": 0.1,
    }
    try:
        body = _http_post_json(settings.openrouter_base_url + "/chat/completions", payload, headers)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:200]
        logger.error(f"OpenRouter HTTP {e.code}: {detail}")
        raise ImportError_("El servicio de IA no está disponible ahora mismo. Inténtalo más tarde.")
    except Exception as e:  # noqa: BLE001
        logger.error(f"Error llamando a OpenRouter: {e}")
        raise ImportError_("No se pudo contactar con el servicio de IA.")

    try:
        content = body["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, AttributeError, TypeError):
        logger.error(f"Respuesta inesperada de OpenRouter: {str(body)[:300]}")
        raise ImportError_("La IA devolvió una respuesta inesperada.")

    if not content or content.strip() == "SIN_PARTITURA":
        raise ImportError_("No encontré una partitura de acordes en esa página.")
    return content


# ─── Foto → partitura con IA de visión (T-V5-11, beta) ─────────────────────────
# Mismo formato de salida que el editor, pero la entrada es una FOTO (data URL base64) en vez de
# texto de una web. Usa un modelo de VISIÓN de OpenRouter (gratuito por defecto). Beta: los modelos
# gratis fallan con manuscritos; funciona mejor con hojas impresas/claras.

_VISION_SYSTEM_PROMPT = (
    "Eres un extractor de partituras de acordes. Recibes una FOTOGRAFÍA de una hoja de papel (o "
    "pantalla) con acordes y letra, y devuelves SOLO la canción en este formato de texto plano, sin "
    "explicaciones ni markdown:\n"
    "- Cada sección empieza con su nombre seguido de dos puntos (p. ej. 'Verso:', 'Estribillo:').\n"
    "- La línea de ACORDES va justo encima de su línea de LETRA, con los acordes alineados por "
    "posición sobre la sílaba correspondiente (usa espacios para alinear).\n"
    "- Una línea en blanco entre secciones.\n"
    "- Conserva los acordes tal cual (Am, F#m7, Csus4, G/B...). No inventes acordes ni letra: "
    "transcribe SOLO lo que se ve en la foto; si algo es ilegible, omítelo.\n"
    "Si la foto no contiene una partitura de acordes, responde exactamente: SIN_PARTITURA"
)

# data URL de imagen (data:image/...;base64,...). Acota tipos y evita mandar basura al modelo.
_IMG_DATA_URL_RE = re.compile(
    r"^data:image/(?:png|jpe?g|webp|gif);base64,[A-Za-z0-9+/=\s]+$", re.IGNORECASE
)
_MAX_IMG_CHARS = 12_000_000  # ~9 MB de imagen en base64 (el cliente ya la reduce)


def extract_chords_from_image(image_data_url: str) -> str:
    """Pide a un modelo de VISIÓN (OpenRouter) que transcriba la partitura de una FOTO. Recibe la
    imagen como data URL (`data:image/...;base64,...`, ya redimensionada en el cliente) y devuelve el
    texto en el formato del editor. Lanza ImportError_ si no hay clave, la imagen no es válida, falla
    la llamada o no hay partitura."""
    if not settings.openrouter_api_key:
        raise ImportError_("Falta configurar OPENROUTER_API_KEY en el servidor.")
    image_data_url = (image_data_url or "").strip()
    if not _IMG_DATA_URL_RE.match(image_data_url):
        raise ImportError_("La imagen no es válida. Sube una foto (JPG o PNG).")
    if len(image_data_url) > _MAX_IMG_CHARS:
        raise ImportError_("La imagen es demasiado grande. Prueba con una foto más pequeña.")

    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://chordflow-ecru.vercel.app",
        "X-Title": "ChordFlow",
    }
    payload = {
        "model": settings.openrouter_vision_model,
        "messages": [
            {"role": "system", "content": _VISION_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Transcribe la partitura (acordes y letra) de esta foto.",
                    },
                    {"type": "image_url", "image_url": {"url": image_data_url}},
                ],
            },
        ],
        "temperature": 0.1,
    }
    try:
        body = _http_post_json(
            settings.openrouter_base_url + "/chat/completions", payload, headers, timeout=60.0
        )
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:200]
        logger.error(f"OpenRouter HTTP {e.code} (visión): {detail}")
        raise ImportError_(
            "El servicio de IA de visión no está disponible ahora mismo. " "Inténtalo más tarde."
        )
    except Exception as e:  # noqa: BLE001
        logger.error(f"Error llamando a OpenRouter (visión): {e}")
        raise ImportError_("No se pudo contactar con el servicio de IA.")

    try:
        content = body["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, AttributeError, TypeError):
        logger.error(f"Respuesta inesperada de OpenRouter (visión): {str(body)[:300]}")
        raise ImportError_("La IA devolvió una respuesta inesperada.")

    if not content or content.strip() == "SIN_PARTITURA":
        raise ImportError_(
            "No encontré una partitura de acordes en esa foto. "
            "Prueba con una foto más clara o de una hoja impresa."
        )
    return content


# ─── Parsers propios por sitio, SIN IA (T-163) ─────────────────────────────────
# CifraClub y LaCuerda tienen HTML suficientemente estable (verificado a mano, no es una
# suposición) para sacar resultados de búsqueda y acordes/letra con regex puro — sin gastar una
# llamada a OpenRouter (ni al lector Jina) por cada búsqueda o import. El LLM se queda como red
# de seguridad: entra si el dominio no tiene parser propio, o si el parser no encuentra nada.

_TAG_RE = re.compile(r"<[^>]+>")


def _cc_search_url(query: str) -> str:
    return f"https://www.cifraclub.com/busca/?q={urllib.parse.quote(query)}"


# Ancla en el `alt` de la carátula ("Portada de la canción &quot;X&quot;, de Y") — es un dato
# semántico de accesibilidad, mucho más estable que las clases CSS hasheadas (p. ej. "_crVx",
# que cambian en cada build de su Next.js) que rodean el resultado.
_CC_ALT_RE = re.compile(r'alt="Portada de la canci[oó]n &quot;([^&]*)&quot;, de ([^"]*)"')
_CC_HREF_RE = re.compile(r'href="(/[a-z0-9_-]+/[a-z0-9_-]+/)"')


def _parse_cifraclub_search(page_html: str, query: str) -> list[dict]:
    """La página de resultados de CifraClub mezcla los resultados reales con una barra de
    "tendencias" (mismo marcado `alt`) — se filtra por relevancia: alguna palabra de la
    búsqueda debe aparecer en el título o el artista."""
    words = [w for w in re.split(r"\s+", query.lower()) if len(w) > 1]
    results, seen = [], set()
    for m in _CC_ALT_RE.finditer(page_html):
        title = html.unescape(m.group(1)).strip()
        artist = html.unescape(m.group(2)).strip()
        if not title:
            continue
        haystack = f"{title} {artist}".lower()
        if words and not any(w in haystack for w in words):
            continue
        # El href del resultado envuelve la carátula por fuera: es el más cercano hacia atrás.
        window = page_html[max(0, m.start() - 1200) : m.start()]
        hrefs = _CC_HREF_RE.findall(window)
        if not hrefs:
            continue
        url = "https://www.cifraclub.com" + hrefs[-1]
        if url in seen:
            continue
        seen.add(url)
        results.append({"title": title, "artist": artist, "url": url, "source": "CifraClub"})
    return results


_CC_CHORD_RE = re.compile(r'<b data-chord-name="([^"]*)"[^>]*>[^<]*</b>')
_CC_SECTION_RE = re.compile(r"^\s*\[([^\]]+)\]\s*$")


def _parse_cifraclub_song(page_html: str) -> str | None:
    """Cada línea visual del bloque de acordes viene separada por un salto de línea REAL en el
    HTML de CifraClub (verificado a mano) — se reconstruye línea a línea, sustituyendo cada
    `<b data-chord-name="X">` (atributo semántico, no depende de la clase CSS) por `X`."""
    start = page_html.find('data-chord-name="')
    if start == -1:
        return None
    pre_start = page_html.rfind("<pre", 0, start)
    end = page_html.find("</pre>", start)
    if pre_start == -1 or end == -1:
        return None
    block = page_html[pre_start:end]
    if len(_CC_CHORD_RE.findall(block)) < 2:
        return None  # muy pocos acordes reconocidos: mejor que lo intente la IA

    lines = []
    for raw_line in block.split("\n"):
        line = _CC_CHORD_RE.sub(lambda m: m.group(1), raw_line)
        line = html.unescape(_TAG_RE.sub("", line))
        section = _CC_SECTION_RE.match(line)
        if section:
            line = section.group(1).strip() + ":"
        lines.append(line.rstrip())

    text = "\n".join(lines).strip("\n")
    return re.sub(r"\n{3,}", "\n\n", text)


def _lc_search_url(query: str) -> str:
    # La lista de resultados solo viene servida en el HTML con canc=1 (buscar "en Canciones");
    # la búsqueda "general" (sin canc, o canc=0) devuelve el conteo pero la lista llega vacía
    # (se carga por JS que ni siquiera el lector Jina llega a ejecutar/esperar) — verificado a mano.
    return f"https://acordes.lacuerda.net/busca.php?lang=ES&exp={urllib.parse.quote(query)}&canc=1&ord=0&ini=0"


_LC_HDS_RE = re.compile(r"var hds=\[([^\]]*)\];")
_LC_FNS_RE = re.compile(r"var fns=\[([^\]]*)\];")
_LC_ROW_RE = re.compile(
    r'<a href="(/[a-z0-9_]+/)">([^<]+)</A></TD><td>.*?<li[^>]*><a href="javascript:">([^<]+)</a></li>',
    re.IGNORECASE | re.DOTALL,
)


def _lc_js_array(match: "re.Match | None") -> list[str]:
    if not match:
        return []
    return [s.strip().strip("'") for s in match.group(1).split(",") if s.strip()]


def _parse_lacuerda_search(page_html: str, query: str) -> list[dict]:
    """El nombre real (slug de la URL) de cada canción va en el array `fns` del HTML, pero en
    orden INVERSO al de las filas de la tabla / al array `hds` (verificado con una canción real:
    la fila N empareja con `fns[len(fns)-1-N]`, no con `fns[N]`) — probablemente por cómo su JS
    construye el array. Si las longitudes no cuadran, mejor no arriesgar un enlace equivocado."""
    rows = _LC_ROW_RE.findall(page_html)
    hds = _lc_js_array(_LC_HDS_RE.search(page_html))
    fns = _lc_js_array(_LC_FNS_RE.search(page_html))
    if not rows or len(hds) != len(rows) or len(fns) != len(rows):
        return []

    fns_rev = list(reversed(fns))
    results = []
    for i, (_href, artist, title) in enumerate(rows):
        url = f"https://acordes.lacuerda.net/{hds[i]}/{fns_rev[i]}"
        results.append(
            {
                "title": html.unescape(title).strip(),
                "artist": html.unescape(artist).strip(),
                "url": url,
                "source": "LaCuerda",
            }
        )
    return results


_LC_CHORD_RE = re.compile(r"<A>([^<]*)</A>", re.IGNORECASE)


def _parse_lacuerda_song(page_html: str) -> str | None:
    start = page_html.find("<pre>")
    if start == -1:
        return None
    end = page_html.find("</pre>", start)
    if end == -1:
        return None
    block = page_html[start + len("<pre>") : end]
    if len(_LC_CHORD_RE.findall(block)) < 2:
        return None

    lines = []
    for raw_line in block.split("\n"):
        line = _LC_CHORD_RE.sub(lambda m: m.group(1), raw_line)
        line = html.unescape(_TAG_RE.sub("", line))
        lines.append(line.rstrip())

    text = "\n".join(lines).strip("\n")
    return re.sub(r"\n{3,}", "\n\n", text)


# Registro de adaptadores por dominio. Añadir un sitio nuevo = añadir una entrada aquí.
_SITE_ADAPTERS = {
    "cifraclub.com": {
        "search_url": _cc_search_url,
        "parse_search": _parse_cifraclub_search,
        "parse_song": _parse_cifraclub_song,
    },
    "lacuerda.net": {
        "search_url": _lc_search_url,
        "parse_search": _parse_lacuerda_search,
        "parse_song": _parse_lacuerda_song,
    },
}


def _adapter_for_host(host: str) -> dict | None:
    host = (host or "").lower()
    for domain, adapter in _SITE_ADAPTERS.items():
        if host == domain or host.endswith("." + domain):
            return adapter
    return None


def import_from_url(url: str) -> str:
    """Orquesta la importación. Si el dominio tiene parser propio (sin IA) y consigue extraer la
    partitura, se usa directo (gratis, rápido, no depende de OpenRouter). Si no hay parser para
    ese dominio o no encuentra nada fiable, cae al flujo de siempre (lector + IA)."""
    adapter = _adapter_for_host(urllib.parse.urlparse(url).netloc)
    if adapter:
        try:
            page = _fetch_raw_html(url)
            parsed = adapter["parse_song"](page)
            if parsed:
                return parsed
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Parser propio falló para {url}, cae a IA: {e}")

    page = fetch_page_text(url)
    return extract_chords(page)


# ─── Buscar canción por nombre (T-162) ─────────────────────────────────────────
# En vez de pegar el enlace, el usuario escribe el nombre de la canción: primero se prueban los
# parsers propios de arriba (sin red Jina, sin LLM); si ninguno da resultados (sitio caído,
# estructura cambiada...) se cae al flujo con IA como red de seguridad.

_SEARCH_SITES = (
    ("CifraClub", "https://www.cifraclub.com/busca/?q={q}"),
    ("LaCuerda", "https://acordes.lacuerda.net/busca.php?lang=ES&exp={q}&canc=1&ord=0&ini=0"),
)

_SEARCH_SYSTEM_PROMPT = (
    "Eres un asistente que extrae resultados de canciones a partir del texto de una página de "
    "búsqueda de un sitio de acordes (CifraClub o LaCuerda). Te doy el nombre buscado y el texto "
    "de la página, con sus enlaces en formato markdown [texto](url). Devuelve SOLO un array JSON "
    "(sin markdown ni explicaciones), con como máximo 8 objetos "
    '{"title": str, "artist": str, "url": str} correspondientes a canciones reales de esa página '
    "que coincidan razonablemente con la búsqueda, ordenados por relevancia. La url debe ser "
    "EXACTAMENTE una de las que aparecen en el texto (absoluta, empieza por http). Si un dato no "
    "está claro, usa cadena vacía. Si no hay ningún resultado de canción, devuelve []."
)


def _guess_source(url: str) -> str:
    host = urllib.parse.urlparse(url).netloc.lower()
    if "cifraclub" in host:
        return "CifraClub"
    if "lacuerda" in host:
        return "LaCuerda"
    return host or "web"


def _extract_json_array(text: str) -> list:
    """El modelo a veces envuelve el JSON en ```json ... ``` pese a que se le pide que no lo haga."""
    text = text.strip()
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        return []
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def _rank_search_results(query: str, page_text: str) -> list[dict]:
    """Pide al modelo (OpenRouter) que estructure los resultados de una página de búsqueda."""
    if not settings.openrouter_api_key:
        raise ImportError_("Falta configurar OPENROUTER_API_KEY en el servidor.")

    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://chordflow-ecru.vercel.app",
        "X-Title": "ChordFlow",
    }
    payload = {
        "model": settings.openrouter_model,
        "messages": [
            {"role": "system", "content": _SEARCH_SYSTEM_PROMPT},
            {"role": "user", "content": f'Búsqueda: "{query}"\n\n{page_text}'},
        ],
        "temperature": 0.1,
    }
    try:
        body = _http_post_json(settings.openrouter_base_url + "/chat/completions", payload, headers)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:200]
        logger.error(f"OpenRouter HTTP {e.code} (búsqueda): {detail}")
        raise ImportError_("El servicio de IA no está disponible ahora mismo. Inténtalo más tarde.")
    except Exception as e:  # noqa: BLE001
        logger.error(f"Error llamando a OpenRouter (búsqueda): {e}")
        raise ImportError_("No se pudo contactar con el servicio de IA.")

    try:
        content = body["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, AttributeError, TypeError):
        logger.error(f"Respuesta inesperada de OpenRouter (búsqueda): {str(body)[:300]}")
        raise ImportError_("La IA devolvió una respuesta inesperada.")

    results = []
    for item in _extract_json_array(content):
        if not isinstance(item, dict):
            continue
        url = str(item.get("url") or "").strip()
        title = str(item.get("title") or "").strip()
        if not url or not title:
            continue
        results.append(
            {
                "title": title,
                "artist": str(item.get("artist") or "").strip(),
                "url": url,
                "source": _guess_source(url),
            }
        )
    return results


def _search_song_via_llm(query: str) -> list[dict]:
    """Red de seguridad: lee las páginas de búsqueda con el lector Jina (renderiza JS) y pide al
    modelo que estructure los resultados. Más lento y con coste de IA — solo se usa si los
    parsers propios (sin IA, arriba) no dieron ningún resultado."""
    fetched = []
    for source, url_tpl in _SEARCH_SITES:
        url = url_tpl.format(q=urllib.parse.quote(query))
        try:
            text = _fetch_via_jina(url)
            if text and not _looks_blocked(text):
                fetched.append((source, text[: settings.chordflow_import_max_chars]))
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Búsqueda con IA en {source} falló para «{query}»: {e}")

    if not fetched:
        raise ImportError_(
            "No se pudo buscar en CifraClub/LaCuerda ahora mismo. "
            "Prueba a pegar el enlace directamente."
        )

    combined = "\n\n".join(f"=== Resultados de {source} ===\n{text}" for source, text in fetched)
    return _rank_search_results(query, combined)


def search_song(query: str) -> list[dict]:
    """Busca una canción por nombre en los sitios soportados (CifraClub/LaCuerda) y devuelve una
    lista de candidatos (título/artista/url/origen) para que el usuario elija antes de importar.
    Primero prueba los parsers propios (T-163, sin red Jina ni LLM); si ninguno da resultados
    (sitio caído, estructura cambiada...) cae al flujo con IA como red de seguridad."""
    query = (query or "").strip()
    if not query:
        return []

    results = []
    for domain, adapter in _SITE_ADAPTERS.items():
        try:
            page = _fetch_raw_html(adapter["search_url"](query))
            results.extend(adapter["parse_search"](page, query))
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Búsqueda sin IA en {domain} falló para «{query}»: {e}")

    if results:
        return results[:8]

    return _search_song_via_llm(query)[:8]
