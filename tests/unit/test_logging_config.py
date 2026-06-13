"""Tests de la configuración centralizada de logging (T-014, ajustado en T-016).

Verifican que:
- `setup_logging()` con `settings.chordflow_log_stdout` manda los logs a stdout
  (cloud-friendly), sin abrir el fichero `logs/app.log`.
- Por defecto escribe a un `FileHandler`.
- Es idempotente: llamarla varias veces no duplica handlers (ni líneas de log).
- `db.py` (módulo de librería) NO configura el logging raíz por su cuenta (sin basicConfig).

Nota (T-016): el destino se lee del singleton `settings` (poblado del entorno al arrancar,
una sola vez), así que aquí se hace monkeypatch sobre `settings`, no sobre `os.environ`.
"""

import logging
import sys
from pathlib import Path

import pytest

from src.services.config import settings
from src.services.logging_config import setup_logging

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _restore_root_logging():
    """Salva y restaura el logger raíz: estos tests manipulan sus handlers."""
    root = logging.getLogger()
    saved_handlers = list(root.handlers)
    saved_level = root.level
    yield
    for h in list(root.handlers):
        if h not in saved_handlers:
            try:
                h.close()
            except Exception:
                pass
        root.removeHandler(h)
    for h in saved_handlers:
        root.addHandler(h)
    root.setLevel(saved_level)


def test_stdout_cuando_la_var_esta_activa(monkeypatch):
    monkeypatch.setattr(settings, "chordflow_log_stdout", True)
    setup_logging()
    handlers = logging.getLogger().handlers
    assert any(
        isinstance(h, logging.StreamHandler) and getattr(h, "stream", None) is sys.stdout
        for h in handlers
    )
    # No debe haber abierto un fichero de log (FileHandler es subclase de StreamHandler).
    assert not any(isinstance(h, logging.FileHandler) for h in handlers)


def test_fichero_por_defecto(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "chordflow_log_stdout", False)
    monkeypatch.chdir(tmp_path)  # logs/app.log se crea relativo al CWD
    setup_logging()
    handlers = logging.getLogger().handlers
    assert any(isinstance(h, logging.FileHandler) for h in handlers)
    assert (tmp_path / "logs" / "app.log").exists()


def test_es_idempotente(monkeypatch):
    monkeypatch.setattr(settings, "chordflow_log_stdout", True)
    setup_logging()
    setup_logging()
    setup_logging()
    # Una sola llamada deja exactamente un handler; repetir no lo duplica.
    assert len(logging.getLogger().handlers) == 1


def test_db_no_llama_a_basicConfig():
    """db.py es librería: no debe configurar el logging raíz (basicConfig)."""
    import src.services.db as db

    src = Path(db.__file__).read_text(encoding="utf-8")
    assert "basicConfig(" not in src
