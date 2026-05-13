# Web Scraping Strategy Guide - MarketSense NG

> This document defines the web scraping architecture for the MarketSense NG Price Intelligence System.

---

## 1. Target Sources

| Source | Type | Priority | Notes |
|---|---|---|---|
| **Jiji.ng** | E-commerce marketplace | High | Most popular classifieds in Nigeria |
| **Konga.com** | E-commerce platform | High | Major online retailer |
| **Jumia.com.ng** | E-commerce platform | High | Largest e-commerce in Nigeria |
| **Facebook Marketplace** | Social commerce | Medium | Informal sellers, high volume |
| **CSV Imports** | Manual upload | High | Offline sellers, bulk data entry |
| **WhatsApp OCR** | Image processing | Low | Screenshot extraction (Phase 2) |

---

## 2. Scraping Approaches

### 2.1 Playwright (JavaScript-rendered sites)

**Use when:** Site uses heavy JS rendering, infinite scroll, lazy loading.

```javascript
// playwright-setup.js
import { chromium } from 'playwright';

export async function createBrowser(config = {}) {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    userAgent: config.userAgent || getRandomUserAgent(),
    viewport: { width: 1280, height: 720 },
    extraHTTPHeaders: {
      'Accept-Language': 'en-US,en;q=0.9',
    },
  });
  return { browser, context };
}

export async function scrapePage(page, url, options = {}) {
  const { waitForSelector, timeout = 30000, retries = 3 } = options;

  for (let attempt = 0; attempt < retries; attempt++) {
    try {
      await page.goto(url, { waitUntil: 'networkidle', timeout });
      if (waitForSelector) {
        await page.waitForSelector(waitForSelector, { timeout: 10000 });
      }
      return await page.content();
    } catch (error) {
      console.warn(`Attempt ${attempt + 1} failed: ${error.message}`);
      if (attempt === retries - 1) throw error;
      await sleep(2000 * (attempt + 1));
    }
  }
}

export async function closeBrowser(browser) {
  if (browser) await browser.close();
}
```

**Common patterns for Nigerian sites:**

```javascript
// jiji-ng-scraper.js
import { chromium } from 'playwright';
import { getRandomDelay } from './utils/delay.js';

const USER_AGENTS = [
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Firefox/121.0',
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
];

export async function scrapeJijiListings(categoryUrl) {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    userAgent: USER_AGENTS[Math.floor(Math.random() * USER_AGENTS.length)],
  });

  const page = await context.newPage();

  // Block images/styles for speed
  await page.route('**/*.{png,jpg,jpeg,css}', route => route.abort());

  try {
    await page.goto(categoryUrl, { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('[data-testid="listing-card"]', { timeout: 10000 });

    const listings = await page.evaluate(() => {
      const cards = document.querySelectorAll('[data-testid="listing-card"]');
      return Array.from(cards).map(card => ({
        title: card.querySelector('.adTitle')?.textContent?.trim() || '',
        price: card.querySelector('.priceValue')?.textContent?.trim() || '',
        location: card.querySelector('.location span')?.textContent?.trim() || '',
        url: card.querySelector('a')?.href || '',
        seller: card.querySelector('.sellerName')?.textContent?.trim() || 'Unknown',
      }));
    });

    return listings;
  } finally {
    await browser.close();
  }
}
```

### 2.2 Scrapy (Static pages)

**Use when:** Site is mostly static HTML, faster crawling needed.

