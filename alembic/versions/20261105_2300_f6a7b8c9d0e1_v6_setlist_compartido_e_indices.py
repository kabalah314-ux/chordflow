"""V6: setlist compartido por enlace (T-V6-63) e índices compuestos (T-V6-75)

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-11-05 23:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('setlists', schema=None) as batch_op:
        batch_op.add_column(sa.Column('share_token', sa.String(length=64), nullable=True))
        batch_op.create_index(batch_op.f('ix_setlists_share_token'), ['share_token'], unique=True)
    with op.batch_alter_table('events', schema=None) as batch_op:
        batch_op.create_index('ix_events_band_starts', ['band_id', 'starts_at'], unique=False)
    with op.batch_alter_table('transactions', schema=None) as batch_op:
        batch_op.create_index('ix_transactions_band_date', ['band_id', 'date'], unique=False)
    with op.batch_alter_table('messages', schema=None) as batch_op:
        batch_op.create_index('ix_messages_band_created', ['band_id', 'created_at'], unique=False)
    with op.batch_alter_table('notifications', schema=None) as batch_op:
        batch_op.create_index('ix_notifications_user_read', ['user_id', 'read_at'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('notifications', schema=None) as batch_op:
        batch_op.drop_index('ix_notifications_user_read')
    with op.batch_alter_table('messages', schema=None) as batch_op:
        batch_op.drop_index('ix_messages_band_created')
    with op.batch_alter_table('transactions', schema=None) as batch_op:
        batch_op.drop_index('ix_transactions_band_date')
    with op.batch_alter_table('events', schema=None) as batch_op:
        batch_op.drop_index('ix_events_band_starts')
    with op.batch_alter_table('setlists', schema=None) as batch_op:
        batch_op.drop_index('ix_setlists_share_token')
        batch_op.drop_column('share_token')
