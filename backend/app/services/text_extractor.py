import asyncio
import concurrent.futures
import csv
import io
import logging
import re
import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urljoin, urlparse

import docx
import fitz  # PyMuPDF
from curl_cffi import requests as cffi_requests
from curl_cffi.requests.errors import RequestsError
from bs4 import BeautifulSoup
from markdownify import markdownify as md

from app.core.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# CrawlResult dataclass
# ---------------------------------------------------------------------------
@dataclass
class CrawlResult:
    text: str
    pages_crawled: int
    total_chars: int
    crawl_duration_secs: float


# ---------------------------------------------------------------------------
# Noise selectors — mirrors web-analyzer/src/server.js noiseSelectors array
# ---------------------------------------------------------------------------
_NOISE_SELECTORS = [
    "header", "footer", "nav", "aside", "noscript", "iframe", "canvas", "svg",
    "button", "form", "input", "select", "textarea", "style", "script",
    "audio", "video",
    # menus
    ".menu", "[class^='menu-']", "[class$='-menu']", "[class*='menu-container']",
    ".nav", "[class^='nav-']", "[class$='-nav']", "[class*='nav-container']",
    ".navbar", "[class^='navbar-']", "[class$='-navbar']",
    # sidebars
    ".sidebar", "[class^='sidebar-']", "[class$='-sidebar']",
    ".sidebar-container",
    # footers / headers
    ".footer", "[class^='footer-']", "[class$='-footer']",
    ".header", "[class^='header-']", "[class$='-header']",
    # id-based
    "[id*='menu']", "[id*='nav']", "[id*='sidebar']",
    "[id*='footer']", "[id*='header']",
    # boilerplate
    ".widget", ".widget-area", ".breadcrumbs", ".breadcrumb",
    ".social", ".social-links", ".sharing", ".social-share",
    ".cookie-consent", ".cookie-banner", ".cookie", "#cookie",
    ".banner", ".ad", ".advertisement",
    ".popup", ".modal", ".overlay",
    ".comments", "#comments", ".disqus", ".reply",
    ".newsletter-signup", ".subscribe",
    "[aria-hidden='true']",
    # e-commerce
    ".shopify-section", ".payment-buttons", ".shopify-payment-button",
    ".cart-drawer", ".mini-cart", ".cart-popup",
    ".announcement-bar", ".promo-bar", ".discount-code", ".newsletter-popup",
    # screen-reader utilities
    ".visually-hidden", ".sr-only",
]

# Static asset extensions to skip when following links
_SKIP_EXTENSIONS = {
    ".pdf", ".zip", ".tar", ".gz", ".png", ".jpg", ".jpeg", ".gif", ".svg",
    ".mp4", ".mp3", ".wav", ".avi", ".mov",
    ".docx", ".xlsx", ".pptx", ".csv",
    ".js", ".css", ".xml", ".json",
}

# Browser-like User-Agent — avoids bot-detection 403s on most CDN-protected sites
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

_ACCEPT_HEADER = "text/html,application/xhtml+xml,application/xhtml,*/*;q=0.9"

# Max content-markdown length per page — matches web-analyzer's 12 000-char limit
_PAGE_MARKDOWN_LIMIT = 12_000

# Heading text values that indicate nav/menu noise rather than real content
_NAV_HEADING_TEXTS = {"menu", "navigation", "quick links", "useful links", "social media"}

# Maximum total wall-clock time for a single URL crawl job.
# 5 minutes gives enough headroom for 15 pages × 45 s timeout with concurrent
# workers, while still bounding runaway jobs.
_CRAWL_BUDGET_SECS = 300

# Thread-local storage for per-thread curl_cffi sessions
_thread_local = threading.local()


def _build_client() -> cffi_requests.Session:
    """Return a configured synchronous curl_cffi session."""
    return cffi_requests.Session(
        timeout=settings.SCRAPE_TIMEOUT_SECS,
        impersonate="chrome120",
        headers={"Accept": _ACCEPT_HEADER},
        allow_redirects=True,
        max_redirects=5,
    )


def _get_thread_client() -> cffi_requests.Session:
    """Lazily create and cache a Session per thread."""
    client = getattr(_thread_local, "client", None)
    if client is None:
        client = _build_client()
        _thread_local.client = client
    return client


