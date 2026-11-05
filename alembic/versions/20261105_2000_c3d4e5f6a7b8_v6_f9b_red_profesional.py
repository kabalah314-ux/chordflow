"""V6-F9b red profesional: perfiles de sala/profesional, convocatorias, candidaturas, EPK,
mensajes de contacto, valoraciones y reportes (T-V6-96..100)

Revision ID: c3d4e5f6a7b8
Revises: b7c8d9e0f1a2
Create Date: 2026-11-05 20:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b7c8d9e0f1a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_KINDS = ("'venue', 'booker', 'photographer', 'video', 'sound_tech', 'light_tech', 'studio', "
          "'rehearsal_room', 'luthier', 'design', 'press', 'teacher', 'other'")


def upgrade() -> None:
    op.create_table('pro_profiles',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('kind', sa.String(length=24), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('zone', sa.String(length=255), nullable=True),
        sa.Column('services', sa.JSON(), nullable=True),
        sa.Column('price_hint', sa.String(length=255), nullable=True),
        sa.Column('links', sa.JSON(), nullable=True),
        sa.Column('photos', sa.JSON(), nullable=True),
        sa.Column('avatar_url', sa.String(length=512), nullable=True),
        sa.Column('phone', sa.String(length=64), nullable=True),
        sa.Column('show_phone', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('capacity', sa.Integer(), nullable=True),
        sa.Column('styles', sa.JSON(), nullable=True),
        sa.Column('deal_types', sa.JSON(), nullable=True),
        sa.Column('backline', sa.Text(), nullable=True),
        sa.Column('address', sa.String(length=512), nullable=True),
        sa.Column('visibility', sa.String(length=16), server_default=sa.text("'public'"),
                  nullable=False),
        sa.Column('plan', sa.String(length=16), server_default=sa.text("'free'"), nullable=False),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('hidden_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint(f"kind IN ({_KINDS})", name='ck_pro_profiles_kind'),
        sa.CheckConstraint("visibility IN ('private', 'unlisted', 'public')",
                           name='ck_pro_profiles_visibility'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('pro_profiles', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_pro_profiles_deleted_at'), ['deleted_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_pro_profiles_kind'), ['kind'], unique=False)
        batch_op.create_index(batch_op.f('ix_pro_profiles_user_id'), ['user_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_pro_profiles_zone'), ['zone'], unique=False)

    op.create_table('gig_calls',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('pro_profile_id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('starts_at', sa.DateTime(), nullable=True),
        sa.Column('ends_at', sa.DateTime(), nullable=True),
        sa.Column('flexible_dates', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('styles', sa.JSON(), nullable=True),
        sa.Column('format', sa.String(length=255), nullable=True),
        sa.Column('deal_type', sa.String(length=16), nullable=True),
        sa.Column('fee', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('conditions', sa.Text(), nullable=True),
        sa.Column('zone', sa.String(length=255), nullable=True),
        sa.Column('deadline_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=16), server_default=sa.text("'open'"), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint("status IN ('open', 'closed', 'filled')", name='ck_gig_calls_status'),
        sa.ForeignKeyConstraint(['pro_profile_id'], ['pro_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('gig_calls', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_gig_calls_deleted_at'), ['deleted_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_gig_calls_pro_profile_id'), ['pro_profile_id'],
                              unique=False)
        batch_op.create_index(batch_op.f('ix_gig_calls_zone'), ['zone'], unique=False)

    op.create_table('gig_applications',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('gig_call_id', sa.String(length=36), nullable=False),
        sa.Column('band_id', sa.String(length=36), nullable=False),
        sa.Column('applied_by', sa.String(length=36), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('epk_snapshot', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=16), server_default=sa.text("'sent'"), nullable=False),
        sa.Column('event_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint("status IN ('sent', 'seen', 'shortlisted', 'chosen', 'declined')",
                           name='ck_gig_applications_status'),
        sa.ForeignKeyConstraint(['band_id'], ['bands.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['gig_call_id'], ['gig_calls.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('gig_call_id', 'band_id', name='uq_gig_application_call_band'),
    )
    with op.batch_alter_table('gig_applications', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_gig_applications_band_id'), ['band_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_gig_applications_gig_call_id'), ['gig_call_id'],
                              unique=False)

    op.create_table('band_epks',
        sa.Column('band_id', sa.String(length=36), nullable=False),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('styles', sa.JSON(), nullable=True),
        sa.Column('formation', sa.String(length=64), nullable=True),
        sa.Column('zone', sa.String(length=255), nullable=True),
        sa.Column('links', sa.JSON(), nullable=True),
        sa.Column('photos', sa.JSON(), nullable=True),
        sa.Column('fee_hint', sa.String(length=255), nullable=True),
        sa.Column('rider_notes', sa.Text(), nullable=True),
        sa.Column('is_public', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['band_id'], ['bands.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('band_id'),
    )
    with op.batch_alter_table('band_epks', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_band_epks_zone'), ['zone'], unique=False)

    op.create_table('contact_threads',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('initiator_id', sa.String(length=36), nullable=False),
        sa.Column('initiator_band_id', sa.String(length=36), nullable=True),
        sa.Column('target_pro_id', sa.String(length=36), nullable=True),
        sa.Column('target_band_id', sa.String(length=36), nullable=True),
        sa.Column('context_kind', sa.String(length=16), nullable=True),
        sa.Column('context_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('last_message_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['initiator_band_id'], ['bands.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['target_band_id'], ['bands.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_pro_id'], ['pro_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('contact_threads', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_contact_threads_initiator_id'), ['initiator_id'],
                              unique=False)
        batch_op.create_index(batch_op.f('ix_contact_threads_last_message_at'), ['last_message_at'],
                              unique=False)
        batch_op.create_index(batch_op.f('ix_contact_threads_target_band_id'), ['target_band_id'],
                              unique=False)
        batch_op.create_index(batch_op.f('ix_contact_threads_target_pro_id'), ['target_pro_id'],
                              unique=False)

    op.create_table('contact_messages',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('thread_id', sa.String(length=36), nullable=False),
        sa.Column('author_id', sa.String(length=36), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['thread_id'], ['contact_threads.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('contact_messages', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_contact_messages_thread_id'), ['thread_id'],
                              unique=False)

    op.create_table('reviews',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('from_user_id', sa.String(length=36), nullable=False),
        sa.Column('to_pro_id', sa.String(length=36), nullable=True),
        sa.Column('to_band_id', sa.String(length=36), nullable=True),
        sa.Column('stars', sa.Integer(), nullable=False),
        sa.Column('body', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('hidden_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint('stars BETWEEN 1 AND 5', name='ck_reviews_stars'),
        sa.ForeignKeyConstraint(['to_band_id'], ['bands.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['to_pro_id'], ['pro_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('from_user_id', 'to_pro_id', 'to_band_id',
                            name='uq_review_author_target'),
    )
    with op.batch_alter_table('reviews', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_reviews_from_user_id'), ['from_user_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_reviews_to_band_id'), ['to_band_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_reviews_to_pro_id'), ['to_pro_id'], unique=False)

    op.create_table('reports',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('reporter_id', sa.String(length=36), nullable=False),
        sa.Column('target_kind', sa.String(length=16), nullable=False),
        sa.Column('target_id', sa.String(length=36), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('reports', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_reports_reporter_id'), ['reporter_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_reports_target_id'), ['target_id'], unique=False)


def downgrade() -> None:
    for table, idxs in (
        ('reports', ['ix_reports_target_id', 'ix_reports_reporter_id']),
        ('reviews', ['ix_reviews_to_pro_id', 'ix_reviews_to_band_id', 'ix_reviews_from_user_id']),
        ('contact_messages', ['ix_contact_messages_thread_id']),
        ('contact_threads', ['ix_contact_threads_target_pro_id', 'ix_contact_threads_target_band_id',
                             'ix_contact_threads_last_message_at',
                             'ix_contact_threads_initiator_id']),
        ('band_epks', ['ix_band_epks_zone']),
        ('gig_applications', ['ix_gig_applications_gig_call_id', 'ix_gig_applications_band_id']),
        ('gig_calls', ['ix_gig_calls_zone', 'ix_gig_calls_pro_profile_id', 'ix_gig_calls_deleted_at']),
        ('pro_profiles', ['ix_pro_profiles_zone', 'ix_pro_profiles_user_id', 'ix_pro_profiles_kind',
                          'ix_pro_profiles_deleted_at']),
    ):
        with op.batch_alter_table(table, schema=None) as batch_op:
            for ix in idxs:
                batch_op.drop_index(ix)
        op.drop_table(table)
