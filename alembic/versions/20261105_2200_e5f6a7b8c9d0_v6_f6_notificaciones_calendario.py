"""V6-F6: notificaciones in-app y suscripción de calendario (T-V6-61, T-V6-62)

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-11-05 22:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('musician_profiles', schema=None) as batch_op:
        batch_op.add_column(sa.Column('calendar_token', sa.String(length=64), nullable=True))
        batch_op.create_index(batch_op.f('ix_musician_profiles_calendar_token'), ['calendar_token'],
                              unique=True)

    op.create_table('notifications',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('band_id', sa.String(length=36), nullable=True),
        sa.Column('kind', sa.String(length=32), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('body', sa.String(length=500), nullable=True),
        sa.Column('link', sa.String(length=512), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['band_id'], ['bands.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('notifications', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_notifications_created_at'), ['created_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_notifications_user_id'), ['user_id'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('notifications', schema=None) as batch_op:
        batch_op.drop_index('ix_notifications_user_id')
        batch_op.drop_index('ix_notifications_created_at')
    op.drop_table('notifications')
    with op.batch_alter_table('musician_profiles', schema=None) as batch_op:
        batch_op.drop_index('ix_musician_profiles_calendar_token')
        batch_op.drop_column('calendar_token')
