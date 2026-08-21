"""Add race-safe supplier and listing idempotency constraints.

Revision ID: 20260821_0003
Revises: 20260821_0002
Create Date: 2026-08-21
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260821_0003"
down_revision: Union[str, None] = "20260821_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _deduplicate_suppliers() -> None:
    bind = op.get_bind()
    duplicate_groups = bind.execute(
        sa.text(
            "SELECT name, source, MIN(id) AS keeper_id "
            "FROM suppliers GROUP BY name, source HAVING COUNT(*) > 1"
        )
    ).mappings().all()

    for group in duplicate_groups:
        duplicate_ids = bind.execute(
            sa.text(
                "SELECT id FROM suppliers "
                "WHERE name = :name AND source = :source AND id <> :keeper_id"
            ),
            dict(group),
        ).scalars().all()
        for duplicate_id in duplicate_ids:
            bind.execute(
                sa.text("UPDATE raw_listings SET seller_id = :keeper WHERE seller_id = :duplicate"),
                {"keeper": group["keeper_id"], "duplicate": duplicate_id},
            )
            bind.execute(sa.text("DELETE FROM suppliers WHERE id = :duplicate"), {"duplicate": duplicate_id})

    supplier_ids = bind.execute(sa.text("SELECT id FROM suppliers")).scalars().all()
    for supplier_id in supplier_ids:
        count = bind.execute(
            sa.text("SELECT COUNT(*) FROM raw_listings WHERE seller_id = :supplier_id"),
            {"supplier_id": supplier_id},
        ).scalar_one()
        bind.execute(
            sa.text("UPDATE suppliers SET total_listings = :count WHERE id = :supplier_id"),
            {"count": int(count or 0), "supplier_id": supplier_id},
        )


def upgrade() -> None:
    _deduplicate_suppliers()
    with op.batch_alter_table("suppliers") as batch_op:
        batch_op.create_unique_constraint("uq_suppliers_name_source", ["name", "source"])
    with op.batch_alter_table("raw_listings") as batch_op:
        batch_op.add_column(sa.Column("ingestion_key", sa.String(length=64), nullable=True))
        batch_op.create_unique_constraint("uq_raw_listings_ingestion_key", ["ingestion_key"])


def downgrade() -> None:
    with op.batch_alter_table("raw_listings") as batch_op:
        batch_op.drop_constraint("uq_raw_listings_ingestion_key", type_="unique")
        batch_op.drop_column("ingestion_key")
    with op.batch_alter_table("suppliers") as batch_op:
        batch_op.drop_constraint("uq_suppliers_name_source", type_="unique")
