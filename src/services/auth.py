import logging
import threading
import time

from fastapi import Header, HTTPException

from .auth_provider import build_auth_provider
from .config import settings

logger = logging.getLogger(__name__)

SUPABASE_URL = settings.supabase_url
SUPABASE_ANON_KEY = settings.supabase_anon_key

# Proveedor de identidad enchufable (T-043). El núcleo de esta caché es agnóstico a él.
_provider = build_auth_provider(settings)

# Modo test: SOLO para tests automatizados / CI. Si está activo, se salta la
# validación con Supabase y se usa un usuario de prueba fijo. NUNCA en producción.
TEST_MODE = settings.chordflow_test_mode
TEST_USER_ID = "test-user-0000-0000-0000-000000000000"

# Caché de validación de token: evita llamar a Supabase en cada request (latencia)
# y permite que la app siga funcionando si Supabase está temporalmente caído (T-005).
# token -> (user_id, expires_at_monotonic)
TOKEN_TTL_SECONDS = settings.chordflow_token_ttl
# Cota dura para que la caché no crezca sin límite (memory leak ante muchos tokens).
TOKEN_CACHE_MAX = settings.chordflow_token_cache_max
# Ventana de gracia tras expirar (T-031): acota cuánto puede sobrevivir una entrada caducada
# cuando la validación remota falla. Limita la exposición de un token revocado a TTL + gracia.
TOKEN_GRACE_SECONDS = settings.chordflow_token_grace
_token_cache: dict[str, tuple[str, float]] = {}
# uvicorn ejecuta los endpoints sync en un threadpool → varios hilos tocan la caché a la
# vez. Sin lock, iterar el dict mientras otro hilo inserta lanza "dictionary changed size
# during iteration" (HTTP 500 a usuarios válidos) y la cota se salta por TOCTOU. Ver T-028.
_cache_lock = threading.Lock()


def _cache_set(token: str, user_id: str, now: float):
    """Guarda en la caché de forma atómica (lock): purga los expirados y, si sigue
    llena, la vacía (cota de memoria). El lock evita el RuntimeError de iteración
    concurrente y respeta TOKEN_CACHE_MAX bajo concurrencia."""
    with _cache_lock:
        if len(_token_cache) >= TOKEN_CACHE_MAX:
            for t in [t for t, (_, exp) in _token_cache.items() if exp <= now]:
                _token_cache.pop(t, None)
            if len(_token_cache) >= TOKEN_CACHE_MAX:
                _token_cache.clear()
        _token_cache[token] = (user_id, now + TOKEN_TTL_SECONDS)


def _validate_token(token: str):
    """Valida el token contra el proveedor de identidad configurado (T-043) y devuelve el
    dict del usuario (con `id`) o None. Punto de extensión y seam de test: el resto de
    `auth.py` (caché, TTL, lock, degradación) no sabe qué proveedor hay detrás."""
    return _provider.validate(token)


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
    user = _validate_token(token)
    if user and user.get("id"):
        _cache_set(token, user["id"], now)
        return user["id"]

    # 3) Falló la validación remota. Degradación elegante ACOTADA (T-031): solo aceptamos una
    #    entrada caducada dentro de la ventana de gracia (TTL ya expirado + TOKEN_GRACE_SECONDS).
    #    Pasada esa ventana, un token revocado deja de colarse → 401, y purgamos la entrada vieja.
    if cached and now < cached[1] + TOKEN_GRACE_SECONDS:
        logger.warning("Validación remota falló; usando caché en ventana de gracia (Supabase caído?)")
        return cached[0]

    if cached:
        _token_cache.pop(token, None)  # fuera de la gracia: no volver a honrarla
    raise HTTPException(status_code=401, detail="Token inválido o expirado")
