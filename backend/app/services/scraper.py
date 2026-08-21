import asyncio
import ipaddress
import re
import socket
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit

import httpx
from bs4 import BeautifulSoup, Tag

from app.core.config import settings
from app.schemas import ListingInput, ScrapeRequest


PRICE_RE = re.compile(
    r"(?:\u20a6|NGN|N\s?)(?P<prefixed>\d[\d,]*(?:\.\d{1,2})?)|"
    r"(?P<number>\d{1,3}(?:,\d{3})+(?:\.\d{1,2})?)\s?(?:naira|NGN)?",
    re.IGNORECASE,
)
REDIRECT_STATUSES = {301, 302, 303, 307, 308}


class ScrapeSafetyError(ValueError):
    """Raised when a requested scrape target violates network safety rules."""


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
            listings.append(
                ListingInput(
                    source=payload.source,
                    original_name=name[:255],
                    price=price_match.value,
                    seller_name=seller_name,
                    seller_source=payload.seller_source,
                    location=payload.location,
                    url=payload.url,
                )
            )

            if len(listings) >= payload.max_items:
                return listings

    return listings


def validate_scrape_target_syntax(url: str) -> str:
    """Reject obviously unsafe targets before any scraper/network code runs."""
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError as exc:
        raise ScrapeSafetyError("Scrape target must be a valid public HTTP(S) URL") from exc

    if parsed.scheme.lower() not in {"http", "https"}:
        raise ScrapeSafetyError("Scrape target must use public HTTP or HTTPS")
    if parsed.username or parsed.password:
        raise ScrapeSafetyError("Scrape target must not contain URL credentials")

    host = (parsed.hostname or "").rstrip(".").lower()
    if not host:
        raise ScrapeSafetyError("Scrape target must include a public hostname")
    if host == "localhost" or host.endswith(".localhost"):
        raise ScrapeSafetyError("Scrape target must resolve to a public network address")

    try:
        literal_ip = ipaddress.ip_address(host)
    except ValueError:
        literal_ip = None

    if literal_ip is not None and not literal_ip.is_global:
        raise ScrapeSafetyError("Scrape target must resolve to a public network address")

    if settings.scrape_allowed_domains and not _host_matches_allowlist(
        host, settings.scrape_allowed_domains
    ):
        raise ScrapeSafetyError("Scrape target is not in the configured public-domain allowlist")

    if port is not None and not 1 <= port <= 65535:
        raise ScrapeSafetyError("Scrape target uses an invalid port")

    return host


async def validate_scrape_target(url: str) -> None:
    """Resolve a target and reject any private/reserved address before connecting."""
    host = validate_scrape_target_syntax(url)
    try:
        literal_ip = ipaddress.ip_address(host)
    except ValueError:
        literal_ip = None

    if literal_ip is not None:
        return

    parsed = urlsplit(url)
    port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)

    try:
        records = await asyncio.to_thread(
            socket.getaddrinfo,
            host,
            port,
            type=socket.SOCK_STREAM,
        )
    except socket.gaierror as exc:
        raise ScrapeSafetyError("Scrape target could not be resolved") from exc

    addresses: set[ipaddress.IPv4Address | ipaddress.IPv6Address] = set()
    for record in records:
        try:
            addresses.add(ipaddress.ip_address(record[4][0]))
        except ValueError:
            continue

    if not addresses or any(not address.is_global for address in addresses):
        raise ScrapeSafetyError("Scrape target must resolve only to public network addresses")


async def _fetch_html(url: str) -> str:
    await validate_scrape_target(url)

    if _browser_scraper_allowed(url):
        crawl4ai_html = await _fetch_with_crawl4ai(url)
        if crawl4ai_html:
            return crawl4ai_html

    return await _fetch_with_httpx(url)


async def _fetch_with_httpx(url: str) -> str:
    timeout = httpx.Timeout(settings.scrape_timeout_seconds)
    async with httpx.AsyncClient(
        follow_redirects=False,
        timeout=timeout,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0 Safari/537.36"
            )
        },
    ) as client:
        current_url = url

        for redirect_count in range(settings.max_scrape_redirects + 1):
            await validate_scrape_target(current_url)

            async with client.stream("GET", current_url) as response:
                if response.status_code in REDIRECT_STATUSES:
                    location = response.headers.get("location")
                    if not location:
                        raise ScrapeSafetyError("Scrape target returned an invalid redirect")
                    if redirect_count >= settings.max_scrape_redirects:
                        raise ScrapeSafetyError("Scrape target exceeded the redirect limit")

                    current_url = urljoin(current_url, location)
                    validate_scrape_target_syntax(current_url)
                    continue

                response.raise_for_status()

                content_type = response.headers.get("content-type", "").lower()
                if content_type and not (
                    "html" in content_type or content_type.startswith("text/")
                ):
                    raise ScrapeSafetyError("Scrape target did not return HTML content")

                content_length = response.headers.get("content-length")
                if content_length:
                    try:
                        announced_size = int(content_length)
                    except ValueError:
                        announced_size = 0
                    if announced_size > settings.max_scrape_response_bytes:
                        raise ScrapeSafetyError("Scrape response is too large")

                body = bytearray()
                async for chunk in response.aiter_bytes():
                    if len(body) + len(chunk) > settings.max_scrape_response_bytes:
                        raise ScrapeSafetyError("Scrape response is too large")
                    body.extend(chunk)

                return bytes(body).decode(response.encoding or "utf-8", errors="replace")

    raise ScrapeSafetyError("Scrape target could not be fetched safely")


def _browser_scraper_allowed(url: str) -> bool:
    if not settings.browser_scraper_enabled:
        return False
    if not settings.browser_scrape_allowed_domains:
        return False

    host = validate_scrape_target_syntax(url)
    return _host_matches_allowlist(host, settings.browser_scrape_allowed_domains)


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

    html = (
        getattr(result, "cleaned_html", None)
        or getattr(result, "html", None)
        or str(getattr(result, "markdown", "") or "")
    )
    if len(html.encode("utf-8")) > settings.max_scrape_response_bytes:
        raise ScrapeSafetyError("Browser scrape response is too large")
    return html


def _host_matches_allowlist(host: str, allowed_domains: list[str]) -> bool:
    normalized_host = host.rstrip(".").lower()
    for domain in allowed_domains:
        normalized_domain = domain.strip().rstrip(".").lstrip(".").lower()
        if not normalized_domain:
            continue
        if normalized_host == normalized_domain or normalized_host.endswith(
            f".{normalized_domain}"
        ):
            return True
    return False


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
        candidate = (
            candidate_node.get("title")
            or candidate_node.get("alt")
            or candidate_node.get_text(" ", strip=True)
        )
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
    host = (urlsplit(url).hostname or "").replace("www.", "")
    return host or "Website Supplier"
