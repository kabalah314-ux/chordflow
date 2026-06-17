"""add reference_url to songs (V3-F4 T-090)

Revision ID: b3f1a9c2d4e5
Revises: 7022a3162284
Create Date: 2026-06-17 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# identificadores de revisión, usados por Alembic.
revision: str = 'b3f1a9c2d4e5'
down_revision: Union[str, None] = '7022a3162284'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Aditivo: enlace de referencia (YouTube/Spotify) por canción. Nullable, no rompe nada.
    with op.batch_alter_table('songs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('reference_url', sa.String(length=512), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('songs', schema=None) as batch_op:
        batch_op.drop_column('reference_url')
