"""Biblioteca global / catálogo público V3-F9

Revision ID: e9f1a2b3c4d5
Revises: d7e9f1a2b3c4
Create Date: 2026-06-17 15:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# identificadores de revisión, usados por Alembic.
revision: str = 'e9f1a2b3c4d5'
down_revision: Union[str, None] = 'd7e9f1a2b3c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Plano de datos separado (no toca lo privado): catálogo público de partituras.
    op.create_table(
        'musical_works',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('artist', sa.String(length=255), nullable=True),
        sa.Column('norm_title', sa.String(length=255), nullable=False),
        sa.Column('norm_artist', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('norm_artist', 'norm_title', name='uq_work_artist_title'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('musical_works', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_musical_works_norm_title'), ['norm_title'], unique=False)
        batch_op.create_index(batch_op.f('ix_musical_works_norm_artist'), ['norm_artist'], unique=False)

    op.create_table(
        'public_scores',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('work_id', sa.String(length=36), nullable=False),
        sa.Column('publisher_id', sa.String(length=36), nullable=False),
        sa.Column('source_band_id', sa.String(length=36), nullable=True),
        sa.Column('source_song_id', sa.String(length=36), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('artist', sa.String(length=255), nullable=True),
        sa.Column('key_root', sa.String(length=4), nullable=True),
        sa.Column('key_mode', sa.String(length=32), nullable=True),
        sa.Column('bpm', sa.Integer(), nullable=True),
        sa.Column('reference_url', sa.String(length=512), nullable=True),
        sa.Column('content_json', sa.JSON(), nullable=False),
        sa.Column('rating_avg', sa.Numeric(precision=3, scale=2), server_default=sa.text('0'), nullable=False),
        sa.Column('rating_count', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('import_count', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('status', sa.String(length=16), server_default=sa.text("'published'"), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint("status IN ('published', 'hidden', 'removed')", name='ck_public_scores_status'),
        sa.ForeignKeyConstraint(['work_id'], ['musical_works.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('public_scores', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_public_scores_work_id'), ['work_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_public_scores_publisher_id'), ['publisher_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_public_scores_source_song_id'), ['source_song_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_public_scores_deleted_at'), ['deleted_at'], unique=False)
        batch_op.create_index('ix_public_scores_status_deleted', ['status', 'deleted_at'], unique=False)

    op.create_table(
        'score_ratings',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('public_score_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('stars', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('public_score_id', 'user_id', name='uq_rating_score_user'),
        sa.ForeignKeyConstraint(['public_score_id'], ['public_scores.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('score_ratings', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_score_ratings_public_score_id'), ['public_score_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_score_ratings_user_id'), ['user_id'], unique=False)

    op.create_table(
        'score_comments',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('public_score_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['public_score_id'], ['public_scores.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('score_comments', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_score_comments_public_score_id'), ['public_score_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_score_comments_user_id'), ['user_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_score_comments_deleted_at'), ['deleted_at'], unique=False)


def downgrade() -> None:
    op.drop_table('score_comments')
    op.drop_table('score_ratings')
    op.drop_table('public_scores')
    op.drop_table('musical_works')
