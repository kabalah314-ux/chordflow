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


def test_upgrade_crea_el_nucleo_de_banda(tmp_path, monkeypatch):
    """T-048 (giro V2): la migración aditiva crea las 4 tablas de identidad de banda
    con sus índices y el único (band_id, user_id). No toca lo existente."""
    db = tmp_path / "mig_banda.db"
    url = f"sqlite:///{db.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", url)

    command.upgrade(_alembic_config(url), "head")

    insp = inspect(create_engine(url))
    tablas = set(insp.get_table_names())
    nucleo_banda = {"musician_profiles", "bands", "band_memberships", "band_invites"}
    assert nucleo_banda.issubset(tablas), f"faltan tablas: {nucleo_banda - tablas}"
    # Las tablas existentes siguen ahí (aditivo, no destructivo).
    assert TABLAS_ESPERADAS.issubset(tablas)

    # Índices band_id (aislamiento/rendimiento, §C.4.3).
    idx_membership = {ix["name"] for ix in insp.get_indexes("band_memberships")}
    assert {"ix_band_memberships_band_id", "ix_band_memberships_user_id"}.issubset(idx_membership)
    assert "ix_band_invites_band_id" in {ix["name"] for ix in insp.get_indexes("band_invites")}

    # Único (band_id, user_id) en la pertenencia.
    uniques = {uc["name"] for uc in insp.get_unique_constraints("band_memberships")}
    assert "uq_membership_band_user" in uniques


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