```python
# scrapy_project/spiders/jumia_spider.py
import scrapy
import re
from datetime import datetime

class JumiaSpider(scrapy.Spider):
    name = 'jumia'
    allowed_domains = ['jumia.com.ng']
    custom_settings = {
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 3,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
        'USER_AGENT': 'MarketSenseNG/1.0 (research@marketsense.ng)',
    }

    def __init__(self, categories=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.categories = categories or ['phones', 'electronics', 'fashion']

    def start_requests(self):
        base_url = 'https://www.jumia.com.ng/'
        for cat in self.categories:
            yield scrapy.Request(
                f'{base_url}{cat}/',
                callback=self.parse_category,
                meta={'category': cat}
            )

    def parse_category(self, response):
        products = response.css('div.prd')

        for product in products:
            yield {
                'name': self.clean_text(product.css('h3::text').get()),
                'price': self.normalize_price(product.css('div.prc::text').get()),
                'seller': self.clean_text(product.css('span.spp::text').get()),
                'location': 'Nigeria',  # Jumia ships nationally
                'url': response.urljoin(product.css('a::attr(href)').get()),
                'category': response.meta['category'],
                'scraped_at': datetime.utcnow().isoformat(),
                'source': 'jumia',
            }

        # Pagination
        next_page = response.css('a.pg[aria-label="Next"]::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse_category)

    def normalize_price(self, price_str):
        if not price_str:
            return None
        # Remove currency symbols and clean
        cleaned = re.sub(r'[^\d.,]', '', price_str)
        # Convert various formats: "₦15,000", "15k", "15,000"
        cleaned = cleaned.replace(',', '').replace(' ', '').lower()
        if 'k' in cleaned:
            cleaned = cleaned.replace('k', '000')
        try:
            return float(cleaned)
        except ValueError:
            return None

    def clean_text(self, text):
        if not text:
            return ''
        return ' '.join(text.split()).strip()
```

**Scrapy settings for Nigerian sites:**

```python
# scrapy_project/settings.py
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'scrapy_project.middlewares.RandomUserAgentMiddleware': 400,
    'scrapy_project.middlewares.RetryMiddleware': 550,
}

ROTATING_PROXY_LIST = [
    # Add Nigerian proxies if needed for scale
]

DOWNLOAD_DELAY = 3
RANDOMIZE_DOWNLOAD_DELAY = True
CONCURRENT_REQUESTS_PER_DOMAIN = 1
COOKIES_ENABLED = True
TELNETCONSOLE_ENABLED = False

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 2
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
```

### 2.3 API Reverse Engineering

**For mobile apps and hidden APIs:**

```javascript
// api_discovery.js
// Use Playwright to detect network requests and find hidden APIs

async function discoverApi(baseUrl) {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  const apiCalls = [];

  page.on('response', async response => {
    const url = response.url();
    if (url.includes('/api/') || url.includes('/v1/') || url.includes('/graphql')) {
      try {
        const body = await response.json().catch(() => response.text());
        apiCalls.push({
          url,
          status: response.status(),
          method: response.request().method(),
          body: typeof body === 'object' ? body : null,
        });
      } catch {
        apiCalls.push({ url, status: response.status(), method: response.request().method() });
      }
    }
  });

  await page.goto(baseUrl, { waitUntil: 'networkidle' });
  await browser.close();

  return apiCalls;
}

// Common Konga/Jumia API patterns:
// https://api.konga.com/v1/products/search
// https://api.jumia.com.ng/v1/products
```

---

## 3. Data Points to Collect

### 3.1 Required Fields

| Field | Type | Source | Validation |
|---|---|---|---|
| `product_name` | string | Scrape/Import | Min 3 chars |
| `price` | decimal | Scrape/Import | > 0, normalized to NGN |
| `price_currency` | string | Scrape/Import | Default: 'NGN' |
| `seller_name` | string | Scrape/Import | Min 1 char |
| `seller_contact` | string | Scrape/Import | Optional, phone/email format |
| `location_city` | string | Scrape/Import | Standardized to city names |
| `location_state` | string | Scrape/Import | Nigerian states |
| `source_url` | string | Scrape | Valid URL format |
| `category` | string | Scrape/Import | From category taxonomy |
| `subcategory` | string | Scrape/Import | More granular |
| `scraped_at` | timestamp | System | ISO 8601 |
| `scrape_source` | string | System | Enum: jiji, konga, jumia, facebook, csv, whatsapp |
| `listing_id` | string | Scrape | Source-specific ID |

