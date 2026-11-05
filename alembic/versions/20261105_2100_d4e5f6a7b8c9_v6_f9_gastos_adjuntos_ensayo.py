"""V6-F9 (3/3): gastos recurrentes, adjuntos, modo ensayo y marcas de práctica
(T-V6-84, 85, 87, 95)

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-11-05 21:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('songs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('practice_refs', sa.JSON(), nullable=True))

    op.create_table('recurring_expenses',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('band_id', sa.String(length=36), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('category', sa.String(length=64), nullable=True),
        sa.Column('paid_by', sa.String(length=36), nullable=True),
        sa.Column('paid_by_fund', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('day_of_month', sa.Integer(), server_default=sa.text('1'), nullable=False),
        sa.Column('last_logged_month', sa.String(length=7), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['band_id'], ['bands.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('recurring_expenses', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_recurring_expenses_band_id'), ['band_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_recurring_expenses_deleted_at'), ['deleted_at'],
                              unique=False)

    op.create_table('attachments',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('owner_id', sa.String(length=36), nullable=False),
        sa.Column('band_id', sa.String(length=36), nullable=True),
        sa.Column('song_id', sa.String(length=36), nullable=True),
        sa.Column('event_id', sa.String(length=36), nullable=True),
        sa.Column('kind', sa.String(length=16), nullable=False),
        sa.Column('url', sa.String(length=1024), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('duration_sec', sa.Integer(), nullable=True),
        sa.Column('size_bytes', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint("kind IN ('audio', 'pdf', 'image', 'link')", name='ck_attachments_kind'),
        sa.ForeignKeyConstraint(['band_id'], ['bands.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['song_id'], ['songs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('attachments', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_attachments_band_id'), ['band_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_attachments_deleted_at'), ['deleted_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_attachments_event_id'), ['event_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_attachments_owner_id'), ['owner_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_attachments_song_id'), ['song_id'], unique=False)

    op.create_table('rehearsal_sessions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('band_id', sa.String(length=36), nullable=False),
        sa.Column('event_id', sa.String(length=36), nullable=True),
        sa.Column('started_by', sa.String(length=36), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('items', sa.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['band_id'], ['bands.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('rehearsal_sessions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_rehearsal_sessions_band_id'), ['band_id'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('rehearsal_sessions', schema=None) as batch_op:
        batch_op.drop_index('ix_rehearsal_sessions_band_id')
    op.drop_table('rehearsal_sessions')
    with op.batch_alter_table('attachments', schema=None) as batch_op:
        for ix in ('ix_attachments_song_id', 'ix_attachments_owner_id', 'ix_attachments_event_id',
                   'ix_attachments_deleted_at', 'ix_attachments_band_id'):
            batch_op.drop_index(ix)
    op.drop_table('attachments')
    with op.batch_alter_table('recurring_expenses', schema=None) as batch_op:
        batch_op.drop_index('ix_recurring_expenses_deleted_at')
        batch_op.drop_index('ix_recurring_expenses_band_id')
    op.drop_table('recurring_expenses')
    with op.batch_alter_table('songs', schema=None) as batch_op:
        batch_op.drop_column('practice_refs')
