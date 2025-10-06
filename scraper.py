import os

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


@retry(
    stop=stop_after_attempt(3),  # 最多重试 3 次
    wait=wait_exponential(multiplier=1, min=1, max=10),  # 指数退避
    retry=retry_if_exception_type(httpx.ReadTimeout),
)
def scrape(url: str) -> str:
    return scrape_with_scraperapi(url)


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

    import time

    time.sleep(1)  # 避免请求过于频繁

    return resp.text
