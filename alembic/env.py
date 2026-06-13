"""Entorno de migraciones de Alembic para ChordFlow (T-011).

Claves:
- La URL sale de DATABASE_URL (misma fuente y default que `src/services/db.py`),
  así las migraciones apuntan a la MISMA base que la app, y los tests pueden usar
  una BD temporal solo cambiando esa variable.
- `target_metadata = Base.metadata` (importando los modelos) → `--autogenerate`.
- `render_as_batch=True`: SQLite no soporta la mayoría de `ALTER TABLE`; el modo
  batch recrea la tabla por debajo. Imprescindible para futuras migraciones de
  integridad (ON DELETE CASCADE, NOT NULL, server_default → T-033/34/36).
"""

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool

from alembic import context

# Hacer importable el paquete `src` (env.py corre desde la raíz del proyecto).
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.services import models  # noqa: E402,F401  (registra todas las tablas en Base)
from src.services.db import Base  # noqa: E402

config = context.config

# URL: prioridad a DATABASE_URL del entorno; mismo default que la app.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./chordflow.db")
config.set_main_option("sqlalchemy.url", DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Genera el SQL sin conectar (modo --sql)."""
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Aplica las migraciones conectando a la BD."""
    section = config.get_section(config.config_ini_section, {})
    section["sqlalchemy.url"] = DATABASE_URL
    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
