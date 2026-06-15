"""Configuración central validada de ChordFlow (T-016).

Un único objeto `Settings` (pydantic-settings) reemplaza los `os.getenv` dispersos por
`db.py` / `auth.py` / `main.py` / `logging_config.py`: tipos, defaults y validación en un
solo sitio, leídos UNA vez al arrancar. Importar el singleton `settings`.

`load_dotenv()` se mantiene aquí (además del `env_file` de pydantic) para poblar también
`os.environ`, del que dependen lectores externos al objeto Settings —p. ej. `alembic/env.py`,
que lee `DATABASE_URL` fresco en cada invocación de migración.
"""

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Poblar os.environ desde .env y .env.local (este último tiene prioridad: credenciales).
load_dotenv()
load_dotenv(".env.local")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        extra="ignore",
        case_sensitive=False,
    )

    # ── Base de datos ───────────────────────────────────────────────────────
    database_url: str = "sqlite:///./chordflow.db"

    # ── Auth ────────────────────────────────────────────────────────────────
    # Proveedor de identidad enchufable (T-043). "supabase" hoy; el molde puede añadir otros.
    chordflow_auth_provider: str = "supabase"
    # Supabase: la anon key es pública por diseño; la service_role NUNCA va aquí ni al front.
    supabase_url: str | None = None
    supabase_anon_key: str | None = None

    # ── Modo test ───────────────────────────────────────────────────────────
    # Solo CI/local: salta Supabase y usa un usuario fijo. JAMÁS en producción (CLAUDE.md §5).
    chordflow_test_mode: bool = False

    # ── Caché de validación de token (T-005 / T-028) ────────────────────────
    chordflow_token_ttl: int = 60
    chordflow_token_cache_max: int = 1000
    # Ventana de gracia (T-031): segundos TRAS expirar el TTL en que una entrada caducada se
    # sigue aceptando si la validación remota falla (Supabase caído). Acota cuánto puede pasar
    # un token revocado: como mucho TTL + gracia. 0 = sin gracia (rechaza en cuanto expira).
    chordflow_token_grace: int = 300

    # ── CORS (T-004): orígenes permitidos, coma-separados ───────────────────
    chordflow_allowed_origins: str = "http://127.0.0.1:8000,http://localhost:8000"

    # ── Logging (T-014) ─────────────────────────────────────────────────────
    log_level: str = "INFO"
    chordflow_log_stdout: bool = False

    # ── Importar desde URL con IA (T-045) ───────────────────────────────────
    # Proveedor: OpenRouter (compatible OpenAI). Clave gratuita en openrouter.ai → Keys.
    # El modelo es configurable porque qué modelos son gratis cambia con el tiempo; por
    # defecto uno gratuito (sufijo ":free"). La página se obtiene vía el lector Jina.
    openrouter_api_key: str | None = None
    # Modelo gratuito por defecto (verificado funcionando). Si deja de estar gratis/disponible,
    # cambiar por env var OPENROUTER_MODEL a otro `:free` (ver openrouter.ai/models).
    openrouter_model: str = "openai/gpt-oss-120b:free"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    # Lector que renderiza JS/sortea anti-bot y devuelve texto limpio (prefijo de URL).
    chordflow_reader_url: str = "https://r.jina.ai/"
    # Tope de caracteres de la página enviados a la IA (acota tokens/coste/latencia).
    chordflow_import_max_chars: int = 12000

    @property
    def allowed_origins_list(self) -> list[str]:
        """`chordflow_allowed_origins` partido en lista, sin vacíos."""
        return [o.strip() for o in self.chordflow_allowed_origins.split(",") if o.strip()]


# Singleton: se instancia una vez al importar este módulo (tras cargar el .env).
settings = Settings()
