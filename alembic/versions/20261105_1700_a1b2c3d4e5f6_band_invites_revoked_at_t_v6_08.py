"""band_invites.revoked_at (T-V6-08 invitaciones revocables)

Revision ID: a1b2c3d4e5f6
Revises: 37fb00af7e5c
Create Date: 2026-11-05 17:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# identificadores de revisión, usados por Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '37fb00af7e5c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('band_invites', schema=None) as batch_op:
        batch_op.add_column(sa.Column('revoked_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('band_invites', schema=None) as batch_op:
        batch_op.drop_column('revoked_at')