def _normalize_url(url: str) -> str:
    """Normalize a URL for dedup: strip query/fragment, trailing slash,
    www. prefix, and lowercase scheme+host."""
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    hostname = parsed.hostname or ""
    if hostname.startswith("www."):
        hostname = hostname[4:]
    port = parsed.port
    netloc = f"{hostname}:{port}" if port else hostname
    path = parsed.path
    # Strip trailing slash unless the path is root "/"
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    return f"{scheme}://{netloc}{path}"


def _clean_soup(soup: BeautifulSoup) -> None:
    """Remove noise elements from a BeautifulSoup tree in-place."""
    # Remove noise selectors
    for selector in _NOISE_SELECTORS:
        for el in soup.select(selector):
            el.decompose()

    # Remove heading elements that are pure navigation labels
    for heading in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        text = heading.get_text().strip().lower()
        if text in _NAV_HEADING_TEXTS:
            # Also remove the immediately following list/nav/div if it exists
            nxt = heading.find_next_sibling()
            if nxt and nxt.name in ("ul", "ol", "nav", "div"):
                nxt.decompose()
            heading.decompose()

    # Remove lists that contain only anchor jump-links (#hash)
    def _is_jump_link_item(li) -> bool:
        links = li.find_all("a")
        return bool(links) and all(a.get("href", "").startswith("#") for a in links)

    for lst in soup.find_all(["ul", "ol"]):
        items = lst.find_all("li")
        if items and all(_is_jump_link_item(li) for li in items):
            lst.decompose()

    # Strip all images (avoids broken markdown image tags)
    for img in soup.find_all("img"):
        img.decompose()


