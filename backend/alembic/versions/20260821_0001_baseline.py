"""MarketSense baseline schema.

Revision ID: 20260821_0001
Revises:
Create Date: 2026-08-21
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260821_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["parent_id"], ["categories.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_categories_id"), "categories", ["id"], unique=False)

    op.create_table(
        "suppliers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("location", sa.String(length=100), nullable=True),
        sa.Column("contact_info", sa.JSON(), nullable=True),
        sa.Column("trust_score", sa.Float(), nullable=True),
        sa.Column("total_listings", sa.Integer(), nullable=True),
        sa.Column("successful_transactions", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_suppliers_id"), "suppliers", ["id"], unique=False)

    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("normalized_name", sa.String(length=255), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("brand", sa.String(length=100), nullable=True),
        sa.Column("specifications", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_products_id"), "products", ["id"], unique=False)
    op.create_index(op.f("ix_products_normalized_name"), "products", ["normalized_name"], unique=False)

    op.create_table(
        "raw_listings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("original_name", sa.String(length=255), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("seller_id", sa.Integer(), nullable=False),
        sa.Column("location", sa.String(length=100), nullable=True),
        sa.Column("url", sa.String(length=500), nullable=True),
        sa.Column("raw_data", sa.JSON(), nullable=True),
        sa.Column("is_suspicious", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("product_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["seller_id"], ["suppliers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_raw_listings_id"), "raw_listings", ["id"], unique=False)

    op.create_table(
        "price_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(), nullable=True),
        sa.Column("source", sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_price_history_id"), "price_history", ["id"], unique=False)

    op.create_table(
        "suspicious_listings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("listing_id", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=True),
        sa.Column("reviewed", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["listing_id"], ["raw_listings.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_suspicious_listings_id"), "suspicious_listings", ["id"], unique=False)

    op.create_table(
        "jobs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("job_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("idempotency_key", sa.String(length=255), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("available_at", sa.DateTime(), nullable=False),
        sa.Column("lease_expires_at", sa.DateTime(), nullable=True),
        sa.Column("worker_id", sa.String(length=255), nullable=True),
        sa.Column("cancel_requested", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_type", "idempotency_key", name="uq_jobs_type_idempotency"),
    )
    op.create_index(op.f("ix_jobs_available_at"), "jobs", ["available_at"], unique=False)
    op.create_index(op.f("ix_jobs_job_type"), "jobs", ["job_type"], unique=False)
    op.create_index(op.f("ix_jobs_lease_expires_at"), "jobs", ["lease_expires_at"], unique=False)
    op.create_index(op.f("ix_jobs_status"), "jobs", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_jobs_status"), table_name="jobs")
    op.drop_index(op.f("ix_jobs_lease_expires_at"), table_name="jobs")
    op.drop_index(op.f("ix_jobs_job_type"), table_name="jobs")
    op.drop_index(op.f("ix_jobs_available_at"), table_name="jobs")
    op.drop_table("jobs")
    op.drop_index(op.f("ix_suspicious_listings_id"), table_name="suspicious_listings")
    op.drop_table("suspicious_listings")
    op.drop_index(op.f("ix_price_history_id"), table_name="price_history")
    op.drop_table("price_history")
    op.drop_index(op.f("ix_raw_listings_id"), table_name="raw_listings")
    op.drop_table("raw_listings")
    op.drop_index(op.f("ix_products_normalized_name"), table_name="products")
    op.drop_index(op.f("ix_products_id"), table_name="products")
    op.drop_table("products")
    op.drop_index(op.f("ix_suppliers_id"), table_name="suppliers")
    op.drop_table("suppliers")
    op.drop_index(op.f("ix_categories_id"), table_name="categories")
    op.drop_table("categories")