### 3.2 Optional Fields

| Field | Type | Notes |
|---|---|---|
| `condition` | enum | new, used, refurbished |
| `brand` | string | Extracted from name |
| `model` | string | Extracted from name |
| `description` | text | Full description if available |
| `image_urls` | array | Product images |
| `rating` | decimal | Seller/rating if available |
| `last_seen` | timestamp | For tracking delistings |

---

## 4. Rate Limiting & Ethics

### 4.1 Rate Limiting Configuration

```javascript
// utils/rateLimiter.js
export class RateLimiter {
  constructor(options = {}) {
    this.minDelay = options.minDelay || 2000;    // 2 seconds
    this.maxDelay = options.maxDelay || 5000;    // 5 seconds
    this.maxRetries = options.maxRetries || 3;
    this.backoffMultiplier = options.backoff || 2;
  }

  async execute(fn) {
    const delay = this.minDelay + Math.random() * (this.maxDelay - this.minDelay);
    await this.sleep(delay);
    return fn();
  }

  async withRetry(fn, context = {}) {
    let lastError;

    for (let attempt = 0; attempt < this.maxRetries; attempt++) {
      try {
        return await this.execute(fn);
      } catch (error) {
        lastError = error;
        console.warn(`Retry ${attempt + 1}/${this.maxRetries} for ${context.url}: ${error.message}`);

        if (attempt < this.maxRetries - 1) {
          const backoff = Math.pow(this.backoffMultiplier, attempt) * 1000;
          await this.sleep(backoff);
        }
      }
    }

    throw lastError;
  }

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
```

### 4.2 Robots.txt Compliance

```javascript
// utils/robotsChecker.js
import robotsParser from 'robots-parser';

export async function canScrape(url) {
  const robotsUrl = new URL('/robots.txt', new URL(url).origin).href;

  try {
    const response = await fetch(robotsUrl);
    const robotsTxt = await response.text();
    const parser = robotsParser(robotsUrl, robotsTxt);

    return parser.isAllowed(url, 'MarketSenseNG/1.0 (+mailto:research@marketsense.ng)');
  } catch {
    // If robots.txt not accessible, default to not scraping
    console.warn(`Could not fetch robots.txt for ${url}, defaulting to allowed`);
    return true; // Be permissive if we can't check
  }
}

// Usage
const allowed = await canScrape('https://www.jiji.ng/product/12345');
if (!allowed) {
  console.warn('Scraping blocked by robots.txt');
  return [];
}
```

### 4.3 User Agent Rotation

```javascript
// utils/userAgents.js
export const USER_AGENTS = [
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/121.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Firefox/122.0',
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/121.0.0.0 Safari/537.36',
  'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/121.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
];

export function getRandomUserAgent() {
  return USER_AGENTS[Math.floor(Math.random() * USER_AGENTS.length)];
}

export function rotateUserAgent(context) {
  const currentIndex = USER_AGENTS.indexOf(context.userAgent);
  const nextIndex = (currentIndex + 1) % USER_AGENTS.length;
  return USER_AGENTS[nextIndex];
}
```

### 4.4 Error Handling

