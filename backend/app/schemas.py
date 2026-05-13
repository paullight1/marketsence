from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProductSummary(BaseModel):
    id: int
    name: str
    category: str | None = None
    brand: str | None = None
    avg_price: float = 0
    min_price: float = 0
    max_price: float = 0
    listings_count: int = 0
    last_updated: datetime | None = None


class ProductDetail(BaseModel):
    id: int
    name: str
    category: str | None = None
    brand: str | None = None
    specifications: dict | None = None


class ProductSearchResult(BaseModel):
    id: int
    name: str


class SupplierSummary(BaseModel):
    id: int
    name: str
    source: str
    location: str | None = None
    trust_score: float
    total_listings: int
    avg_price: float = 0
    suspicious_count: int = 0


class SupplierDetail(BaseModel):
    id: int
    name: str
    source: str
    location: str | None = None
    contact_info: dict | None = None
    trust_score: float
    total_listings: int
    successful_transactions: int


class SupplierListingItem(BaseModel):
    id: int
    product_name: str
    price: float
    source: str
    location: str | None = None
    date: datetime | None = None
    is_suspicious: bool


class MarketSnapshot(BaseModel):
    product_id: int
    product_name: str
    average_price: float
    market_range: list[float]
    total_listings: int
    suspicious_listings: int


class SourceComparison(BaseModel):
    source: str
    avg_price: float
    min_price: float
    max_price: float
    listings_count: int


class TrendPoint(BaseModel):
    date: str
    avg_price: float


class DashboardSummary(BaseModel):
    total_products: int
    total_suppliers: int
    total_listings: int
    suspicious_prices: int
    avg_trust_score: float


class CategoryBreakdownItem(BaseModel):
    category: str
    count: int


class SuspiciousSummary(BaseModel):
    total_unreviewed: int
    high_severity: int
    medium_severity: int


class ListingInput(BaseModel):
    source: str = Field(min_length=2, max_length=50)
    original_name: str = Field(min_length=3, max_length=255)
    price: float = Field(gt=0)
    seller_name: str = Field(min_length=2, max_length=255)
    seller_source: str = Field(min_length=2, max_length=50)
    location: str | None = Field(default=None, max_length=100)
    url: str | None = Field(default=None, max_length=500)


class BulkListingsInput(BaseModel):
    listings: list[ListingInput] = Field(min_length=1, max_length=5000)


class IngestResult(BaseModel):
    added: int
    message: str


class ScrapeRequest(BaseModel):
    url: str = Field(pattern=r"^https?://", max_length=500)
    source: str = Field(default="Website", min_length=2, max_length=50)
    seller_name: str | None = Field(default=None, max_length=255)
    seller_source: str = Field(default="website", min_length=2, max_length=50)
    location: str | None = Field(default=None, max_length=100)
    max_items: int = Field(default=25, ge=1, le=100)
    ingest: bool = True
    context_keywords: list[str] = Field(
        default_factory=lambda: [
            "price",
            "market",
            "shop",
            "store",
            "supplier",
            "wholesale",
            "retail",
            "product",
            "nigeria",
            "naira",
        ],
        max_length=25,
    )


class ScrapedListingPreview(BaseModel):
    source: str
    original_name: str
    price: float
    seller_name: str
    seller_source: str
    location: str | None = None
    url: str | None = None


class ScrapeIngestResult(BaseModel):
    scraped: int
    ingested: int
    listings: list[ScrapedListingPreview]
    message: str


class CleanCsvResult(BaseModel):
    file_id: str
    download_filename: str
    rows_before: int
    rows_after: int
    duplicates_removed: int
    columns: list[str]
    detected_name_column: str | None = None
    detected_price_column: str | None = None
    detected_date_column: str | None = None
    missing_before: dict[str, int]
    missing_after: dict[str, int]
    preview: list[dict]
    message: str


class OpsMetric(BaseModel):
    label: str
    value: str
    tone: str = "default"


class OpsTask(BaseModel):
    id: str
    title: str
    stage: str
    owner: str
    source: str
    eta: str
    progress: int
    listings: int
    note: str


class OpsReviewAlert(BaseModel):
    id: str
    product: str
    issue: str
    severity: str
    delta: float


class OpsRecentListing(BaseModel):
    id: int
    product_name: str
    price: float
    seller: str
    source: str
    location: str | None = None
    is_suspicious: bool


class OpsOverview(BaseModel):
    queue_metrics: list[OpsMetric]
    tasks: list[OpsTask]
    review_alerts: list[OpsReviewAlert]
    recent_listings: list[OpsRecentListing]


class NormalizationResult(BaseModel):
    message: str
    linked_count: int
    new_suggestions: int
    status: str


class BenchmarkResult(BaseModel):
    message: str
    updated_products: int
    status: str


class HealthResponse(BaseModel):
    status: str


class RootResponse(BaseModel):
    message: str
    status: str


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
