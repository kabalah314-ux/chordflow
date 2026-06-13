from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from .api.songs_router import router as songs_router
from .services.auth import SUPABASE_ANON_KEY, SUPABASE_URL, TEST_MODE
from .services.config import settings
from .services.db import Base, engine
from .services.logging_config import setup_logging

# Logging configurado UNA sola vez para toda la app (T-014). Los módulos de librería
# solo usan getLogger; aquí decidimos el destino (fichero o stdout cloud-friendly).
setup_logging()

# Inicializar Base de Datos
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ChordFlow API",
    description="Backend API para la aplicación ChordFlow (Partituras y Acordes)",
    version="1.0.0"
)

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

# Montar carpeta de archivos estáticos (Frontend)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Incluir routers
app.include_router(songs_router)

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