```javascript
// utils/errorHandler.js
export class ScrapingError extends Error {
  constructor(message, code, context = {}) {
    super(message);
    this.name = 'ScrapingError';
    this.code = code;
    this.context = context;
    this.timestamp = new Date().toISOString();
  }
}

export const ErrorCodes = {
  RATE_LIMITED: 'RATE_LIMITED',
  BLOCKED: 'BLOCKED',
  PARSE_FAILED: 'PARSE_FAILED',
  NOT_FOUND: 'NOT_FOUND',
  TIMEOUT: 'TIMEOUT',
  INVALID_RESPONSE: 'INVALID_RESPONSE',
  ROBOTS_BLOCKED: 'ROBOTS_BLOCKED',
};

export async function withErrorHandling(fn, context = {}) {
  try {
    return await fn();
  } catch (error) {
    const scrapingError = new ScrapingError(
      error.message,
      mapErrorToCode(error),
      { ...context, originalError: error.stack }
    );

    await logError(scrapingError);
    throw scrapingError;
  }
}

function mapErrorToCode(error) {
  if (error.message.includes('net::ERR_')) return ErrorCodes.TIMEOUT;
  if (error.message.includes('403')) return ErrorCodes.BLOCKED;
  if (error.message.includes('429')) return ErrorCodes.RATE_LIMITED;
  if (error.message.includes('404')) return ErrorCodes.NOT_FOUND;
  return ErrorCodes.PARSE_FAILED;
}

async function logError(error) {
  // Send to logging service
  console.error(JSON.stringify(error));
}
```

---

## 5. Nigerian-Specific Challenges

### 5.1 Price Format Normalization

```javascript
// utils/priceNormalizer.js
const PRICE_PATTERNS = [
  { regex: /₦\s*([\d,]+(?:\.\d{2})?)/i, parser: (m) => m.replace(/,/g, '') },  // ₦15,000
  { regex: /([\d,]+(?:\.\d{2})?)\s*(?:ngn|naira)/i, parser: (m) => m.replace(/,/g, '') },  // 15000 naira
  { regex: /([\d.]+)\s*k\b/i, parser: (m) => (parseFloat(m) * 1000).toString() },  // 15k
  { regex: /([\d,]+)\s*k\b/i, parser: (m) => m.replace(/,/g, '').replace(/k$/i, '000') },  // 15,000k
  { regex: /([\d,]+)/, parser: (m) => m.replace(/,/g, '') },  // 15,000
  { regex: /([\d.]+)/, parser: (m) => parseFloat(m).toString() },  // 15000.00
];

export function normalizePrice(priceStr) {
  if (!priceStr || typeof priceStr !== 'string') {
    return null;
  }

  const cleaned = priceStr.trim();

  for (const { regex, parser } of PRICE_PATTERNS) {
    const match = cleaned.match(regex);
    if (match) {
      const parsed = parser(match[1] || match[0]);
      const value = parseFloat(parsed);
      if (!isNaN(value) && value > 0 && value < 100000000) {  // Sanity check
        return Math.round(value * 100) / 100;  // Round to 2 decimals
      }
    }
  }

  console.warn(`Could not parse price: ${priceStr}`);
  return null;
}

// Usage
normalizePrice('₦15,000');        // 15000
normalizePrice('15k');            // 15000
normalizePrice('15,000 NGN');     // 15000
normalizePrice('N15,000');        // 15000
normalizePrice('15000');          // 15000
```

### 5.2 Location Normalization

