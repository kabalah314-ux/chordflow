"""add plan to bands (V3-F3 andamiaje SaaS)

Revision ID: d7e9f1a2b3c4
Revises: c5d7e9f1a2b3
Create Date: 2026-06-17 14:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# identificadores de revisión, usados por Alembic.
revision: str = 'd7e9f1a2b3c4'
down_revision: Union[str, None] = 'c5d7e9f1a2b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Aditivo: plan SaaS de la banda ('free' por defecto). Sin cobro aún (andamiaje V3-F3).
    with op.batch_alter_table('bands', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('plan', sa.String(length=16), server_default=sa.text("'free'"), nullable=False))


def downgrade() -> None:
    with op.batch_alter_table('bands', schema=None) as batch_op:
        batch_op.drop_column('plan')
