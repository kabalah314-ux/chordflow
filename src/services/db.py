import logging

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import settings

# El logging lo configura la app una sola vez (ver services/logging_config.py, T-014).
# Aquí, como módulo de librería, solo obtenemos un logger con nombre: sin basicConfig.
logger = logging.getLogger(__name__)

DATABASE_URL = settings.database_url

# Si se usa SQLite, se requieren argumentos adicionales para evitar errores en hilos múltiples
_is_sqlite = DATABASE_URL.startswith("sqlite")
engine_args = {"check_same_thread": False} if _is_sqlite else {}

# En Postgres gestionado (Supabase) / detrás de un pooler, `pool_pre_ping` descarta conexiones
# muertas antes de usarlas (evita errores tras cierres del pooler o reinicios). En SQLite no aplica.
engine_kwargs = {"connect_args": engine_args}
if not _is_sqlite:
    engine_kwargs["pool_pre_ping"] = True

engine = create_engine(DATABASE_URL, **engine_kwargs)

# SQLite no fuerza las foreign keys por defecto: hay que activarlo por conexión.
# Defensa en profundidad contra filas huérfanas (ver T-003).
if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _enable_sqlite_fk(dbapi_conn, _record):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Error en sesión de base de datos: {e}", exc_info=True)
        raise
    finally:
        db.close()
