import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from .api.import_router import router as import_router
from .api.setlists_router import router as setlists_router
from .api.songs_router import router as songs_router
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
try:
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
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response

# Montar carpeta de archivos estáticos (Frontend). Ruta ABSOLUTA (relativa a la raíz del repo,
# = padre de src/) para que funcione tanto en local como en serverless (Vercel), donde el CWD
# no es la raíz del proyecto.
_STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

# Incluir routers
app.include_router(songs_router)
app.include_router(import_router)
app.include_router(setlists_router)

@app.get("/")
def read_root():
    # La biblioteca es la pantalla de entrada de la app
    return RedirectResponse(url="/static/library.html")


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
