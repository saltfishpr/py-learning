import logging
import os

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

log = logging.getLogger(__name__)


@retry(
    stop=stop_after_attempt(3),  # 最多重试 3 次
    wait=wait_exponential(multiplier=1, min=1, max=10),  # 指数退避
    retry=retry_if_exception_type(httpx.ReadTimeout),
)
def scrape(url: str) -> str:
    return scrape_with_oxylabs(url)


def scrape_direct(url: str) -> str:
    """
    直接使用 httpx 抓取网页内容。
    """
    resp = httpx.get(url, timeout=10).raise_for_status()

    _sleep(1)  # 避免请求过于频繁

    return resp.text


def scrape_with_zenrows(url: str) -> str:
    """
    使用 zenrows 抓取网页内容。
    """
    params = {
        "url": url,
        "apikey": os.environ.get("ZENROWS_API_KEY"),
        "mode": "auto",
    }

    resp = httpx.get(
        "https://api.zenrows.com/v1/", params=params
    ).raise_for_status()

    _sleep(1)  # 避免请求过于频繁

    return resp.text


def scrape_with_scraperapi(url: str) -> str:
    """
    使用 scraperapi 抓取网页内容。
    """
    payload = {
        "api_key": os.environ.get("SCRAPER_API_KEY"),
        "url": url,
    }
    resp = httpx.get(
        "https://api.scraperapi.com/",
        params=payload,
        timeout=10,
    ).raise_for_status()

    _sleep(1)  # 避免请求过于频繁

    return resp.text


def scrape_with_firecrawl(url: str) -> str:
    """
    使用 firecrawl 抓取网页内容。
    """
    payload = {
        "url": url,
        "formats": ["html"],
    }

    headers = {
        "Authorization": f"Bearer {os.environ.get('FIRECRAWL_API_KEY')}",
        "Content-Type": "application/json",
    }

    resp = httpx.post(
        "https://api.firecrawl.dev/v2/scrape",
        json=payload,
        headers=headers,
        timeout=10,
    ).raise_for_status()

    data = resp.json()
    return data.get("data", {}).get("html", "")


def scrape_with_oxylabs(url: str) -> str:
    """
    使用 Oxylabs 抓取网页内容。
    """
    payload = {
        "source": "universal",
        "url": url,
        "render": "html",  # If page type requires
        "user_agent_type": "desktop",
        "geo_location": "United States",
    }

    resp = httpx.post(
        "https://realtime.oxylabs.io/v1/queries",
        json=payload,
        auth=(
            os.environ.get("OXYLABS_USER", ""),
            os.environ.get("OXYLABS_PASS", ""),
        ),
        timeout=60,
    ).raise_for_status()

    data = resp.json()
    return data.get("results", [])[0].get("content", "")


def _sleep(seconds: int):
    import time

    time.sleep(seconds)
