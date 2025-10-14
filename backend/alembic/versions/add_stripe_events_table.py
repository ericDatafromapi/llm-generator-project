"""Add stripe_events table for webhook idempotency

Revision ID: e8f4c2d1a3b5
Revises: d6939c5121ef
Create Date: 2025-10-13 21:44:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e8f4c2d1a3b5'
down_revision: Union[str, None] = 'd6939c5121ef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create stripe_events table
    op.create_table('stripe_events',
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('type', sa.String(length=100), nullable=False),
        sa.Column('created', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('processed_at', sa.DateTime(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_stripe_events_id'), 'stripe_events', ['id'], unique=False)
    op.create_index(op.f('ix_stripe_events_type'), 'stripe_events', ['type'], unique=False)
    op.create_index(op.f('ix_stripe_events_created'), 'stripe_events', ['created'], unique=False)


def downgrade() -> None:
    # Drop stripe_events table
    op.drop_index(op.f('ix_stripe_events_created'), table_name='stripe_events')
    op.drop_index(op.f('ix_stripe_events_type'), table_name='stripe_events')
    op.drop_index(op.f('ix_stripe_events_id'), table_name='stripe_events')
    op.drop_table('stripe_events')