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

import json
import logging
import urllib.error
import urllib.parse
import urllib.request

from .config import settings

logger = logging.getLogger(__name__)


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


def fetch_page_text(url: str) -> str:
    """Descarga el contenido legible de la página vía el lector (Jina). Devuelve texto plano,
    truncado a `chordflow_import_max_chars` para acotar tokens. Lanza ImportError_ si falla."""
    reader = settings.chordflow_reader_url + url
    try:
        req = urllib.request.Request(reader, headers={"User-Agent": "ChordFlow/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            text = resp.read().decode("utf-8", "replace")
    except Exception as e:  # noqa: BLE001
        logger.warning(f"No se pudo leer la página {url}: {e}")
        raise ImportError_("No se pudo leer esa página. Prueba con otro enlace o pega el texto.")
    text = text.strip()
    if not text:
        raise ImportError_("La página no devolvió contenido legible.")
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
