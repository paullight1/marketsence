"""Use fixed-point NUMERIC columns for monetary values.

Revision ID: 20260821_0002
Revises: 20260821_0001
Create Date: 2026-08-21
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260821_0002"
down_revision: Union[str, None] = "20260821_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("raw_listings") as batch_op:
        batch_op.alter_column(
            "price",
            existing_type=sa.Float(),
            type_=sa.Numeric(precision=18, scale=2),
            existing_nullable=False,
        )
    with op.batch_alter_table("price_history") as batch_op:
        batch_op.alter_column(
            "price",
            existing_type=sa.Float(),
            type_=sa.Numeric(precision=18, scale=2),
            existing_nullable=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("price_history") as batch_op:
        batch_op.alter_column(
            "price",
            existing_type=sa.Numeric(precision=18, scale=2),
            type_=sa.Float(),
            existing_nullable=False,
        )
    with op.batch_alter_table("raw_listings") as batch_op:
        batch_op.alter_column(
            "price",
            existing_type=sa.Numeric(precision=18, scale=2),
            type_=sa.Float(),
            existing_nullable=False,
        )
