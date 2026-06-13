"""
Tests de las migraciones Alembic (T-011).

Verifican que:
- `alembic upgrade head` construye el esquema completo (las 5 tablas + alembic_version)
  partiendo de una BD vacía y temporal.
- Las migraciones están EN SINCRONÍA con los modelos: `alembic check` no detecta
  cambios pendientes (si alguien añade/cambia una columna sin migración, esto falla).
"""

from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from alembic import command

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parent.parent.parent
TABLAS_ESPERADAS = {"songs", "sections", "lines", "chord_markers", "tab_lines"}


def _alembic_config(url: str) -> Config:
    """Config de Alembic apuntando a una BD concreta (env.py lee DATABASE_URL)."""
    cfg = Config(str(ROOT / "alembic.ini"))
    # Rutas absolutas para no depender del CWD al correr los tests.
    cfg.set_main_option("script_location", str(ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg


def test_upgrade_head_crea_el_esquema(tmp_path, monkeypatch):
    db = tmp_path / "mig.db"
    url = f"sqlite:///{db.as_posix()}"
    # env.py toma la URL de DATABASE_URL.
    monkeypatch.setenv("DATABASE_URL", url)

    command.upgrade(_alembic_config(url), "head")

    insp = inspect(create_engine(url))
    tablas = set(insp.get_table_names())
    assert TABLAS_ESPERADAS.issubset(tablas), f"faltan tablas: {TABLAS_ESPERADAS - tablas}"
    assert "alembic_version" in tablas  # la migración quedó registrada (stamp de versión)
    # Los índices de T-012 también deben existir (p. ej. owner_id y deleted_at en songs).
    indices_songs = {ix["name"] for ix in insp.get_indexes("songs")}
    assert {"ix_songs_owner_id", "ix_songs_deleted_at"}.issubset(indices_songs)


def test_migraciones_en_sync_con_los_modelos(tmp_path, monkeypatch):
    """Tras migrar, autogenerate no debe detectar diferencias contra los modelos.
    Guarda contra el drift esquema↔modelos (olvidar una migración)."""
    db = tmp_path / "mig_check.db"
    url = f"sqlite:///{db.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", url)

    cfg = _alembic_config(url)
    command.upgrade(cfg, "head")
    # command.check lanza si hay operaciones de upgrade pendientes (drift).
    command.check(cfg)
