import json
import logging
import os
import time
import urllib.request

from dotenv import load_dotenv
from fastapi import Header, HTTPException

# Cargar también .env.local (donde están las credenciales de Supabase)
load_dotenv()
load_dotenv(".env.local")

logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

# Modo test: SOLO para tests automatizados / CI. Si está activo, se salta la
# validación con Supabase y se usa un usuario de prueba fijo. NUNCA en producción.
TEST_MODE = os.getenv("CHORDFLOW_TEST_MODE") == "1"
TEST_USER_ID = "test-user-0000-0000-0000-000000000000"

# Caché de validación de token: evita llamar a Supabase en cada request (latencia)
# y permite que la app siga funcionando si Supabase está temporalmente caído (T-005).
# token -> (user_id, expires_at_monotonic)
TOKEN_TTL_SECONDS = int(os.getenv("CHORDFLOW_TOKEN_TTL", "60"))
# Cota dura para que la caché no crezca sin límite (memory leak ante muchos tokens).
TOKEN_CACHE_MAX = int(os.getenv("CHORDFLOW_TOKEN_CACHE_MAX", "1000"))
_token_cache: dict[str, tuple[str, float]] = {}


def _cache_set(token: str, user_id: str, now: float):
    """Guarda en la caché aplicando una cota de tamaño: primero purga los
    expirados; si sigue llena, la vacía (límite de memoria)."""
    if len(_token_cache) >= TOKEN_CACHE_MAX:
        for t in [t for t, (_, exp) in _token_cache.items() if exp <= now]:
            _token_cache.pop(t, None)
        if len(_token_cache) >= TOKEN_CACHE_MAX:
            _token_cache.clear()
    _token_cache[token] = (user_id, now + TOKEN_TTL_SECONDS)


def _validate_token_with_supabase(token: str):
    """Pregunta a Supabase '¿de quién es este token?'. Devuelve el dict del usuario
    o None si el token no es válido. No requiere el JWT secret: usa el endpoint
    /auth/v1/user con la anon key, validado por el propio Supabase."""
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        logger.error("Faltan SUPABASE_URL o SUPABASE_ANON_KEY en el entorno")
        return None
    try:
        req = urllib.request.Request(
            f"{SUPABASE_URL}/auth/v1/user",
            headers={
                "apikey": SUPABASE_ANON_KEY,
                "Authorization": f"Bearer {token}",
            },
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                return json.loads(resp.read())
    except Exception as e:
        logger.warning(f"Token inválido o error validando con Supabase: {e}")
    return None


def get_current_user(authorization: str = Header(None)) -> str:
    """Dependencia FastAPI: exige un Bearer token válido y devuelve el user_id.
    Lanza 401 si no hay token o no es válido."""
    # Atajo de tests: usuario fijo, sin tocar Supabase.
    if TEST_MODE:
        return TEST_USER_ID

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="No autenticado")

    token = authorization.split(" ", 1)[1].strip()

    # 1) Caché válida → no llamamos a Supabase (rápido y resistente a caídas).
    now = time.monotonic()
    cached = _token_cache.get(token)
    if cached and cached[1] > now:
        return cached[0]

    # 2) Validación remota; si va bien, cacheamos con TTL.
    user = _validate_token_with_supabase(token)
    if user and user.get("id"):
        _cache_set(token, user["id"], now)
        return user["id"]

    # 3) Falló la validación remota: si teníamos una entrada (aunque caducada),
    #    la usamos como degradación elegante mientras Supabase se recupera.
    if cached:
        logger.warning("Validación remota falló; usando caché previa del token (Supabase caído?)")
        return cached[0]

    raise HTTPException(status_code=401, detail="Token inválido o expirado")
