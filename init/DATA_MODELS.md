# MarketSense NG - Database Schema Guide

## Overview

MarketSense NG uses PostgreSQL 15+ with the following core entities:

- **Products** - Normalized product catalog
- **Raw Listings** - Original scraped listing data
- **Price History** - Historical price tracking
- **Suppliers** - Seller/merchant information
- **Suspicious Prices** - Flagged anomalies
- **Categories** - Hierarchical product categories

---

## Entity Relationship Diagram

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│  Categories  │       │   Products   │       │  Suppliers   │
├──────────────┤       ├──────────────┤       ├──────────────┤
│ id (PK)      │──┐    │ id (PK)      │       │ id (PK)      │
│ name         │  │    │ category_id  │──┐    │ name         │
│ parent_id    │──┘    │ normalized_  │  │    │ source       │
│              │       │   name       │  │    │ trust_score  │
└──────────────┘       │ brand        │  │    │              │
                       │ specs (jsonb)│  │    └──────┬───────┘
                       └──────┬───────┘  │           │
                              │          │           │
                       ┌──────┴───────┐  │    ┌──────┴───────┐
                       │ Raw Listings │  │    │ Raw Listings │
                       ├──────────────┤  │    │ supplier_id  │
                       │ id (PK)      │  │    │ (FK)         │
                       │ product_id   │──┘    └──────────────┘
                       │ supplier_id  │
                       │ source       │
                       │ price        │
                       │ location     │
                       │ url          │
                       │ raw_data     │
                       └──────┬───────┘
                              │
                       ┌──────┴───────┐
                       │ Price History│
                       ├──────────────┤
                       │ id (PK)      │
                       │ product_id   │──┐
                       │ supplier_id  │  │
                       │ price        │  │
                       │ recorded_at  │  │
                       └──────────────┘  │
                                          │
                       ┌──────────────────┴───┐
                       │  Suspicious Prices   │
                       ├──────────────────────┤
                       │ id (PK)              │
                       │ listing_id (FK)      │
                       │ reason               │
                       │ severity             │
                       │ reviewed             │
                       └──────────────────────┘
