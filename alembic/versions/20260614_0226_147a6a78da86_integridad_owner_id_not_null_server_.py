"""integridad: owner_id NOT NULL, server_defaults, CHECK Line.type (T-034/035/036)

Revision ID: 147a6a78da86
Revises: dac91229a048
Create Date: 2026-06-14 02:26:18.036033

Notas:
- owner_id → NOT NULL (T-034): asume que no hay filas con owner_id NULL (la API siempre lo
  asigna). Si una BD vieja las tuviera, rellenarlas antes de migrar.
- server_default (T-036): los defaults dejan de vivir solo en Python; un INSERT por SQL directo
  también los recibe. `compare_server_default` está desactivado en env.py, así que no genera drift.
- CHECK ck_lines_type (T-035): defensa en profundidad sobre la validación de schema (Literal).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# identificadores de revisión, usados por Alembic.
revision: str = '147a6a78da86'
down_revision: Union[str, None] = 'dac91229a048'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('songs', schema=None) as batch_op:
        batch_op.alter_column('owner_id',
               existing_type=sa.VARCHAR(length=36),
               nullable=False)
        batch_op.alter_column('bpm', existing_type=sa.INTEGER(),
               server_default=sa.text('120'))
        batch_op.alter_column('time_signature_num', existing_type=sa.INTEGER(),
               server_default=sa.text('4'))
        batch_op.alter_column('time_signature_den', existing_type=sa.INTEGER(),
               server_default=sa.text('4'))
        batch_op.alter_column('capo', existing_type=sa.INTEGER(),
               server_default=sa.text('0'))
        batch_op.alter_column('format_version', existing_type=sa.VARCHAR(length=8),
               server_default=sa.text("'1.0'"))
        batch_op.alter_column('is_public', existing_type=sa.BOOLEAN(),
               server_default=sa.text('0'))

    with op.batch_alter_table('sections', schema=None) as batch_op:
        batch_op.alter_column('repeat_count', existing_type=sa.INTEGER(),
               server_default=sa.text('1'))

    with op.batch_alter_table('lines', schema=None) as batch_op:
        batch_op.create_check_constraint(
            'ck_lines_type',
            "type IN ('lyric', 'tab', 'chord_only', 'comment', 'spacer')",
        )


def downgrade() -> None:
    with op.batch_alter_table('lines', schema=None) as batch_op:
        batch_op.drop_constraint('ck_lines_type', type_='check')

    with op.batch_alter_table('sections', schema=None) as batch_op:
        batch_op.alter_column('repeat_count', existing_type=sa.INTEGER(),
               server_default=None)

    with op.batch_alter_table('songs', schema=None) as batch_op:
        batch_op.alter_column('is_public', existing_type=sa.BOOLEAN(), server_default=None)
        batch_op.alter_column('format_version', existing_type=sa.VARCHAR(length=8),
               server_default=None)
        batch_op.alter_column('capo', existing_type=sa.INTEGER(), server_default=None)
        batch_op.alter_column('time_signature_den', existing_type=sa.INTEGER(),
               server_default=None)
        batch_op.alter_column('time_signature_num', existing_type=sa.INTEGER(),
               server_default=None)
        batch_op.alter_column('bpm', existing_type=sa.INTEGER(), server_default=None)
        batch_op.alter_column('owner_id', existing_type=sa.VARCHAR(length=36), nullable=True)
