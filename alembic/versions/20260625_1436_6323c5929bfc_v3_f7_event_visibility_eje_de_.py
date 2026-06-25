"""V3-F7 Event.visibility (eje de visibilidad, default private)

Revision ID: 6323c5929bfc
Revises: b6434fe1096d
Create Date: 2026-06-25 14:36:27.975410
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# identificadores de revisión, usados por Alembic.
revision: str = '6323c5929bfc'
down_revision: Union[str, None] = 'b6434fe1096d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Aditiva: nueva columna `visibility` (default 'private') + su CHECK. El CHECK lo añadimos a mano
    # (autogenerate no introspecta CHECKs); batch mode lo aplica también en SQLite (recrea la tabla).
    with op.batch_alter_table('events', schema=None) as batch_op:
        batch_op.add_column(sa.Column('visibility', sa.String(length=16), server_default=sa.text("'private'"), nullable=False))
        batch_op.create_check_constraint(
            'ck_events_visibility',
            "visibility IN ('private', 'unlisted', 'public')",
        )


def downgrade() -> None:
    with op.batch_alter_table('events', schema=None) as batch_op:
        batch_op.drop_constraint('ck_events_visibility', type_='check')
        batch_op.drop_column('visibility')
