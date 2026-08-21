import hashlib
from collections import Counter
from collections.abc import Iterable

from sqlalchemy import select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import RawListing, Supplier
from app.schemas import BulkListingsInput, ListingInput

SUPPLIER_LOOKUP_BATCH_SIZE = 400
LISTING_INSERT_BATCH_SIZE = 300


async def ingest_listings(
    db: AsyncSession,
    payload: BulkListingsInput,
    *,
    request_key: str | None = None,
) -> int:
    """Persist listings with DB-enforced supplier and listing idempotency."""
    supplier_keys = list(dict.fromkeys((item.seller_name, item.seller_source) for item in payload.listings))
    suppliers = await _load_suppliers(db, supplier_keys)
    missing = [key for key in supplier_keys if key not in suppliers]
    if missing:
        await _insert_missing_suppliers(db, payload, missing)
        suppliers = await _load_suppliers(db, supplier_keys)

    values: list[dict] = []
    for index, listing in enumerate(payload.listings):
        seller = suppliers[(listing.seller_name, listing.seller_source)]
        values.append(
            {
                "source": listing.source,
                "original_name": listing.original_name,
                "price": listing.price,
                "seller_id": seller.id,
                "location": listing.location,
                "url": listing.url,
                "ingestion_key": _ingestion_key(listing, request_key=request_key, index=index),
                "is_suspicious": False,
            }
        )

    inserted_by_supplier: Counter[int] = Counter()
    for chunk in _chunks(values, LISTING_INSERT_BATCH_SIZE):
        statement = _dialect_insert(db, RawListing).values(chunk)
        statement = statement.on_conflict_do_nothing(index_elements=["ingestion_key"]).returning(RawListing.seller_id)
        result = await db.execute(statement)
        inserted_by_supplier.update(int(seller_id) for seller_id in result.scalars().all())

    for supplier in suppliers.values():
        added = inserted_by_supplier.get(int(supplier.id), 0)
        if added:
            supplier.total_listings = int(supplier.total_listings or 0) + added

    await db.commit()
    return sum(inserted_by_supplier.values())


async def _insert_missing_suppliers(
    db: AsyncSession,
    payload: BulkListingsInput,
    missing: list[tuple[str, str]],
) -> None:
    first_by_key: dict[tuple[str, str], ListingInput] = {}
    for listing in payload.listings:
        first_by_key.setdefault((listing.seller_name, listing.seller_source), listing)

    values = [
        {
            "name": first_by_key[key].seller_name,
            "source": first_by_key[key].seller_source,
            "location": first_by_key[key].location,
            "total_listings": 0,
            "successful_transactions": 0,
            "trust_score": 50.0,
        }
        for key in missing
    ]
    statement = _dialect_insert(db, Supplier).values(values)
    statement = statement.on_conflict_do_nothing(index_elements=["name", "source"])
    await db.execute(statement)
    await db.flush()


async def _load_suppliers(db: AsyncSession, supplier_keys: list[tuple[str, str]]) -> dict[tuple[str, str], Supplier]:
    suppliers: dict[tuple[str, str], Supplier] = {}
    for chunk in _chunks(supplier_keys, SUPPLIER_LOOKUP_BATCH_SIZE):
        result = await db.execute(select(Supplier).where(tuple_(Supplier.name, Supplier.source).in_(chunk)))
        for supplier in result.scalars().all():
            suppliers.setdefault((supplier.name, supplier.source), supplier)
    return suppliers


def _ingestion_key(listing: ListingInput, *, request_key: str | None, index: int) -> str | None:
    if listing.external_id:
        identity = f"external\0{listing.source}\0{listing.seller_source}\0{listing.external_id.strip()}"
    elif request_key:
        identity = f"request\0{request_key.strip()}\0{index}"
    else:
        return None
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def _dialect_insert(db: AsyncSession, model):
    dialect = db.get_bind().dialect.name
    if dialect == "postgresql":
        from sqlalchemy.dialects.postgresql import insert
        return insert(model)
    if dialect == "sqlite":
        from sqlalchemy.dialects.sqlite import insert
        return insert(model)
    raise RuntimeError(f"Unsupported ingestion database dialect: {dialect}")


def _chunks[T](items: list[T], size: int) -> Iterable[list[T]]:
    for index in range(0, len(items), size):
        yield items[index : index + size]