```javascript
// utils/locationNormalizer.js
const LOCATION_MAP = {
  'lagos': 'Lagos',
  'lagos state': 'Lagos',
  'lagos island': 'Lagos',
  'lekki': 'Lagos',
  'victoria island': 'Lagos',
  'vi': 'Lagos',
  'ikeja': 'Lagos',
  'surulere': 'Lagos',
  'yaba': 'Lagos',
  'abuja': 'Abuja',
  'fct': 'Abuja',
  'abuja fct': 'Abuja',
  'port harcourt': 'Port Harcourt',
  'ph': 'Port Harcourt',
  'rivers': 'Port Harcourt',
  'kano': 'Kano',
  'ibadan': 'Ibadan',
  'enugu': 'Enugu',
  'benin city': 'Benin City',
  'calabar': 'Calabar',
  'kaduna': 'Kaduna',
  'uyo': 'Uyo',
  'aba': 'Aba',
};

const STATE_MAP = {
  'Lagos': 'Lagos',
  'Abuja': 'FCT',
  'Port Harcourt': 'Rivers',
  'Kano': 'Kano',
  'Ibadan': 'Oyo',
  'Enugu': 'Enugu',
  'Benin City': 'Edo',
  'Calabar': 'Cross River',
  'Kaduna': 'Kaduna',
  'Uyo': 'Akwa Ibom',
  'Aba': 'Abia',
};

export function normalizeLocation(locationStr) {
  if (!locationStr) return { city: 'Unknown', state: 'Unknown' };

  const cleaned = locationStr.toLowerCase().trim();

  // Direct match
  if (LOCATION_MAP[cleaned]) {
    const city = LOCATION_MAP[cleaned];
    return { city, state: STATE_MAP[city] || 'Unknown' };
  }

  // Partial match
  for (const [pattern, city] of Object.entries(LOCATION_MAP)) {
    if (cleaned.includes(pattern)) {
      return { city, state: STATE_MAP[city] || 'Unknown' };
    }
  }

  // Try to extract state
  const stateMatch = cleaned.match(/(?:state|lagos state|abuja fct)/i);
  if (stateMatch) {
    const city = cleaned.replace(stateMatch[0], '').trim();
    return { city: capitalize(city) || 'Unknown', state: capitalize(stateMatch[0]) || 'Unknown' };
  }

  return { city: capitalize(cleaned), state: 'Unknown' };
}

function capitalize(str) {
  return str.replace(/\b\w/g, c => c.toUpperCase());
}
```

### 5.3 Text Cleaning (English/Pidgin)

```javascript
// utils/textCleaner.js
import stringSimilarity from 'string-similarity';

const PRODUCT_KEYWORDS = [
  'iphone', 'samsung', 'huawei', 'dell', 'hp', 'lenovo', 'macbook',
  'nike', 'adidas', 'zara', 'hm', 'gucci', 'louis vuitton',
  'samsung', 'lg', 'sony', 'philips', ' panasonic',
];

export function cleanProductName(name) {
  if (!name) return '';

  let cleaned = name
    .replace(/\s+/g, ' ')  // Multiple spaces
    .replace(/[^\w\s'-,.]/g, '')  // Special chars except price indicators
    .trim();

  // Common Pidgin corrections
  const pidginFixes = {
    /\bcomot\b/gi: 'remove',
    /\bdie\b/gi: 'dead',
    /\bhow much\b/gi: '',
    /\bna\b/gi: 'is',
    /\bburna\b/gi: 'burner',
    /\bsabi\b/gi: 'know',
    /\bshop\b/gi: 'store',
    /\bdollar\b/gi: '$',
    /\bnaira\b/gi: '₦',
  };

  for (const [pattern, replacement] of Object.entries(pidginFixes)) {
    cleaned = cleaned.replace(pattern, replacement);
  }

  return cleaned;
}

export function extractBrand(name) {
  const cleaned = name.toLowerCase();

  for (const brand of PRODUCT_KEYWORDS) {
    if (cleaned.includes(brand)) {
      return brand.charAt(0).toUpperCase() + brand.slice(1);
    }
  }

  return 'Unknown';
}

export function extractCondition(text) {
  const lower = text.toLowerCase();

  if (/new\s*(?!item|product|in\s*box)/i.test(lower)) return 'new';
  if (/used|fairly used|second hand|pre-owned/i.test(lower)) return 'used';
  if (/refurbished|recondition/i.test(lower)) return 'refurbished';

  return 'unknown';
}
```

---

## 6. Implementation Plan

### Phase 1: Foundation (Week 1-2)

**Goal:** CSV import + mock scraper for UI development

```
init/
├── scripts/
│   ├── csv-importer.js       # CSV upload and parsing
│   └── mock-data-generator.js # Generate realistic test data
├── utils/
│   ├── priceNormalizer.js
│   └── locationNormalizer.js
└── tests/
    └── normalizer.test.js
```

**Deliverables:**
- [ ] CSV import endpoint with validation
- [ ] Mock scraper that generates test data
- [ ] Price/location normalization utilities
- [ ] Unit tests for all utilities

