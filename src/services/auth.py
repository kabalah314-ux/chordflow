import os
import json
import logging
import urllib.request
from fastapi import Header, HTTPException
from dotenv import load_dotenv

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
    user = _validate_token_with_supabase(token)
    if not user or not user.get("id"):
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    return user["id"]
