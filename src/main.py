import logging
import uuid
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from .api.account_router import router as account_router
from .api.band_collections_router import router as band_collections_router
from .api.band_setlists_router import router as band_setlists_router
from .api.band_songs_router import router as band_songs_router
from .api.band_tools_router import router as band_tools_router
from .api.bands_router import router as bands_router
from .api.catalog_router import router as catalog_router
from .api.collections_router import router as collections_router
from .api.events_router import router as events_router
from .api.finance_router import router as finance_router
from .api.import_router import router as import_router
from .api.invites_router import router as invites_router
from .api.me_router import router as me_router
from .api.messages_router import router as messages_router
from .api.network_router import router as network_router
from .api.notifications_router import router as notifications_router
from .api.profile_router import router as profile_router
from .api.public_router import router as public_router
from .api.search_router import router as search_router
from .api.setlists_router import router as setlists_router
from .api.songs_router import router as songs_router
from .api.tours_router import router as tours_router
from .api.venues_router import router as venues_router
from .services.auth import SUPABASE_ANON_KEY, SUPABASE_URL, TEST_MODE
from .services.config import settings
from .services.db import Base, engine
from .services.logging_config import setup_logging

# Logging configurado UNA sola vez para toda la app (T-014). Los módulos de librería
# solo usan getLogger; aquí decidimos el destino (fichero o stdout cloud-friendly).
setup_logging()
logger = logging.getLogger(__name__)

# Inicializar el esquema (idempotente: solo crea lo que falte). En serverless el esquema ya
# existe (creado/migrado aparte), así que envolvemos en try/except: un parpadeo de la BD al
# importar NO debe tumbar toda la función; los errores reales se verán por petición.
# T-V6-13 (B-12): solo en SQLite (local/tests). En Postgres el esquema lo gestionan las migraciones
# de Alembic: create_all en cada arranque en frío reflejaba ~26 tablas y podía crear tablas fuera
# de la cadena de migraciones (drift silencioso).
try:
    if settings.database_url.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)
except Exception as e:  # noqa: BLE001
    logger.warning(f"create_all al arrancar no se pudo completar (¿BD no disponible?): {e}")

app = FastAPI(
    title="ChordFlow API",
    description="Backend API para la aplicación ChordFlow (Partituras y Acordes)",
    version="1.0.0"
)


# Handler de errores global (T-044): backstop de defensa en profundidad. Si una excepción
# inesperada escapa de un endpoint (o salta en una dependencia/middleware, fuera de los
# try/except de los routers), la registramos con traza y respondemos un 500 GENÉRICO —
# nunca `str(e)` al cliente, para no filtrar internals (misma política que T-027).
# Las HTTPException (404/401/422/...) NO pasan por aquí: las maneja FastAPI con su código.
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(
        f"Excepción no controlada en {request.method} {request.url.path}: {exc}",
        exc_info=True,
    )
    return JSONResponse(status_code=500, content={"detail": "Error interno del servidor"})


# CORS: lista explícita de orígenes vía env (coma-separada). Default seguro a localhost.
# El frontend se sirve desde el mismo origen que la API, así que esto no afecta al uso normal;
# protege frente a sitios de terceros que intenten usar la sesión del usuario (ver T-004).
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cabeceras de seguridad en todas las respuestas (T-029). Conjunto conservador que no
# rompe la app (CSP queda pendiente: requiere afinar 'unsafe-inline' por los estilos inline).
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # Micrófono permitido SOLO a este origen: el afinador y la grabadora de ensayo lo necesitan
    # (antes `microphone=()` lo bloqueaba también para la propia app → afinador mudo).
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(self), camera=(self)"
    response.headers["X-Request-ID"] = getattr(request.state, "request_id", "-")
    return response


# T-V6-24: caché del navegador/CDN. Los estáticos versionados (`?v=<hash>`, ver cachebust.py) no
# cambian nunca → un año e `immutable`; el HTML siempre se revalida (así un deploy se ve al instante).
@app.middleware("http")
async def static_cache_mw(request, call_next):
    response = await call_next(request)
    path = request.url.path
    if path.startswith("/static/") and response.status_code == 200:
        if request.query_params.get("v") and not path.endswith(".html"):
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        elif path.endswith(".html") or path.endswith("sw.js") or path.endswith("manifest.json"):
            response.headers["Cache-Control"] = "no-cache"
    return response


# T-V6-29: id de petición para cruzar un error del usuario con el log (cabecera X-Request-ID).
@app.middleware("http")
async def request_id_mw(request, call_next):
    rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:16]
    request.state.request_id = rid[:64]
    return await call_next(request)

# Montar carpeta de archivos estáticos (Frontend). Ruta ABSOLUTA (relativa a la raíz del repo,
# = padre de src/) para que funcione tanto en local como en serverless (Vercel), donde el CWD
# no es la raíz del proyecto.
_STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

# Incluir routers
app.include_router(songs_router)
app.include_router(import_router)
app.include_router(setlists_router)
app.include_router(collections_router)
app.include_router(bands_router)
app.include_router(invites_router)
app.include_router(profile_router)
app.include_router(band_songs_router)
app.include_router(band_setlists_router)
app.include_router(band_collections_router)
app.include_router(events_router)
app.include_router(venues_router)
app.include_router(finance_router)
app.include_router(messages_router)
app.include_router(me_router)
app.include_router(tours_router)
app.include_router(catalog_router)
app.include_router(public_router)
app.include_router(band_tools_router)
app.include_router(network_router)
app.include_router(notifications_router)
app.include_router(search_router)
app.include_router(account_router)

@app.get("/")
def read_root():
    # T-V6-68: portada pública (bienvenida.html). Si ya hay sesión, ella misma salta a la app.
    return RedirectResponse(url="/static/bienvenida.html")


# T-V6-68: 404 con marca para quien navega (HTML); la API sigue devolviendo JSON.
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    wants_html = "text/html" in (request.headers.get("accept") or "")
    if exc.status_code == 404 and wants_html and request.method == "GET":
        page = _STATIC_DIR / "404.html"
        if page.exists():
            return HTMLResponse(page.read_text(encoding="utf-8"), status_code=404)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail},
                        headers=getattr(exc, "headers", None))


@app.get("/health")
def health():
    """Liveness check (T-025): '¿el proceso está vivo y sirviendo?'. Barato y sin
    dependencias (no toca la BD ni Supabase) para que orquestadores/uptime checks lo
    consulten a alta frecuencia sin coste. Separado de `/config`, que expone config
    pública del frontend y no es un health check."""
    return {"status": "ok"}


@app.get("/config")
def get_config():
    """Config pública para el frontend (la anon key es pública por diseño).
    NUNCA exponer aquí la service_role key."""
    return {
        "supabase_url": SUPABASE_URL,
        "supabase_anon_key": SUPABASE_ANON_KEY,
        "test_mode": TEST_MODE,
    }
