"""Configuración centralizada del logging de ChordFlow (T-014).

Regla: los módulos de librería (`db.py`, `auth.py`, ...) NUNCA llaman a `basicConfig`
ni montan handlers; solo hacen `logging.getLogger(__name__)`. Quién decide a dónde van
los logs es la APP, **una sola vez** al arrancar, vía `setup_logging()`.

Por defecto escribe a `logs/app.log`. En entornos cloud (contenedores, Fly, Heroku...)
conviene log a stdout para que la plataforma lo capture: activar con
`CHORDFLOW_LOG_STDOUT=1`.
"""

import logging
import os
import sys

from .config import settings

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def setup_logging() -> None:
    """Configura el logger raíz UNA sola vez. Idempotente: si se vuelve a llamar
    (p. ej. en tests), reemplaza los handlers en vez de duplicar líneas de log."""
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    formatter = logging.Formatter(LOG_FORMAT)
    if settings.chordflow_log_stdout:
        handler: logging.Handler = logging.StreamHandler(sys.stdout)
    else:
        os.makedirs("logs", exist_ok=True)
        handler = logging.FileHandler("logs/app.log", encoding="utf-8")
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)
    # Idempotencia: cerrar y soltar los handlers previos para no duplicar líneas
    # ni dejar ficheros de log abiertos si se reconfigura.
    for h in list(root.handlers):
        root.removeHandler(h)
        try:
            h.close()
        except Exception:
            pass
    root.addHandler(handler)
