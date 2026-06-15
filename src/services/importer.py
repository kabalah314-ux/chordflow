"""Importar una partitura desde una URL con ayuda de IA (T-045).

Flujo: descargar el contenido de la página con un lector que renderiza JS y sortea anti-bot
(Jina Reader), y pedir a un modelo (OpenRouter, compatible OpenAI, modelo gratuito) que
devuelva SOLO la partitura en el formato de texto que entiende el editor (`parseRawText`):

    Sección:
    Am        C        G
    Letra de la canción alineada bajo sus acordes

    (línea en blanco entre secciones)

No usa SDKs externos: ambas llamadas (lector + OpenRouter) van por urllib (stdlib), igual que
`auth_provider.py`. La clave de OpenRouter es gratuita y va en `.env.local` (nunca al frontend).
"""

import html
import json
import logging
import re
import urllib.error
import urllib.request

from .config import settings

logger = logging.getLogger(__name__)

_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/124 Safari/537.36")


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
    señales = ("just a moment", "error 403", "error 404", "error 429", "forbidden",
               "rate limit", "captcha", "are you a robot", "enable javascript")
    return any(s in head for s in señales)


def _html_to_text(html_doc: str) -> str:
    """Convierte HTML crudo en texto legible: quita script/style, sustituye tags por saltos de
    línea/espacios, desescapa entidades y colapsa el exceso de líneas en blanco."""
    html_doc = re.sub(r"(?is)<(script|style|noscript|head)\b.*?</\1>", " ", html_doc)
    html_doc = re.sub(r"(?i)<(br|/p|/div|/li|/h[1-6]|/tr)\s*>", "\n", html_doc)
    text = re.sub(r"(?s)<[^>]+>", "", html_doc)        # quitar el resto de tags
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
        raise ImportError_("No se pudo leer esa página (puede bloquear bots). "
                           "Prueba con CifraClub/LaCuerda o pega el texto manualmente.")
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


def import_from_url(url: str) -> str:
    """Orquesta: descargar la página y extraer la partitura. Devuelve el texto para el editor."""
    page = fetch_page_text(url)
    return extract_chords(page)
