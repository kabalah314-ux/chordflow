"""V6-F9 funciones de banda: semáforo, vista por miembro, pizarra, hoja del bolo, votación de
fechas, feedback y eventos de producto (T-V6-81/82/83/86/88/92/94)

Revision ID: b7c8d9e0f1a2
Revises: a1b2c3d4e5f6
Create Date: 2026-11-05 19:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b7c8d9e0f1a2'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Song.duration_sec (T-V6-88) ──
    with op.batch_alter_table('songs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('duration_sec', sa.Integer(), nullable=True))

    # ── Hoja del bolo en events (T-V6-86) ──
    with op.batch_alter_table('events', schema=None) as batch_op:
        batch_op.add_column(sa.Column('load_in_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('soundcheck_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('doors_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('set_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('address', sa.String(length=512), nullable=True))
        batch_op.add_column(sa.Column('parking_notes', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('backline_notes', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('sheet_token', sa.String(length=64), nullable=True))
        batch_op.create_index(batch_op.f('ix_events_sheet_token'), ['sheet_token'], unique=True)

    # ── Semáforo del repertorio (T-V6-83) ──
    op.create_table('song_statuses',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('song_id', sa.String(length=36), nullable=False),
        sa.Column('band_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('status', sa.String(length=16), nullable=False),
        sa.Column('shared', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint("status IN ('pending', 'improving', 'mastered')",
                           name='ck_song_statuses_status'),
        sa.ForeignKeyConstraint(['band_id'], ['bands.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['song_id'], ['songs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('song_id', 'user_id', name='uq_song_status_song_user'),
    )
    with op.batch_alter_table('song_statuses', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_song_statuses_band_id'), ['band_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_song_statuses_song_id'), ['song_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_song_statuses_user_id'), ['user_id'], unique=False)

    # ── Vista por miembro (T-V6-81) ──
    op.create_table('song_member_prefs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('song_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('transpose', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('capo', sa.Integer(), nullable=True),
        sa.Column('view_mode', sa.String(length=16), nullable=True),
        sa.Column('font_scale', sa.Float(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['song_id'], ['songs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('song_id', 'user_id', name='uq_song_pref_song_user'),
    )
    with op.batch_alter_table('song_member_prefs', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_song_member_prefs_song_id'), ['song_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_song_member_prefs_user_id'), ['user_id'], unique=False)

    # ── Pizarra (T-V6-92) ──
    op.create_table('band_notes',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('band_id', sa.String(length=36), nullable=False),
        sa.Column('author_id', sa.String(length=36), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('assignee_id', sa.String(length=36), nullable=True),
        sa.Column('is_pinned', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('done_at', sa.DateTime(), nullable=True),
        sa.Column('song_id', sa.String(length=36), nullable=True),
        sa.Column('event_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['band_id'], ['bands.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['song_id'], ['songs.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('band_notes', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_band_notes_band_id'), ['band_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_band_notes_deleted_at'), ['deleted_at'], unique=False)

    # ── Checklist de la hoja del bolo (T-V6-86) ──
    op.create_table('event_checklist_items',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('event_id', sa.String(length=36), nullable=False),
        sa.Column('text', sa.String(length=255), nullable=False),
        sa.Column('assignee_id', sa.String(length=36), nullable=True),
        sa.Column('position', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('done_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('event_checklist_items', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_event_checklist_items_event_id'), ['event_id'],
                              unique=False)

    # ── Votación de fechas (T-V6-82) ──
    op.create_table('date_polls',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('band_id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('type', sa.String(length=16), server_default=sa.text("'rehearsal'"),
                  nullable=False),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('token', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=16), server_default=sa.text("'open'"), nullable=False),
        sa.Column('event_id', sa.String(length=36), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint("status IN ('open', 'closed')", name='ck_date_polls_status'),
        sa.ForeignKeyConstraint(['band_id'], ['bands.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('date_polls', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_date_polls_band_id'), ['band_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_date_polls_deleted_at'), ['deleted_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_date_polls_token'), ['token'], unique=True)

    op.create_table('date_poll_options',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('poll_id', sa.String(length=36), nullable=False),
        sa.Column('starts_at', sa.DateTime(), nullable=False),
        sa.Column('ends_at', sa.DateTime(), nullable=True),
        sa.Column('position', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.ForeignKeyConstraint(['poll_id'], ['date_polls.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('date_poll_options', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_date_poll_options_poll_id'), ['poll_id'], unique=False)

    op.create_table('date_poll_votes',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('option_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('status', sa.String(length=8), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint("status IN ('yes', 'no', 'maybe')", name='ck_date_poll_votes_status'),
        sa.ForeignKeyConstraint(['option_id'], ['date_poll_options.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('option_id', 'user_id', name='uq_poll_vote_option_user'),
    )
    with op.batch_alter_table('date_poll_votes', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_date_poll_votes_option_id'), ['option_id'],
                              unique=False)

    # ── Feedback + eventos de producto (T-V6-94) ──
    op.create_table('feedback',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('page', sa.String(length=255), nullable=True),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('user_agent', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('feedback', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_feedback_user_id'), ['user_id'], unique=False)

    op.create_table('product_events',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('band_id', sa.String(length=36), nullable=True),
        sa.Column('kind', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('product_events', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_product_events_band_id'), ['band_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_product_events_kind'), ['kind'], unique=False)
        batch_op.create_index(batch_op.f('ix_product_events_user_id'), ['user_id'], unique=False)


def downgrade() -> None:
    for table, idxs in (
        ('product_events', ['ix_product_events_user_id', 'ix_product_events_kind',
                            'ix_product_events_band_id']),
        ('feedback', ['ix_feedback_user_id']),
        ('date_poll_votes', ['ix_date_poll_votes_option_id']),
        ('date_poll_options', ['ix_date_poll_options_poll_id']),
        ('date_polls', ['ix_date_polls_token', 'ix_date_polls_deleted_at', 'ix_date_polls_band_id']),
        ('event_checklist_items', ['ix_event_checklist_items_event_id']),
        ('band_notes', ['ix_band_notes_deleted_at', 'ix_band_notes_band_id']),
        ('song_member_prefs', ['ix_song_member_prefs_user_id', 'ix_song_member_prefs_song_id']),
        ('song_statuses', ['ix_song_statuses_user_id', 'ix_song_statuses_song_id',
                           'ix_song_statuses_band_id']),
    ):
        with op.batch_alter_table(table, schema=None) as batch_op:
            for ix in idxs:
                batch_op.drop_index(ix)
        op.drop_table(table)

    with op.batch_alter_table('events', schema=None) as batch_op:
        batch_op.drop_index('ix_events_sheet_token')
        for col in ('sheet_token', 'backline_notes', 'parking_notes', 'address', 'set_at',
                    'doors_at', 'soundcheck_at', 'load_in_at'):
            batch_op.drop_column(col)

    with op.batch_alter_table('songs', schema=None) as batch_op:
        batch_op.drop_column('duration_sec')
