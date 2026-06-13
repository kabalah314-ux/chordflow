"""FKs ON DELETE CASCADE (T-033)

Defensa en profundidad sobre el cascade ORM (+ PRAGMA foreign_keys=ON): aunque alguien
borre una fila padre con SQL directo (sin pasar por el ORM), la BD borra en cascada las
hijas y no quedan filas huérfanas. Complementa T-003.

SQLite no permite ALTER de una FK: el `batch_alter_table` recrea la tabla. Y para SOLTAR
una FK *sin nombre* en batch mode hace falta un naming convention que le dé un nombre
determinista a la constraint reflejada; sin él, `drop_constraint(None)` es un no-op y la
tabla se recrea conservando la FK vieja (sin ondelete). Por eso pasamos `naming_convention`.

Revision ID: dac91229a048
Revises: fefcd5a0b14a
Create Date: 2026-06-13 10:24:49.969270
"""
from typing import Sequence, Union

from alembic import op

# identificadores de revisión, usados por Alembic.
revision: str = 'dac91229a048'
down_revision: Union[str, None] = 'fefcd5a0b14a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Da nombre determinista a las FKs reflejadas (sin nombre en la BD) para poder soltarlas.
NAMING = {"fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"}

# (tabla hija, columna FK, tabla padre) de las 4 relaciones.
RELACIONES = [
    ("chord_markers", "line_id", "lines"),
    ("lines", "section_id", "sections"),
    ("sections", "song_id", "songs"),
    ("tab_lines", "line_id", "lines"),
]


def _recrear_fks(ondelete):
    for tabla, col, padre in RELACIONES:
        nombre = f"fk_{tabla}_{col}_{padre}"
        with op.batch_alter_table(tabla, schema=None, naming_convention=NAMING) as batch_op:
            batch_op.drop_constraint(nombre, type_="foreignkey")
            batch_op.create_foreign_key(nombre, padre, [col], ["id"], ondelete=ondelete)


def upgrade() -> None:
    _recrear_fks(ondelete="CASCADE")


def downgrade() -> None:
    _recrear_fks(ondelete=None)
