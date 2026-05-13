# MarketSense NG - API Endpoints Reference Guide

> Base URL: `https://api.marketsense.ng/v1`

---

## Table of Contents

- [Products](#products)
- [Market Data](#market-data)
- [Suppliers](#suppliers)
- [Analytics](#analytics)
- [Data Ingestion (Internal)](#data-ingestion-internal)

---

## Products

### GET /api/products

List all products with optional filtering and pagination.

#### Query Parameters

| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| `page` | integer | No | Page number | 1 |
| `limit` | integer | No | Items per page (max 100) | 20 |
| `category` | string | No | Filter by category | - |
| `source` | string | No | Filter by data source | - |
| `min_price` | float | No | Minimum price | - |
| `max_price` | float | No | Maximum price | - |
| `sort_by` | string | No | Sort field (`price`, `name`, `updated_at`) | `updated_at` |
| `sort_order` | string | No | Sort direction (`asc`, `desc`) | `desc` |

#### Authentication

Requires `Bearer` token in Authorization header.

```http
Authorization: Bearer <your_api_token>
```

#### Response (200 OK)

```json
{
  "data": [
    {
      "id": "prod_abc123",
      "name": "Dell UltraSharp 27 Monitor",
      "category": "Electronics",
      "brand": "Dell",
      "current_price": 449.99,
      "currency": "USD",
      "source": "amazon",
      "url": "https://amazon.com/dp/B09KY7FQHP",
      "last_updated": "2026-05-10T14:30:00Z",
      "trust_score": 0.92
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total_items": 1543,
    "total_pages": 78
  }
}
```

#### Error Responses

| Status | Description |
|--------|-------------|
| 401 | Unauthorized - Invalid or missing token |
| 403 | Forbidden - Insufficient permissions |
| 422 | Validation Error - Invalid query parameters |

---

### GET /api/products/{id}

Get detailed information about a specific product.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Product UUID |

#### Authentication

Requires `Bearer` token.

#### Response (200 OK)

```json
{
  "id": "prod_abc123",
  "name": "Dell UltraSharp 27 Monitor",
  "category": "Electronics",
  "brand": "Dell",
  "model": "U2722D",
  "description": "27 inch QHD USB-C Hub Monitor",
  "specifications": {
    "resolution": "2560x1440",
    "refresh_rate": "60Hz",
    "panel_type": "IPS",
    "response_time": "5ms"
  },
  "current_price": 449.99,
  "currency": "USD",
  "price_history": [
    {"date": "2026-05-10", "price": 449.99},
    {"date": "2026-05-09", "price": 479.99},
    {"date": "2026-05-08", "price": 469.99}
  ],
  "sources": [
    {"source": "amazon", "price": 449.99, "trust_score": 0.92},
    {"source": "newegg", "price": 459.99, "trust_score": 0.88}
  ],
  "last_updated": "2026-05-10T14:30:00Z"
}
```

#### Error Responses

| Status | Description |
|--------|-------------|
| 404 | Product not found |

---

### GET /api/products/search

Search products by name, brand, or keywords.

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `q` | string | Yes | Search query (min 2 characters) |
| `category` | string | No | Filter by category |
| `limit` | integer | No | Max results (default 20, max 100) |

#### Authentication

Requires `Bearer` token.

#### Response (200 OK)

```json
{
  "query": "dell monitor",
  "results": [
    {
      "id": "prod_abc123",
      "name": "Dell UltraSharp 27 Monitor",
      "category": "Electronics",
      "brand": "Dell",
      "current_price": 449.99,
      "highlight": "Dell <em>UltraSharp</em> 27 Monitor"
    },
    {
      "id": "prod_def456",
      "name": "Dell S2722DQM Monitor",
      "category": "Electronics",
      "brand": "Dell",
      "current_price": 329.99,
      "highlight": "Dell <em>S2722DQM</em> Monitor"
    }
  ],
  "total_results": 42
}
```

#### Error Responses

| Status | Description |
|--------|-------------|
| 400 | Bad Request - Query too short |
| 422 | Validation Error |

---

## Market Data

### GET /api/market/{product_name}

Get current market prices for a specific product across all sources.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `product_name` | string | Product name (URL encoded) |

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `region` | string | No | Filter by region (us, eu, uk) |

#### Authentication

Requires `Bearer` token.

#### Response (200 OK)

```json
{
  "product_name": "iphone 15 pro max",
  "searched_at": "2026-05-10T15:00:00Z",
  "prices": [
    {
      "source": "amazon",
      "price": 1199.00,
      "currency": "USD",
      "availability": "in_stock",
      "seller": "Amazon.com",
      "url": "https://amazon.com/iphone15",
      "trust_score": 0.95,
      "last_updated": "2026-05-10T14:45:00Z"
    },
    {
      "source": "bestbuy",
      "price": 1199.99,
      "currency": "USD",
      "availability": "in_stock",
      "seller": "Best Buy",
      "url": "https://bestbuy.com/iphone15",
      "trust_score": 0.93,
      "last_updated": "2026-05-10T14:30:00Z"
    },
    {
      "source": "ebay",
      "price": 1099.00,
      "currency": "USD",
      "availability": "limited",
      "seller": "TechDeals_US",
      "url": "https://ebay.com/iphone15",
      "trust_score": 0.78,
      "last_updated": "2026-05-10T13:20:00Z"
    }
  ],
  "statistics": {
    "lowest_price": 1099.00,
    "highest_price": 1299.00,
    "average_price": 1165.99,
    "median_price": 1199.00
  }
}
```

#### Error Responses

| Status | Description |
|--------|-------------|
| 404 | Product not found in market data |

---

### GET /api/market/compare

Compare prices across multiple sources for benchmarking.

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `products` | string | Yes | Comma-separated product IDs |
| `sources` | string | No | Comma-separated sources to compare |

#### Authentication

Requires `Bearer` token.

#### Request Example

```
GET /api/market/compare?products=prod_abc123,prod_def456&sources=amazon,newegg
```

#### Response (200 OK)

```json
{
  "comparison_date": "2026-05-10T15:00:00Z",
  "products": [
    {
      "product_id": "prod_abc123",
      "product_name": "Dell UltraSharp 27 Monitor",
      "prices_by_source": {
        "amazon": {"price": 449.99, "trust_score": 0.92},
        "newegg": {"price": 459.99, "trust_score": 0.88},
        "bestbuy": {"price": 469.99, "trust_score": 0.90}
      },
      "best_price": {
        "source": "amazon",
        "price": 449.99,
        "savings_vs_avg": 4.2
      }
    },
    {
      "product_id": "prod_def456",
      "product_name": "Dell S2722DQM Monitor",
      "prices_by_source": {
        "amazon": {"price": 329.99, "trust_score": 0.91},
        "newegg": {"price": 319.99, "trust_score": 0.86}
      },
      "best_price": {
        "source": "newegg",
        "price": 319.99,
        "savings_vs_avg": 3.1
      }
    }
  ]
}
```

#### Error Responses

| Status | Description |
|--------|-------------|
| 400 | Missing required products parameter |
| 422 | Invalid product ID format |

---

### GET /api/market/trends

Get historical price trends over specified time period.

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `product_id` | string | Yes | Product UUID |
| `period` | string | No | Time period (`7d`, `30d`, `90d`, `1y`) | `30d` |
| `interval` | string | No | Data interval (`daily`, `weekly`) | `daily` |

#### Authentication

Requires `Bearer` token.

#### Response (200 OK)

```json
{
  "product_id": "prod_abc123",
  "product_name": "Dell UltraSharp 27 Monitor",
  "period": "30d",
  "currency": "USD",
  "trend_data": [
    {"date": "2026-05-10", "price": 449.99, "volume": 45},
    {"date": "2026-05-09", "price": 479.99, "volume": 32},
    {"date": "2026-05-08", "price": 469.99, "volume": 28},
    {"date": "2026-05-07", "price": 459.99, "volume": 51}
  ],
  "analysis": {
    "current_vs_30d_avg": -5.2,
    "trend_direction": "decreasing",
    "volatility": "low",
    "best_day_to_buy": "Friday",
    "price_forecast": [
      {"date": "2026-05-11", "predicted_price": 445.00},
      {"date": "2026-05-12", "predicted_price": 442.00}
    ]
  }
}
```

#### Error Responses

| Status | Description |
|--------|-------------|
| 404 | Product not found |
| 400 | Invalid period or interval |

---

## Suppliers

### GET /api/suppliers

List all registered suppliers with filtering.

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | integer | No | Page number |
| `limit` | integer | No | Items per page (max 100) |
| `category` | string | No | Filter by category |
| `min_trust_score` | float | No | Minimum trust score (0-1) |
| `verified` | boolean | No | Filter verified suppliers only |

#### Authentication

Requires `Bearer` token.

#### Response (200 OK)

```json
{
  "data": [
    {
      "id": "sup_xyz789",
      "name": "TechWorld Distributors",
      "category": "Electronics",
      "verified": true,
      "trust_score": 0.94,
      "total_listings": 1247,
      "avg_response_time_hours": 2.3,
      "last_active": "2026-05-10T14:00:00Z"
    },
    {
      "id": "sup_uvw012",
      "name": "GlobalParts Inc",
      "category": "Computer Parts",
      "verified": true,
      "trust_score": 0.88,
      "total_listings": 892,
      "avg_response_time_hours": 4.1,
      "last_active": "2026-05-10T12:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total_items": 156,
    "total_pages": 8
  }
}
```

---

### GET /api/suppliers/{id}

Get detailed supplier information including trust score breakdown.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Supplier UUID |

#### Authentication

Requires `Bearer` token.

#### Response (200 OK)

```json
{
  "id": "sup_xyz789",
  "name": "TechWorld Distributors",
  "legal_name": "TechWorld Distributors LLC",
  "category": "Electronics",
  "verified": true,
  "verified_at": "2025-11-15T10:00:00Z",
  "contact": {
    "email": "support@techworld.com",
    "phone": "+1-555-0123",
    "website": "https://techworld.com"
  },
  "trust_score": 0.94,
  "trust_breakdown": {
    "delivery_reliability": 0.96,
    "product_accuracy": 0.92,
    "response_quality": 0.94,
    "pricing_consistency": 0.95,
    "customer_satisfaction": 0.93
  },
  "statistics": {
    "total_listings": 1247,
    "active_listings": 1156,
    "total_sales": 45672,
    "avg_rating": 4.7,
    "review_count": 892
  },
  "last_active": "2026-05-10T14:00:00Z"
}
```

#### Error Responses

| Status | Description |
|--------|-------------|
| 404 | Supplier not found |

---

### GET /api/suppliers/{id}/listings

Get all product listings from a specific supplier.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Supplier UUID |

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | integer | No | Page number |
| `limit` | integer | No | Items per page (max 100) |
| `category` | string | No | Filter by category |
| `in_stock` | boolean | No | Filter in-stock items only |

#### Authentication

Requires `Bearer` token.

#### Response (200 OK)

```json
{
  "supplier_id": "sup_xyz789",
  "supplier_name": "TechWorld Distributors",
  "listings": [
    {
      "listing_id": "lst_001",
      "product_name": "Dell UltraSharp 27 Monitor",
      "sku": "DELL-U2722D",
      "price": 429.99,
      "currency": "USD",
      "stock_status": "in_stock",
      "stock_quantity": 50,
      "moq": 1,
      "lead_time_days": 2,
      "url": "https://techworld.com/products/dell-u2722d",
      "last_updated": "2026-05-10T14:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total_items": 1156,
    "total_pages": 58
  }
}
```

---

## Analytics

### GET /api/analytics/summary

Get dashboard summary with key metrics.

#### Authentication

Requires `Bearer` token with analytics scope.

#### Response (200 OK)

```json
{
  "generated_at": "2026-05-10T15:00:00Z",
  "overview": {
    "total_products": 15432,
    "total_suppliers": 156,
    "total_listings": 89342,
    "active_listings": 76234
  },
  "price_metrics": {
    "avg_product_price": 345.67,
    "avg_listing_price": 298.45,
    "price_change_24h": -0.8
  },
  "data_health": {
    "listings_last_24h": 1245,
    "listings_last_7d": 8932,
    "data_freshness_avg_minutes": 15
  },
  "alerts": {
    "suspicious_prices_count": 23,
    "price_spike_count": 5,
    "out_of_stock_spike": 12
  }
}
```

---

### GET /api/analytics/categories

Get category breakdown with pricing distribution.

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `period` | string | No | Time period (`7d`, `30d`, `90d`) | `30d` |

#### Authentication

Requires `Bearer` token.

#### Response (200 OK)

```json
{
  "generated_at": "2026-05-10T15:00:00Z",
  "period": "30d",
  "categories": [
    {
      "name": "Electronics",
      "product_count": 4521,
      "avg_price": 456.78,
      "price_range": {"min": 19.99, "max": 3499.99},
      "listing_count": 28342,
      "supplier_count": 45,
      "trending": true,
      "growth_rate": 5.2
    },
    {
      "name": "Computer Parts",
      "product_count": 3245,
      "avg_price": 234.56,
      "price_range": {"min": 9.99, "max": 1999.99},
      "listing_count": 18765,
      "supplier_count": 38,
      "trending": true,
      "growth_rate": 3.8
    }
  ]
}
```

---

### GET /api/analytics/suspicious

Get count and details of suspicious pricing activity.

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `severity` | string | No | Filter by severity (`low`, `medium`, `high`) |
| `page` | integer | No | Page number |
| `limit` | integer | No | Items per page |

#### Authentication

Requires `Bearer` token with admin scope.

#### Response (200 OK)

```json
{
  "generated_at": "2026-05-10T15:00:00Z",
  "summary": {
    "total_count": 23,
    "high_severity": 5,
    "medium_severity": 12,
    "low_severity": 6
  },
  "suspicious_items": [
    {
      "id": "susp_001",
      "product_id": "prod_abc123",
      "product_name": "NVIDIA RTX 4090",
      "suspicious_price": 899.99,
      "expected_price_range": {"min": 1599.99, "max": 1799.99},
      "deviation": -44.4,
      "severity": "high",
      "source": "unverified_seller",
      "detected_at": "2026-05-10T14:30:00Z",
      "reason": "Price significantly below market benchmark"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total_items": 23,
    "total_pages": 2
  }
}
```

---

## Data Ingestion (Internal)

> **Note**: These endpoints are for internal use only. Require internal service authentication.

### POST /api/ingest/listings

Bulk add raw product listings from external sources.

#### Authentication

Requires `X-Internal-Key` header with internal API key.

```http
X-Internal-Key: <internal_service_key>
```

#### Request Body

```json
{
  "source": "amazon",
  "source_id": "src_amazon_001",
  "listings": [
    {
      "external_id": "B09KY7FQHP",
      "name": "Dell UltraSharp 27 Monitor",
      "brand": "Dell",
      "category": "Electronics",
      "price": 449.99,
      "currency": "USD",
      "url": "https://amazon.com/dp/B09KY7FQHP",
      "seller": "Amazon.com",
      "in_stock": true,
      "raw_data": {
        "asin": "B09KY7FQHP",
        "title": "Dell UltraSharp 27 USB-C Hub Monitor...",
        "rating": 4.6
      }
    }
  ],
  "ingested_at": "2026-05-10T15:00:00Z"
}
```

#### Response (201 Created)

```json
{
  "status": "success",
  "ingested_count": 150,
  "errors": [],
  "processing_time_ms": 234
}
```

#### Error Responses

| Status | Description |
|--------|-------------|
| 401 | Unauthorized - Invalid internal key |
| 413 | Payload Too Large - Max 5000 listings per request |
| 422 | Validation Error |

---

### POST /api/ingest/normalize

Run the normalization pipeline on ingested data.

#### Authentication

Requires `X-Internal-Key` header.

#### Request Body

```json
{
  "batch_id": "batch_20260510_001",
  "options": {
    "recalculate_prices": true,
    "update_benchmarks": true,
    "detect_duplicates": true,
    "enrich_metadata": true
  }
}
```

#### Response (200 OK)

```json
{
  "status": "success",
  "batch_id": "batch_20260510_001",
  "processed": {
    "total": 150,
    "normalized": 148,
    "duplicates_merged": 5,
    "failed": 2
  },
  "normalization_stats": {
    "price_standardized": 148,
    "category_mapped": 145,
    "brand_normalized": 147,
    "specs_extracted": 92
  },
  "processing_time_ms": 1542
}
```

---

### POST /api/ingest/benchmark

Recalculate price benchmarks for affected products.

#### Authentication

Requires `X-Internal-Key` header.

#### Request Body

```json
{
  "scope": "recent",
  "recent_hours": 24,
  "product_ids": ["prod_abc123", "prod_def456"],
  "force_recalculation": false
}
```

#### Response (200 OK)

```json
{
  "status": "success",
  "recalculated": {
    "benchmarks": 342,
    "price_ranges": 338,
    "trust_scores": 342
  },
  "processing_time_ms": 892
}
```

---

## Authentication

### API Key Authentication

All endpoints (except internal) require a Bearer token:

```http
Authorization: Bearer <your_api_token>
```

### Internal Service Authentication

Internal endpoints use a different header:

```http
X-Internal-Key: <internal_service_key>
```

### Token Scopes

| Scope | Description |
|-------|-------------|
| `read:products` | Read product data |
| `read:market` | Read market data |
| `read:suppliers` | Read supplier data |
| `read:analytics` | Read analytics |
| `write:ingest` | Internal data ingestion |
| `admin` | Full access |

---

## Error Response Format

All errors follow this format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid query parameter: page must be positive",
    "details": {
      "field": "page",
      "constraint": "must_be_positive"
    }
  }
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| `UNAUTHORIZED` | Invalid or missing authentication |
| `FORBIDDEN` | Insufficient permissions |
| `NOT_FOUND` | Resource not found |
| `VALIDATION_ERROR` | Invalid request parameters |
| `RATE_LIMITED` | Too many requests |
| `INTERNAL_ERROR` | Server error |
| `SERVICE_UNAVAILABLE` | External service unavailable |

---

## Rate Limits

| Endpoint Category | Limit |
|-------------------|-------|
| Products | 1000 req/min |
| Market Data | 500 req/min |
| Suppliers | 500 req/min |
| Analytics | 100 req/min |
| Internal | 100 req/min |

---

*Last Updated: May 2026 | Version: 1.0*