```

---

## 1. Categories

Hierarchical product categorization with self-referencing parent_id.

### Table Definition

```sql
CREATE TABLE categories (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    slug            VARCHAR(255) UNIQUE NOT NULL,
    parent_id       INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    description     TEXT,
    icon            VARCHAR(100),
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Self-referencing index for hierarchy queries
CREATE INDEX idx_categories_parent_id ON categories(parent_id);
CREATE INDEX idx_categories_slug ON categories(slug);
```

### Example Hierarchy

| id | name     | parent_id | path                |
|----|----------|-----------|---------------------|
| 1  | Building Materials | NULL   | Building Materials |
| 2  | Cement    | 1         | Building Materials > Cement |
| 3  | Dangote   | 2         | Building Materials > Cement > Dangote |
| 4  | Electronics | NULL   | Electronics         |
| 5  | Laptops   | 4         | Electronics > Laptops |

### Sample Queries

**Get full category path:**
```sql
WITH RECURSIVE category_tree AS (
    SELECT id, name, parent_id, name::TEXT as path
    FROM categories
    WHERE parent_id IS NULL
    
    UNION ALL
    
    SELECT c.id, c.name, c.parent_id, ct.path || ' > ' || c.name
    FROM categories c
    JOIN category_tree ct ON c.parent_id = ct.id
)
SELECT * FROM category_tree ORDER BY path;
```

**Get immediate subcategories:**
```sql
SELECT * FROM categories WHERE parent_id = 1;
```

**Get all descendants of a category:**
```sql
WITH RECURSIVE descendants AS (
    SELECT id FROM categories WHERE id = 2
    UNION ALL
    SELECT c.id FROM categories c
    JOIN descendants d ON c.parent_id = d.id
)
SELECT * FROM descendants;
```

---

## 2. Products

Normalized product catalog - deduplicated canonical product records.

### Table Definition

```sql
CREATE TABLE products (
    id                  SERIAL PRIMARY KEY,
    normalized_name     VARCHAR(500) NOT NULL,
    category_id         INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    brand               VARCHAR(255),
    model               VARCHAR(255),
    specifications      JSONB DEFAULT '{}',
    image_urls          TEXT[],
    search_terms        TEXT[],
    is_active           BOOLEAN DEFAULT TRUE,
    verified_at         TIMESTAMPTZ,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    
    -- Ensure unique normalized names per category
    UNIQUE(normalized_name, category_id)
);

-- Indexes for common lookups
CREATE INDEX idx_products_category_id ON products(category_id);
CREATE INDEX idx_products_brand ON products(brand);
CREATE INDEX idx_products_normalized_name_trgm ON products USING GIN (normalized_name gin_trgm_ops);
CREATE INDEX idx_products_search_terms ON products USING GIN (search_terms);
CREATE INDEX idx_products_specs ON products USING GIN (specifications);
```

### JSONB Specifications Example

```json
{
    "weight": "50kg",
    "grade": "42.5R",
    "type": "Portland Limestone Cement",
    "manufacturing_date": "2024-01",
    "expiry_date": "2026-01",
    "certifications": ["SON", "ISO 9001"],
    "packaging": "bag"
}
```

### Sample Queries

**Search products by name (fuzzy match):**
```sql
SELECT p.*, c.name as category_name
FROM products p
LEFT JOIN categories c ON p.category_id = c.id
WHERE p.normalized_name % 'dangote cement 50kg'
ORDER BY similarity(p.normalized_name, 'dangote cement 50kg') DESC
LIMIT 20;
```

**Find products by specification:**
```sql
SELECT * FROM products
WHERE specifications @> '{"grade": "42.5R"}'
  AND specifications @> '{"weight": "50kg"}';
```

**Get products with latest prices:**
```sql
SELECT 
    p.id,
    p.normalized_name,
    p.brand,
    MIN(rl.price) as min_price,
    MAX(rl.price) as max_price,
    COUNT(rl.id) as listing_count
FROM products p
JOIN raw_listings rl ON rl.product_id = p.id
WHERE rl.is_active = TRUE
GROUP BY p.id, p.normalized_name, p.brand
ORDER BY p.normalized_name;
```

---

## 3. Raw Listings

Original scraped listing data from various sources.

### Table Definition

```sql
CREATE TABLE raw_listings (
    id              SERIAL PRIMARY KEY,
    product_id      INTEGER REFERENCES products(id) ON DELETE SET NULL,
    supplier_id     INTEGER REFERENCES suppliers(id) ON DELETE SET NULL,
    source          VARCHAR(100) NOT NULL,
    original_name   VARCHAR(500) NOT NULL,
    price           DECIMAL(12, 2) NOT NULL CHECK (price >= 0),
    currency        VARCHAR(3) DEFAULT 'NGN',
    location        VARCHAR(255),
    seller          VARCHAR(255),
    url             TEXT NOT NULL,
    image_url       TEXT,
    availability    VARCHAR(50) DEFAULT 'in_stock',
    raw_data        JSONB DEFAULT '{}',
    is_active       BOOLEAN DEFAULT TRUE,
    last_checked_at TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_listings_product_id ON raw_listings(product_id);
CREATE INDEX idx_listings_supplier_id ON raw_listings(supplier_id);
CREATE INDEX idx_listings_source ON raw_listings(source);
CREATE INDEX idx_listings_price ON raw_listings(price);
CREATE INDEX idx_listings_location ON raw_listings(location);
CREATE INDEX idx_listings_created_at ON raw_listings(created_at DESC);
CREATE INDEX idx_listings_url ON raw_listings(url) WHERE is_active = TRUE;
CREATE INDEX idx_listings_product_source ON raw_listings(product_id, source);
```

### Availability Values

- `in_stock` - Available for purchase
- `out_of_stock` - Currently unavailable
- `pre_order` - Available for pre-order
- `limited` - Limited stock
- `unknown` - Status not confirmed

### Sample Queries

**Get all listings for a product with supplier info:**
```sql
SELECT 
    rl.*,
    s.name as supplier_name,
    s.trust_score
FROM raw_listings rl
LEFT JOIN suppliers s ON rl.supplier_id = s.id
WHERE rl.product_id = 123
  AND rl.is_active = TRUE
ORDER BY rl.price ASC;
```

**Compare prices across sources:**
```sql
SELECT 
    source,
    COUNT(*) as listings,
    AVG(price) as avg_price,
    MIN(price) as min_price,
    MAX(price) as max_price
FROM raw_listings
WHERE product_id = 123
  AND is_active = TRUE
GROUP BY source;
```

**Find newest listings:**
```sql
SELECT * FROM raw_listings
WHERE is_active = TRUE
ORDER BY created_at DESC
LIMIT 50;
```

---

## 4. Price History

Tracks price changes over time for trend analysis.

### Table Definition

```sql
CREATE TABLE price_history (
    id              SERIAL PRIMARY KEY,
    product_id      INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    supplier_id     INTEGER REFERENCES suppliers(id) ON DELETE SET NULL,
    source          VARCHAR(100) NOT NULL,
    price           DECIMAL(12, 2) NOT NULL CHECK (price >= 0),
    recorded_at      TIMESTAMPTZ DEFAULT NOW(),
    
    -- Composite index for time-series queries
    UNIQUE(product_id, supplier_id, source, recorded_at)
);

-- Indexes optimized for time-series data
CREATE INDEX idx_price_history_product_id ON price_history(product_id);
CREATE INDEX idx_price_history_recorded_at ON price_history(recorded_at DESC);
CREATE INDEX idx_price_history_product_time ON price_history(product_id, recorded_at DESC);
CREATE INDEX idx_price_history_supplier_time ON price_history(supplier_id, recorded_at DESC);
```

### Sample Queries

**Get price trend for a product (last 30 days):**
```sql
SELECT 
    DATE(recorded_at) as date,
    AVG(price) as avg_price,
    MIN(price) as min_price,
    MAX(price) as max_price,
    COUNT(*) as observations
FROM price_history
WHERE product_id = 123
  AND recorded_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(recorded_at)
ORDER BY date;
```

**Get price change summary:**
```sql
WITH latest AS (
    SELECT price, product_id, supplier_id, source,
           ROW_NUMBER() OVER (PARTITION BY product_id, supplier_id, source 
                              ORDER BY recorded_at DESC) as rn
    FROM price_history
),
previous AS (
    SELECT price, product_id, supplier_id, source,
           ROW_NUMBER() OVER (PARTITION BY product_id, supplier_id, source 
                              ORDER BY recorded_at DESC) as rn
    FROM price_history
)
SELECT 
    l.product_id,
    l.supplier_id,
    l.source,
    p.price as previous_price,
    l.price as current_price,
    l.price - p.price as price_change,
    ROUND((l.price - p.price) / NULLIF(p.price, 0) * 100, 2) as change_percent
FROM latest l
JOIN previous p ON l.product_id = p.product_id 
    AND l.supplier_id = p.supplier_id 
    AND l.source = p.source
WHERE l.rn = 1 AND p.rn = 2;
```

**Weekly average prices:**
```sql
SELECT 
    DATE_TRUNC('week', recorded_at) as week,
    AVG(price) as avg_price
FROM price_history
WHERE product_id = 123
GROUP BY DATE_TRUNC('week', recorded_at)
ORDER BY week;
```

---

## 5. Suppliers

Seller/merchant information with trust metrics.

### Table Definition

```sql
CREATE TABLE suppliers (
    id                      SERIAL PRIMARY KEY,
    name                    VARCHAR(255) NOT NULL,
    source                  VARCHAR(100) NOT NULL,
    source_id               VARCHAR(255),
    contact_info            JSONB DEFAULT '{}',
    trust_score             DECIMAL(3, 2) DEFAULT 0.00 CHECK (trust_score >= 0 AND trust_score <= 1),
    total_listings          INTEGER DEFAULT 0,
    successful_transactions INTEGER DEFAULT 0,
    avg_response_time_hours INTEGER,
    verified                BOOLEAN DEFAULT FALSE,
    is_active               BOOLEAN DEFAULT TRUE,
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(source, source_id)
);

-- Indexes
CREATE INDEX idx_suppliers_source ON suppliers(source);
CREATE INDEX idx_suppliers_trust_score ON suppliers(trust_score DESC);
CREATE INDEX idx_suppliers_name_trgm ON suppliers USING GIN (name gin_trgm_ops);
```

### Contact Info JSONB Structure

```json
{
    "email": "contact@supplier.com",
    "phone": "+234 xxx xxx xxxx",
    "address": "123 Main Street, Lagos",
    "website": "https://supplier.com",
    "social_media": {
        "twitter": "@supplier",
        "instagram": "@supplier"
    }
}
```

### Trust Score Calculation

Trust score is calculated from:
- Transaction completion rate (40%)
- Response time (20%)
- Listing accuracy (20%)
- Review scores (20%)

```sql
UPDATE suppliers SET trust_score = 
    (transaction_rate * 0.4) + 
    (response_score * 0.2) + 
    (accuracy_score * 0.2) + 
    (review_score * 0.2);
```

### Sample Queries

**Top trusted suppliers for a category:**
```sql
SELECT 
    s.*,
    COUNT(rl.id) as active_listings
FROM suppliers s
JOIN raw_listings rl ON rl.supplier_id = s.id
JOIN products p ON p.id = rl.product_id
WHERE p.category_id = 2
  AND s.is_active = TRUE
  AND rl.is_active = TRUE
GROUP BY s.id
ORDER BY s.trust_score DESC
LIMIT 20;
```

**Supplier statistics:**
```sql
SELECT 
    supplier_id,
    COUNT(*) as total_listings,
    COUNT(DISTINCT product_id) as unique_products,
    AVG(price) as avg_price,
    MIN(price) as lowest_price,
    MAX(price) as highest_price
FROM raw_listings
WHERE is_active = TRUE
GROUP BY supplier_id;
```

---

## 6. Suspicious Prices

Flagged listings that may be fraudulent or erroneous.

### Table Definition

```sql
CREATE TABLE suspicious_prices (
    id              SERIAL PRIMARY KEY,
    listing_id      INTEGER NOT NULL REFERENCES raw_listings(id) ON DELETE CASCADE,
    reason          VARCHAR(100) NOT NULL,
    details         TEXT,
    severity        VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    anomaly_score   DECIMAL(5, 4),
    reviewed        BOOLEAN DEFAULT FALSE,
    reviewed_by     VARCHAR(255),
    reviewed_at     TIMESTAMPTZ,
    resolution      VARCHAR(50),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_suspicious_listing_id ON suspicious_prices(listing_id);
CREATE INDEX idx_suspicious_severity ON suspicious_prices(severity);
CREATE INDEX idx_suspicious_reviewed ON suspicious_prices(reviewed) WHERE NOT reviewed;
CREATE INDEX idx_suspicious_created_at ON suspicious_prices(created_at DESC);
```

### Reason Types

- `price_too_low` - Price significantly below market average
- `price_too_high` - Price significantly above market average
- `duplicate_listing` - Multiple listings for same product from same supplier
- `invalid_url` - URL no longer accessible
- `price_manipulation` - Sudden extreme price change detected
- `fake_discount` - Claimed discount doesn't match actual price history
- `unrealistic_offer` - Price too good to be true

### Severity Levels

| Level    | Description                              | Action Required          |
|----------|------------------------------------------|--------------------------|
| low      | Minor anomaly, low confidence            | Monitor                  |
| medium   | Notable anomaly, review recommended     | Review within 48h        |
| high     | Strong anomaly, likely problematic       | Review within 24h        |
| critical | Extremely suspicious, immediate action   | Investigate immediately  |

### Sample Queries

**Get critical un-reviewed flags:**
```sql
SELECT 
    sp.*,
    rl.original_name,
    rl.price,
    rl.url,
    rl.source
FROM suspicious_prices sp
JOIN raw_listings rl ON rl.id = sp.listing_id
WHERE sp.severity IN ('high', 'critical')
  AND sp.reviewed = FALSE
ORDER BY 
    CASE sp.severity 
        WHEN 'critical' THEN 1 
        WHEN 'high' THEN 2 
    END,
    sp.created_at DESC;
```

**Price anomaly detection query:**
```sql
-- Find listings with prices > 2 standard deviations from mean
WITH stats AS (
    SELECT 
        product_id,
        AVG(price) as mean_price,
        STDDEV(price) as std_price
    FROM raw_listings
    WHERE is_active = TRUE
      AND recorded_at > NOW() - INTERVAL '7 days'
    GROUP BY product_id
    HAVING COUNT(*) >= 5
)
SELECT 
    rl.*,
    s.mean_price,
    s.std_price,
    (rl.price - s.mean_price) / NULLIF(s.std_price, 0) as z_score
FROM raw_listings rl
JOIN stats s ON s.product_id = rl.product_id
WHERE ABS((rl.price - s.mean_price) / NULLIF(s.std_price, 0)) > 2
ORDER BY z_score DESC;
```

---

## 7. Views

### Active Product Prices View

```sql
CREATE OR REPLACE VIEW v_active_prices AS
SELECT 
    p.id as product_id,
    p.normalized_name,
    p.brand,
    c.name as category_name,
    rl.supplier_id,
    s.name as supplier_name,
    s.trust_score,
    rl.price,
    rl.source,
    rl.location,
    rl.url,
    rl.created_at
FROM products p
JOIN raw_listings rl ON rl.product_id = p.id
JOIN suppliers s ON s.id = rl.supplier_id
LEFT JOIN categories c ON c.id = p.category_id
WHERE p.is_active = TRUE
  AND rl.is_active = TRUE
  AND s.is_active = TRUE;
```

### Price Summary View

```sql
CREATE OR REPLACE VIEW v_price_summary AS
SELECT 
    p.id as product_id,
    p.normalized_name,
    p.brand,
    c.name as category_name,
    COUNT(DISTINCT rl.supplier_id) as supplier_count,
    MIN(rl.price) as min_price,
    MAX(rl.price) as max_price,
    ROUND(AVG(rl.price)::numeric, 2) as avg_price,
    COUNT(rl.id) as listing_count,
    MAX(rl.created_at) as last_seen
FROM products p
LEFT JOIN categories c ON c.id = p.category_id
LEFT JOIN raw_listings rl ON rl.product_id = p.id AND rl.is_active = TRUE
WHERE p.is_active = TRUE
GROUP BY p.id, p.normalized_name, p.brand, c.name;
```

---

## 8. Triggers & Functions

### Auto-update updated_at

```sql
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all tables with updated_at
CREATE TRIGGER tr_products_updated_at 
    BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER tr_raw_listings_updated_at 
    BEFORE UPDATE ON raw_listings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER tr_suppliers_updated_at 
    BEFORE UPDATE ON suppliers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER tr_categories_updated_at 
    BEFORE UPDATE ON categories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

### Record price changes

```sql
CREATE OR REPLACE FUNCTION record_price_change()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.price != OLD.price OR NEW.supplier_id != OLD.supplier_id THEN
        INSERT INTO price_history (product_id, supplier_id, source, price)
        VALUES (NEW.product_id, NEW.supplier_id, NEW.source, NEW.price);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_listing_price_change
    AFTER INSERT OR UPDATE ON raw_listings
    FOR EACH ROW EXECUTE FUNCTION record_price_change();
```

### Update supplier listing count

```sql
CREATE OR REPLACE FUNCTION update_supplier_stats()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        UPDATE suppliers 
        SET total_listings = total_listings - 1
        WHERE id = OLD.supplier_id;
    ELSIF TG_OP = 'INSERT' THEN
        UPDATE suppliers 
        SET total_listings = total_listings + 1
        WHERE id = NEW.supplier_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_update_supplier_listing_count
    AFTER INSERT OR DELETE ON raw_listings
    FOR EACH ROW EXECUTE FUNCTION update_supplier_stats();
```

---

## 9. Partitioning Strategy

### Price History Partitioning by Month

```sql
CREATE TABLE price_history (
    id              SERIAL,
    product_id      INTEGER NOT NULL,
    supplier_id     INTEGER,
    source          VARCHAR(100) NOT NULL,
    price           DECIMAL(12, 2) NOT NULL,
    recorded_at     TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (id, recorded_at)
) PARTITION BY RANGE (recorded_at);

-- Create monthly partitions
CREATE TABLE price_history_2024_01 PARTITION OF price_history
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE price_history_2024_02 PARTITION OF price_history
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- Continue for other months...

-- Auto-create partitions function
CREATE OR REPLACE FUNCTION create_monthly_partition()
RETURNS void AS $$
DECLARE
    partition_date DATE;
    partition_name TEXT;
    start_date TEXT;
    end_date TEXT;
BEGIN
    partition_date := DATE_TRUNC('month', NOW() + INTERVAL '1 month');
    partition_name := 'price_history_' || TO_CHAR(partition_date, 'YYYY_MM');
    start_date := TO_CHAR(partition_date, 'YYYY-MM-DD');
    end_date := TO_CHAR(partition_date + INTERVAL '1 month', 'YYYY-MM-DD');
    
    EXECUTE format(
        'CREATE TABLE IF NOT EXISTS %I PARTITION OF price_history 
         FOR VALUES FROM (%L) TO (%L)',
        partition_name, start_date, end_date
    );
END;
$$ LANGUAGE plpgsql;
```

---

## 10. Maintenance

### Vacuum and Analyze Schedule

```sql
-- Recommended autovacuum settings in postgresql.conf
ALTER TABLE products SET (
    autovacuum_vacuum_scale_factor = 0.01,
    autovacuum_analyze_scale_factor = 0.01
);

ALTER TABLE raw_listings SET (
    autovacuum_vacuum_scale_factor = 0.05,
    autovacuum_analyze_scale_factor = 0.02
);

ALTER TABLE price_history SET (
    autovacuum_vacuum_scale_factor = 0.1
);
```

### Data Retention

```sql
-- Archive old price history (older than 1 year) to cold storage
CREATE TABLE price_history_archive () INHERITS (price_history);

-- Move old data monthly
INSERT INTO price_history_archive 
SELECT * FROM price_history 
WHERE recorded_at < NOW() - INTERVAL '1 year';

DELETE FROM price_history 
WHERE recorded_at < NOW() - INTERVAL '1 year';
```

---

## 11. Common Operations

### Product Deduplication

```sql
-- Find potential duplicates based on normalized name similarity
SELECT 
    normalized_name,
    category_id,
    COUNT(*) as count,
    ARRAY_AGG(id) as product_ids
FROM products
GROUP BY normalized_name, category_id
HAVING COUNT(*) > 1;
```

### Bulk Price Update

```sql
-- Update prices from new scrape data
INSERT INTO raw_listings (product_id, supplier_id, source, original_name, price, url, source_id)
VALUES 
    (123, 1, 'jiji', 'Dangote Cement 50kg', 4500.00, 'https://jiji.ng/listing/123', 'jiji_123'),
    (456, 2, 'konga', 'HP Laptop 15', 350000.00, 'https://konga.com/product/456', 'konga_456')
ON CONFLICT (source, source_id) 
DO UPDATE SET 
    price = EXCLUDED.price,
    last_checked_at = NOW();
```

### Generate Sitemap Data

```sql
SELECT 
    '/products/' || p.id || '-' || LOWER(REPLACE(p.normalized_name, ' ', '-')) as path,
    'product' as type,
    p.updated_at as lastmod
FROM products p
WHERE p.is_active = TRUE
ORDER BY p.updated_at DESC;
```

---

## 12. Performance Guidelines

| Operation | Expected Rows | Recommended Approach |
|-----------|---------------|---------------------|
| Product search | 10-100 | GiN trigram index + LIMIT |
| Price history | 1000-10000 | Partition by time + product_id index |
| Supplier lookup | 1-100 | B-tree index on source + source_id |
| Category tree | 50-500 | Recursive CTE with index on parent_id |
| Bulk insert | 1000-10000 | COPY command + batch inserts |

---

## 13. Security Considerations

- Use row-level security for multi-tenant queries
- Sanitize all raw_data JSONB input
- Rate limit API endpoints
- Use parameterized queries to prevent SQL injection
- Store API keys and secrets in environment variables

---

*Last updated: 2026-05-12*