def _html_to_markdown(soup: BeautifulSoup) -> str:
    """
    Extract main content from soup and convert to clean Markdown.
    Mirrors the web-analyzer turndown conversion.
    """
    # Try to find a main content container.
    # Avoid picking a single <article> if there are multiple (e.g. blog index),
    # to prevent losing most of the page's content.
    content_el = None
    for selector in [
        lambda: soup.find("main"),
        lambda: soup.find(attrs={"role": "main"}),
        lambda: soup.find(id=re.compile(r"content|main", re.I)),
        lambda: soup.find(class_=re.compile(r"content|main", re.I)),
        lambda: soup.find("article") if len(soup.find_all("article")) == 1 else None,
        lambda: soup.find("body"),
    ]:
        content_el = selector()
        if content_el:
            break

    html_fragment = str(content_el) if content_el else str(soup)

    raw_md = md(
        html_fragment,
        heading_style="atx",
        bullets="-",
        strip=["script", "style", "img"],  # preserve anchor text for semantic context
    )

    # Clean stray symbols and collapse blank lines — mirrors web-analyzer post-processing
    lines = []
    for line in raw_md.split("\n"):
        stripped = line.strip()
        if stripped in ("→", "←", "»", "«", "—"):
            lines.append("")
        else:
            lines.append(line.rstrip())

    cleaned = "\n".join(lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned[:_PAGE_MARKDOWN_LIMIT]


def _extract_internal_links(soup: BeautifulSoup, base_url: str) -> list[str]:
    """Extract and normalize all internal links from the page."""
    parsed_origin = urlparse(base_url)
    origin_host = parsed_origin.netloc.split(":")[0].lower()
    if origin_host.startswith("www."):
        origin_host = origin_host[4:]

    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        link_text = a.get_text().strip()

        if not href or href.startswith(("#", "javascript")) or len(link_text) <= 1:
            continue

        try:
            resolved = urlparse(urljoin(base_url, href))
            resolved_host = resolved.netloc.split(":")[0].lower()
            if resolved_host.startswith("www."):
                resolved_host = resolved_host[4:]

            if resolved.scheme in ("http", "https") and resolved_host == origin_host:
                resolved_str = _normalize_url(resolved.geturl())
                if not any(resolved.path.lower().endswith(ext) for ext in _SKIP_EXTENSIONS):
                    links.append(resolved_str)
        except Exception:
            pass

    return links


def _scrape_page_sync(url: str) -> dict:
    """
    Scrape a single page synchronously using a per-thread curl_cffi session.
    Returns a dict with keys: url, title, content_markdown, links, error.
    Mirrors web-analyzer's scrapeURL() function.
    """
    client = _get_thread_client()
    try:
        resp = client.get(url)
        resp.raise_for_status()

        # Reject non-HTML content (PDFs, ZIPs, images, etc.)
        content_type = resp.headers.get("content-type", "")
        if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
            raise ValueError(f"Unsupported content type: {content_type}")

        soup = BeautifulSoup(resp.text, "html.parser")

        # Extract metadata before cleaning the DOM
        title = (
            (soup.find("head") and soup.find("head").find("title") and soup.find("head").find("title").get_text(strip=True))
            or (soup.find("title") and soup.find("title").get_text(strip=True))
            or (soup.find("h1") and soup.find("h1").get_text(strip=True))
            or "Untitled"
        )

        # Collect internal links before noise removal alters the tree
        links = _extract_internal_links(soup, url)

        logger.info("Url: %s - Extracted %d raw links, filtered to %d internal links", url, len(soup.find_all("a")), len(links))
        _clean_soup(soup)
        content_markdown = _html_to_markdown(soup)

        return {
            "url": url,
            "title": title,
            "content_markdown": content_markdown,
            "links": links,
            "error": None,
        }

    except RequestsError as exc:
        status_code = getattr(exc.response, 'status_code', None) if hasattr(exc, 'response') and exc.response else None

        if status_code:
            if status_code == 403:
                msg = "Access blocked (403 Forbidden). This site uses Cloudflare or a firewall."
            elif status_code == 401:
                msg = "This page requires login/authentication."
            elif status_code == 404:
                msg = "Page not found (404)."
            elif status_code == 429:
                msg = "Rate limited (429). The site is blocking too-frequent requests."
            elif status_code >= 500:
                msg = f"The website's server returned an error ({status_code})."
            else:
                msg = f"HTTP error {status_code} while crawling this page."
            logger.warning("Scrape failed for %s: %s", url, msg)
            return {"url": url, "title": "", "content_markdown": "", "links": [], "error": msg}

        # If it's a timeout or connection error (curl_cffi raises RequestsError for these too)
        msg = f"Network or timeout error: {exc}"
        logger.warning("Request error for %s: %s", url, exc)
        return {"url": url, "title": "", "content_markdown": "", "links": [], "error": msg}

    except ValueError as exc:
        # Raised by our content-type guard (PDFs, ZIPs, etc.)
        msg = (
            f"Unsupported content: {exc}. "
            "Only HTML web pages can be crawled — PDF/ZIP/image links are not supported."
        )
        logger.warning("Unsupported content at %s: %s", url, exc)
        return {"url": url, "title": "", "content_markdown": "", "links": [], "error": msg}

    except Exception as exc:
        msg = f"Unexpected error while crawling: {exc}"
        logger.warning("Unexpected scrape error for %s: %s", url, exc)
        return {"url": url, "title": "", "content_markdown": "", "links": [], "error": msg}


def _crawl_site_sync(
    start_url: str,
    max_pages: int = None,
    max_depth: int = None,
) -> tuple[list[dict], int, float]:
    """
    BFS multi-page crawl starting at start_url using ThreadPoolExecutor for concurrent requests.
    Mirrors web-analyzer's crawlSite() function with level-based concurrency.

    Returns a tuple of (page_dicts, pages_crawled, crawl_duration_secs).
    If the root page fails, raises immediately so the job is marked FAILED.
    """
    max_pages = max_pages or settings.SCRAPE_MAX_PAGES
    max_depth = max_depth or settings.SCRAPE_MAX_DEPTH

    visited: set[str] = set()
    results: list[dict] = []
    crawl_start = time.monotonic()

    # Normalize the start URL for consistent visited-set tracking
    norm_start = _normalize_url(start_url)

    # We BFS crawl by depth levels in parallel
    current_depth_urls = [start_url]

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        try:
            for depth in range(max_depth + 1):
                if not current_depth_urls or len(results) >= max_pages:
                    break

                # Filter out already visited URLs
                urls_to_crawl = []
                for url in current_depth_urls:
                    norm = _normalize_url(url)
                    if norm not in visited:
                        visited.add(norm)
                        urls_to_crawl.append(url)

                if not urls_to_crawl:
                    continue

                # Limit to remaining page slots
                remaining_slots = max_pages - len(results)
                urls_to_crawl = urls_to_crawl[:remaining_slots]

                logger.info("Crawling depth %d in parallel: %d pages...", depth, len(urls_to_crawl))

                # Map scraping tasks to thread pool (each worker uses its own client)
                futures = {executor.submit(_scrape_page_sync, url): url for url in urls_to_crawl}

                next_depth_links = []
                for future in concurrent.futures.as_completed(futures):
                    url = futures[future]
                    try:
                        page = future.result()
                        if page["error"] and depth == 0:
                            raise RuntimeError(f"Failed to scrape the starting URL: {page['error']}")
                        results.append(page)
                        if not page["error"]:
                            next_depth_links.extend(page["links"])
                    except Exception as exc:
                        if depth == 0:
                            raise RuntimeError(f"Failed to scrape the starting URL: {exc}")
                        logger.warning("Scrape task failed for %s: %s", url, exc)

                # Prepare next level URLs (deduplicate links)
                current_depth_urls = list(dict.fromkeys(next_depth_links))

                if time.monotonic() - crawl_start > _CRAWL_BUDGET_SECS:
                    logger.warning(
                        "Crawl budget of %ds exceeded for %s — stopping.",
                        _CRAWL_BUDGET_SECS, start_url
                    )
                    break

                # Brief pause between depth levels to avoid rate-limiting by target servers
                time.sleep(0.3)
        finally:
            # Clean up per-thread httpx clients created by workers
            # (the executor is shutting down so workers are done)
            pass

    crawl_duration = time.monotonic() - crawl_start
    return results, len(results), crawl_duration


def _pages_to_text(pages: list[dict]) -> str:
    """
    Concatenate crawled page Markdowns into a single string for chunking.
    Each page is separated by a YAML-like frontmatter header (mirrors
    web-analyzer's generateConsolidatedMarkdown).
    """
    parts = []
    for page in pages:
        if not page.get("content_markdown"):
            continue
        header = f"# {page['title'] or 'Untitled'}\n\n*Source: {page['url']}*\n\n"
        parts.append(header + page["content_markdown"])
    return "\n\n---\n\n".join(parts)


# ---------------------------------------------------------------------------
# Public TextExtractor class
# ---------------------------------------------------------------------------

class TextExtractor:
    @staticmethod
    def extract_pdf(file_path: str) -> str:
        text = []
        with fitz.open(file_path) as doc:
            for page in doc:
                text.append(page.get_text())
        return "\n".join(text)

    @staticmethod
    def extract_docx(file_path: str) -> str:
        doc = docx.Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs])

    @staticmethod
    def extract_txt(file_path: str) -> str:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    @staticmethod
    def extract_csv(file_path: str) -> str:
        text = []
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            for row in reader:
                text.append(", ".join(row))
        return "\n".join(text)

    @staticmethod
    def extract_url_sync(url: str) -> CrawlResult:
        """
        Synchronous multi-page crawl + Markdown extraction.
        Safe to call from APScheduler threads or any sync context.
        Returns a CrawlResult with consolidated Markdown and crawl metadata.
        Raises RuntimeError if the root URL cannot be scraped or content is too thin.
        """
        pages, pages_crawled, crawl_duration = _crawl_site_sync(url)
        text = _pages_to_text(pages)

        if len(text) < 50:
            raise RuntimeError(
                "No readable content found. The site may require JavaScript "
                "rendering or may be blocking automated access."
            )

        return CrawlResult(
            text=text,
            pages_crawled=pages_crawled,
            total_chars=len(text),
            crawl_duration_secs=round(crawl_duration, 2),
        )

    @staticmethod
    def validate_url_sync(url: str) -> dict:
        """
        Quickly check if a single URL is crawlable without traversing links.
        Raises ValueError if it's not crawlable.
        Returns metadata about the page.
        """
        page = _scrape_page_sync(url)
        if page["error"]:
            raise ValueError(page["error"])
        if len(page["content_markdown"]) < 50:
            raise ValueError(
                "No readable content found. The site may require JavaScript "
                "rendering or may be blocking automated access."
            )
        return {
            "links_found": len(page["links"])
        }

    @staticmethod
    async def extract_url(url: str) -> CrawlResult:
        """
        Async wrapper kept for API-level use.
        Delegates to the sync implementation via a thread to avoid blocking the
        event loop during long crawls.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, TextExtractor.extract_url_sync, url)
