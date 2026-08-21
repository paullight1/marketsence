from datetime import datetime, timezone
import uuid

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.money import MONEY_PRECISION, MONEY_SCALE
from app.db.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    created_at = Column(DateTime, default=utc_now)

    parent = relationship("Category", remote_side=[id])
    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    normalized_name = Column(String(255), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    brand = Column(String(100), nullable=True)
    specifications = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    category = relationship("Category", back_populates="products")
    raw_listings = relationship("RawListing", back_populates="product")
    price_history = relationship("PriceHistory", back_populates="product")


class RawListing(Base):
    __tablename__ = "raw_listings"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(50), nullable=False)
    original_name = Column(String(255), nullable=False)
    price = Column(Numeric(MONEY_PRECISION, MONEY_SCALE), nullable=False)
    seller_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    location = Column(String(100), nullable=True)
    url = Column(String(500), nullable=True)
    raw_data = Column(JSON, nullable=True)
    is_suspicious = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)

    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    product = relationship("Product", back_populates="raw_listings")
    seller = relationship("Supplier", back_populates="listings")


class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    price = Column(Numeric(MONEY_PRECISION, MONEY_SCALE), nullable=False)
    recorded_at = Column(DateTime, default=utc_now)
    source = Column(String(50), nullable=True)

    product = relationship("Product", back_populates="price_history")


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    source = Column(String(50), nullable=False)
    location = Column(String(100), nullable=True)
    contact_info = Column(JSON, nullable=True)
    trust_score = Column(Float, default=50.0)
    total_listings = Column(Integer, default=0)
    successful_transactions = Column(Integer, default=0)
    created_at = Column(DateTime, default=utc_now)

    listings = relationship("RawListing", back_populates="seller")


class SuspiciousListing(Base):
    __tablename__ = "suspicious_listings"

    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("raw_listings.id"), nullable=False)
    reason = Column(Text, nullable=False)
    severity = Column(String(20), default="low")
    reviewed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint("job_type", "idempotency_key", name="uq_jobs_type_idempotency"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_type = Column(String(50), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="queued", index=True)
    payload = Column(JSON, nullable=False, default=dict)
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    idempotency_key = Column(String(255), nullable=True)
    attempts = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=3)
    available_at = Column(DateTime, nullable=False, default=utc_now, index=True)
    lease_expires_at = Column(DateTime, nullable=True, index=True)
    worker_id = Column(String(255), nullable=True)
    cancel_requested = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
