import time
import asyncio
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class FirecrawlResult:
    text: str
    pages_crawled: int
    total_chars: int
    crawl_duration_secs: float
    title: Optional[str] = None
    pages: Optional[List[Dict[str, Any]]] = None


class FirecrawlService:
    """
    Service for web scraping and multi-page crawling via Firecrawl API.
    Converts web pages into clean, LLM-ready Markdown while handling
    JavaScript execution, SPAs, and anti-bot protections.
    """

    @classmethod
    def get_api_key(cls) -> str:
        return settings.FIRECRAWL_API_KEY.strip()

    @classmethod
    def get_base_url(cls) -> str:
        return (settings.FIRECRAWL_API_URL or "https://api.firecrawl.dev").rstrip("/")

    @classmethod
    def is_configured(cls) -> bool:
        return bool(cls.get_api_key())

    @classmethod
    def _get_headers(cls) -> Dict[str, str]:
        api_key = cls.get_api_key()
        if not api_key:
            raise ValueError(
                "Firecrawl API key is not configured. Please add FIRECRAWL_API_KEY to your .env file."
            )
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    @classmethod
    async def scrape_url_async(cls, url: str) -> Dict[str, Any]:
        """
        Asynchronously scrape a single URL using Firecrawl /v1/scrape.
        """
        base_url = cls.get_base_url()
        headers = cls._get_headers()
        payload = {
            "url": url,
            "formats": ["markdown"],
            "onlyMainContent": True,
        }

        async with httpx.AsyncClient(timeout=settings.SCRAPE_TIMEOUT_SECS) as client:
            try:
                response = await client.post(
                    f"{base_url}/v1/scrape",
                    headers=headers,
                    json=payload,
                )
                if response.status_code == 401:
                    raise ValueError("Invalid Firecrawl API key. Please check your FIRECRAWL_API_KEY.")
                if response.status_code == 402:
                    raise ValueError("Firecrawl account credit limit reached. Please check your Firecrawl credits.")
                if response.status_code == 429:
                    raise ValueError("Firecrawl rate limit exceeded. Please try again in a few moments.")
                
                response.raise_for_status()
                data = response.json()

                if not data.get("success", False) and "data" not in data:
                    error_msg = data.get("error", "Unknown error from Firecrawl")
                    raise RuntimeError(f"Firecrawl scrape failed: {error_msg}")

                scrape_data = data.get("data", {})
                markdown = scrape_data.get("markdown", "") or ""
                metadata = scrape_data.get("metadata", {}) or {}
                title = metadata.get("title") or metadata.get("og:title") or "Website Page"

                return {
                    "url": url,
                    "title": title,
                    "markdown": markdown,
                    "metadata": metadata,
                    "links": scrape_data.get("links", []),
                }

            except httpx.HTTPStatusError as e:
                logger.error("Firecrawl HTTP error %s for url %s: %s", e.response.status_code, url, e.response.text)
                raise RuntimeError(f"Firecrawl HTTP error {e.response.status_code}: {e.response.text}")
            except httpx.RequestError as e:
                logger.error("Firecrawl connection error for url %s: %s", url, str(e))
                raise RuntimeError(f"Failed to connect to Firecrawl API: {str(e)}")

    @classmethod
    def scrape_url(cls, url: str) -> Dict[str, Any]:
        """
        Synchronous wrapper for scrape_url_async.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(cls.scrape_url_async(url))
        else:
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                return executor.submit(asyncio.run, cls.scrape_url_async(url)).result()

    @classmethod
    async def crawl_site_async(
        cls,
        url: str,
        limit: Optional[int] = None,
        max_depth: Optional[int] = None,
        poll_interval: float = 3.0,
        max_wait_secs: float = 240.0,
    ) -> FirecrawlResult:
        """
        Asynchronously crawl a website starting at url up to limit pages.
        Uses Firecrawl /v1/crawl and non-blocking asyncio.sleep polling until complete.
        Falls back to single-page scrape if crawl creation is unsupported or fails.
        """
        start_time = time.monotonic()
        limit = limit or settings.SCRAPE_MAX_PAGES
        max_depth = max_depth or settings.SCRAPE_MAX_DEPTH
        base_url = cls.get_base_url()
        headers = cls._get_headers()

        payload = {
            "url": url,
            "limit": limit,
            "maxDepth": max_depth,
            "scrapeOptions": {
                "formats": ["markdown"],
                "onlyMainContent": True,
            },
        }

        async with httpx.AsyncClient(timeout=settings.SCRAPE_TIMEOUT_SECS) as client:
            # 1. Initiate crawl
            try:
                response = await client.post(
                    f"{base_url}/v1/crawl",
                    headers=headers,
                    json=payload,
                )
                
                if response.status_code == 401:
                    raise ValueError("Invalid Firecrawl API key. Please check your FIRECRAWL_API_KEY.")
                if response.status_code == 402:
                    raise ValueError("Firecrawl account credit limit reached. Please check your Firecrawl credits.")
                
                response.raise_for_status()
                crawl_init = response.json()
            except Exception as e:
                logger.warning("Firecrawl /v1/crawl endpoint failed (%s). Falling back to single-page scrape.", e)
                # Fallback to single page scrape
                scraped = await cls.scrape_url_async(url)
                duration = time.monotonic() - start_time
                md_text = scraped["markdown"]
                if len(md_text.strip()) < 30:
                    raise RuntimeError("No readable content could be extracted from this website.")
                return FirecrawlResult(
                    text=md_text,
                    pages_crawled=1,
                    total_chars=len(md_text),
                    crawl_duration_secs=round(duration, 2),
                    title=scraped["title"],
                )

            crawl_id = crawl_init.get("id")
            if not crawl_id:
                # If synchronous or returned directly
                data_items = crawl_init.get("data", [])
                return cls._format_crawl_data(data_items, start_time)

            # 2. Non-blocking status polling
            status_url = f"{base_url}/v1/crawl/{crawl_id}"
            elapsed = 0.0

            while elapsed < max_wait_secs:
                await asyncio.sleep(poll_interval)
                elapsed = time.monotonic() - start_time

                try:
                    poll_resp = await client.get(status_url, headers=headers)
                    poll_resp.raise_for_status()
                    poll_data = poll_resp.json()
                    
                    status = poll_data.get("status")
                    if status == "completed":
                        data_items = poll_data.get("data", [])
                        return cls._format_crawl_data(data_items, start_time)
                    elif status == "failed":
                        error_msg = poll_data.get("error", "Crawl failed on Firecrawl.")
                        raise RuntimeError(f"Firecrawl crawl failed: {error_msg}")
                    elif status in ("scraping", "processing", "active"):
                        logger.info(
                            "Firecrawl job %s in progress... (completed %s/%s pages)",
                            crawl_id,
                            poll_data.get("completed", 0),
                            poll_data.get("total", "?"),
                        )
                        continue
                except (httpx.HTTPStatusError, httpx.RequestError) as poll_err:
                    logger.warning("Error polling Firecrawl status: %s", poll_err)
                    continue

            # If polling times out
            raise TimeoutError(f"Firecrawl crawl timed out after {int(elapsed)} seconds.")

    @classmethod
    def crawl_site(
        cls,
        url: str,
        limit: Optional[int] = None,
        max_depth: Optional[int] = None,
        poll_interval: float = 3.0,
        max_wait_secs: float = 240.0,
    ) -> FirecrawlResult:
        """
        Synchronous wrapper for crawl_site_async.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(
                cls.crawl_site_async(url, limit, max_depth, poll_interval, max_wait_secs)
            )
        else:
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                return executor.submit(
                    asyncio.run,
                    cls.crawl_site_async(url, limit, max_depth, poll_interval, max_wait_secs)
                ).result()

    @classmethod
    def _format_crawl_data(cls, data_items: List[Dict[str, Any]], start_time: float) -> FirecrawlResult:
        """Format Firecrawl page list into a consolidated Markdown document."""
        if not data_items:
            raise RuntimeError("No content was returned from Firecrawl for this website.")

        parts = []
        first_title = None

        for item in data_items:
            md_content = item.get("markdown", "") or ""
            metadata = item.get("metadata", {}) or {}
            page_url = metadata.get("sourceURL") or metadata.get("url") or "Website Page"
            page_title = metadata.get("title") or metadata.get("og:title") or "Untitled"

            if not first_title and page_title != "Untitled":
                first_title = page_title

            if md_content.strip():
                header = f"# {page_title}\n\n*Source: {page_url}*\n\n"
                parts.append(header + md_content.strip())

        consolidated_text = "\n\n---\n\n".join(parts)
        duration = time.monotonic() - start_time

        if len(consolidated_text.strip()) < 30:
            raise RuntimeError("No readable content could be extracted from this website.")

        return FirecrawlResult(
            text=consolidated_text,
            pages_crawled=len(data_items),
            total_chars=len(consolidated_text),
            crawl_duration_secs=round(duration, 2),
            title=first_title or "Website Knowledge",
            pages=data_items,
        )

    @classmethod
    def validate_url(cls, url: str) -> Dict[str, Any]:
        """
        Validate if a URL is accessible and scrapable by Firecrawl.
        """
        if not cls.is_configured():
            raise ValueError(
                "Firecrawl API key is missing. Please add FIRECRAWL_API_KEY to your backend .env file."
            )
        
        result = cls.scrape_url(url)
        markdown = result.get("markdown", "")
        if len(markdown.strip()) < 30:
            raise ValueError("The website returned empty content or is inaccessible.")

        links = result.get("links", [])
        return {
            "status": "ok",
            "title": result.get("title", "Website Page"),
            "links_found": len(links),
            "chars_extracted": len(markdown),
        }
