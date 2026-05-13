import re
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup, Tag

from app.schemas import ListingInput, ScrapeRequest


PRICE_RE = re.compile(
    r"(?:\u20a6|NGN|N\s?)(?P<prefixed>\d[\d,]*(?:\.\d{1,2})?)|"
    r"(?P<number>\d{1,3}(?:,\d{3})+(?:\.\d{1,2})?)\s?(?:naira|NGN)?",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class PriceMatch:
    text: str
    value: float


async def scrape_price_listings(payload: ScrapeRequest) -> list[ListingInput]:
    html = await _fetch_html(payload.url)
    soup = BeautifulSoup(html, "html.parser")

    for node in soup(["script", "style", "noscript", "svg"]):
        node.decompose()

    seller_name = payload.seller_name or _domain_name(payload.url)
    listings: list[ListingInput] = []
    seen: set[tuple[str, float]] = set()

    for text_node in soup.find_all(string=PRICE_RE):
        parent = text_node.parent
        if not isinstance(parent, Tag):
            continue

        context_node = _expand_context(parent)
        context = context_node.get_text(" ", strip=True)
        if len(context) < 5:
            continue

        for price_match in _extract_prices(str(text_node)):
            name = _extract_listing_name(context_node, context, price_match.text)
            if not name:
                continue

            dedupe_key = (name.lower(), price_match.value)
            if dedupe_key in seen:
                continue

            seen.add(dedupe_key)
            listing = ListingInput(
                source=payload.source,
                original_name=name[:255],
                price=price_match.value,
                seller_name=seller_name,
                seller_source=payload.seller_source,
                location=payload.location,
                url=payload.url,
            )
            listings.append(listing)

            if len(listings) >= payload.max_items:
                return listings

    return listings


async def _fetch_html(url: str) -> str:
    crawl4ai_html = await _fetch_with_crawl4ai(url)
    if crawl4ai_html:
        return crawl4ai_html

    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=20,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0 Safari/537.36"
            )
        },
    ) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text


async def _fetch_with_crawl4ai(url: str) -> str | None:
    try:
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig
    except Exception:
        return None

    try:
        browser_config = BrowserConfig(headless=True, verbose=False)
        run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, word_count_threshold=1)
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=url, config=run_config)
    except Exception:
        return None

    if not getattr(result, "success", False):
        return None

    return (
        getattr(result, "cleaned_html", None)
        or getattr(result, "html", None)
        or str(getattr(result, "markdown", "") or "")
    )


def _extract_prices(text: str) -> list[PriceMatch]:
    matches: list[PriceMatch] = []
    for match in PRICE_RE.finditer(text):
        raw_value = match.group("prefixed") or match.group("number")
        if not raw_value:
            continue

        value = float(raw_value.replace(",", ""))
        if 10 <= value <= 1_000_000_000:
            matches.append(PriceMatch(text=match.group(0), value=value))

    return matches


def _expand_context(node: Tag) -> Tag:
    current = node
    for _ in range(3):
        parent = current.parent
        if not isinstance(parent, Tag):
            break
        text = parent.get_text(" ", strip=True)
        if 20 <= len(text) <= 700:
            current = parent
        if parent.name in {"article", "li", "tr", "section", "main"}:
            current = parent
            break
    return current


def _extract_listing_name(node: Tag, context: str, price_text: str) -> str | None:
    for selector in ["h1", "h2", "h3", "h4", "[title]", "img[alt]"]:
        candidate_node = node.select_one(selector)
        if not candidate_node:
            continue
        candidate = candidate_node.get("title") or candidate_node.get("alt") or candidate_node.get_text(" ", strip=True)
        cleaned = _clean_name(candidate, price_text)
        if cleaned:
            return cleaned

    cleaned_context = _clean_name(context, price_text)
    if cleaned_context:
        return cleaned_context

    previous_heading = node.find_previous(["h1", "h2", "h3", "h4"])
    if previous_heading:
        return _clean_name(previous_heading.get_text(" ", strip=True), price_text)

    return None


def _clean_name(text: str | None, price_text: str) -> str | None:
    if not text:
        return None

    cleaned = PRICE_RE.sub(" ", text.replace(price_text, " "))
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" -:|,")
    if len(cleaned) > 255:
        cleaned = cleaned[:255].rsplit(" ", 1)[0]

    if len(cleaned) < 3:
        return None

    rejected = {"price", "add to cart", "buy now", "shop now", "sale"}
    if cleaned.lower() in rejected:
        return None

    return cleaned


def _domain_name(url: str) -> str:
    host = urlparse(url).netloc.replace("www.", "")
    return host or "Website Supplier"