### Phase 2: Basic Scraping (Week 3-4)

**Goal:** Implement Playwright scraper for one site

```
src/
├── scrapers/
│   ├── base/
│   │   ├── RateLimiter.js
│   │   ├── BaseScraper.js
│   │   └── robotsChecker.js
│   └── sites/
│       ├── jiji.js
│       └── config.js
```

**Deliverables:**
- [ ] Base scraper class with error handling
- [ ] Rate limiting implementation
- [ ] Jiji.ng scraper (start with 3 categories)
- [ ] Robots.txt compliance checker

### Phase 3: Multi-Site Support (Week 5-6)

**Goal:** Add Konga and Jumia scrapers

**Deliverables:**
- [ ] Konga.com scraper
- [ ] Jumia.com.ng scraper
- [ ] Common product matching across sources
- [ ] Scheduling system (cron or similar)

### Phase 4: Advanced Features (Week 7-8)

**Goal:** Facebook Marketplace + WhatsApp OCR

**Deliverables:**
- [ ] Facebook Marketplace scraper
- [ ] WhatsApp screenshot OCR pipeline
- [ ] Price history tracking
- [ ] Alert system for price changes

---

## 7. CSV Import Specification

### Expected Format

```csv
product_name,price,currency,seller_name,seller_contact,location,category
iPhone 14 Pro 256GB,850000,NGN,John Electronics,08031234567,Lagos,Phones
Samsung 55" Smart TV,450000,NGN,Tech Store,08099876543,Abuja,Electronics
Nike Air Max 270,35000,NGN,Fashion Hub,08055512345,Ibadan,Fashion
```

### Validation Rules

| Field | Required | Validation |
|---|---|---|
| product_name | Yes | Min 3 chars, max 500 |
| price | Yes | Numeric, > 0 |
| currency | No | Default: NGN |
| seller_name | Yes | Min 1 char |
| seller_contact | No | Phone format: 08xxxxxxxxx or email |
| location | Yes | Any text (will be normalized) |
| category | Yes | Must match category taxonomy |

### Upload Endpoint

```
POST /api/imports/csv
Content-Type: multipart/form-data

Response: {
  "success": true,
  "imported": 150,
  "failed": 3,
  "errors": [
    { "row": 12, "field": "price", "error": "Invalid format" }
  ]
}
```

---

## 8. Monitoring & Logging

### Required Logs

```javascript
// logs/scraper-logs.js
export function logScrapingEvent(event) {
  const logEntry = {
    timestamp: new Date().toISOString(),
    event_type: event.type,  // 'scrape_start', 'scrape_complete', 'error', 'retry'
    source: event.source,
    url: event.url,
    items_found: event.itemsFound || 0,
    duration_ms: event.duration || 0,
    error: event.error || null,
  };

  // Write to log file
  appendToFile('logs/scraping.log', JSON.stringify(logEntry) + '\n');

  // Send to monitoring if error
  if (event.type === 'error') {
    sendAlert(logEntry);
  }
}
```

### Health Checks

- Track success/failure ratio per source
- Monitor average response times
- Alert on sustained failures (> 5 consecutive)
- Report items per hour crawled

---

## 9. Legal & Ethical Considerations

1. **Terms of Service:** Always read and comply with site ToS. Jiji, Konga, Jumia prohibit scraping in their ToS - use for research only or obtain permission.

2. **Data Usage:**
   - Do not republish scraped data
   - Use only for internal price intelligence
   - Do not store personal contact info longer than needed

3. **Rate Limiting:**
   - Never exceed 1 request per second
   - Respect 429 responses and back off
   - Consider off-peak hours (2-6 AM WAT)

4. **Alternative Approaches:**
   - Use official APIs where available
   - Partner with platforms for data access
   - Consider paid data feeds

---

*Document Version: 1.0*
*Last Updated: 2026-05-12*
*Maintainer: MarketSense NG Engineering Team*