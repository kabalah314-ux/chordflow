"""Giras (tours/tour_stops/tour_budget_lines) V3-F5

Revision ID: c5d7e9f1a2b3
Revises: b3f1a9c2d4e5
Create Date: 2026-06-17 13:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# identificadores de revisión, usados por Alembic.
revision: str = 'c5d7e9f1a2b3'
down_revision: Union[str, None] = 'b3f1a9c2d4e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Aditivo: 3 tablas nuevas de giras, aisladas por band_id. No toca nada existente.
    op.create_table(
        'tours',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('band_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=16), server_default=sa.text("'planning'"), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "status IN ('planning', 'active', 'done', 'cancelled')", name='ck_tours_status'),
        sa.ForeignKeyConstraint(['band_id'], ['bands.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('tours', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_tours_band_id'), ['band_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_tours_deleted_at'), ['deleted_at'], unique=False)

    op.create_table(
        'tour_stops',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tour_id', sa.String(length=36), nullable=False),
        sa.Column('event_id', sa.String(length=36), nullable=True),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('city', sa.String(length=255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['tour_id'], ['tours.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('tour_stops', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_tour_stops_tour_id'), ['tour_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_tour_stops_event_id'), ['event_id'], unique=False)

    op.create_table(
        'tour_budget_lines',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tour_id', sa.String(length=36), nullable=False),
        sa.Column('concept', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=64), nullable=True),
        sa.Column('estimated_amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.ForeignKeyConstraint(['tour_id'], ['tours.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('tour_budget_lines', schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f('ix_tour_budget_lines_tour_id'), ['tour_id'], unique=False)


def downgrade() -> None:
    op.drop_table('tour_budget_lines')
    op.drop_table('tour_stops')
    op.drop_table('tours')
