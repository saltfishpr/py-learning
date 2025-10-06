import logging
import os

from bs4 import BeautifulSoup
from rich.progress import Progress

from scraper import scrape

log = logging.getLogger(__name__)


def _get_book_detail(html: str) -> dict[str, str]:
    """
    通过 book_id 获取该书详情。
    """
    soup = BeautifulSoup(html, "html.parser")

    bookbox_div = soup.select_one("div.bookbox")
    if not bookbox_div:
        return {}

    booknav2_div = bookbox_div.select_one("div.booknav2")
    if not booknav2_div:
        return {}

    details: dict[str, str] = {}

    title_tag = booknav2_div.select_one("h1 a")
    details["title"] = title_tag.text.strip() if title_tag else ""

    author_tag = booknav2_div.select_one('p a[href*="author.php"]')
    details["author"] = author_tag.text.strip() if author_tag else ""

    p_tags = booknav2_div.select("p")
    for p in p_tags:
        text = p.text.strip()
        if "万字" in text and "|" in text:
            word_count, status = text.split("|")
            details["word_count"] = word_count.strip()
            details["status"] = status.strip()
        elif text.startswith("更新："):
            details["update_time"] = text.replace("更新：", "").strip()

    return details


def _get_chapter_links(html: str) -> dict[int, str]:
    """
    通过 book_id 获取该书章节 url 列表。
    """
    soup = BeautifulSoup(html, "html.parser")

    links: dict[int, str] = {}
    catalog = soup.select_one("#catalog")
    if catalog:
        for li in catalog.select("ul li"):
            data_num_val = li.get("data-num")
            data_num_str = (
                data_num_val[0] if isinstance(data_num_val, list) else str(data_num_val)
            )
            chapter_num = int(data_num_str)

            a = li.find("a")
            if a and a.get("href"):
                href_val = a.get("href")
                href_str = href_val[0] if isinstance(href_val, list) else str(href_val)
                links[chapter_num] = href_str.strip()
    return links


def _get_chapter_content(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    # 获取 class 为 txtnav 的 div 元素
    content_div = soup.select_one("div.txtnav")
    if content_div:
        # 排除 class 为 hide720 的元素和 id 为 txtright 的元素
        for element in content_div.select(".hide720, #txtright"):
            element.decompose()
        return content_div.get_text(separator="\n", strip=True)
    return ""


def download(book_id: str, output_dir: str = "output/69shuba"):
    book_dir = f"{output_dir}/{book_id}"
    os.makedirs(book_dir, exist_ok=True)

    book_detail_html = scrape(f"https://www.69shuba.com/book/{book_id}.htm")
    book_detail = _get_book_detail(book_detail_html)
    # 存储 book_detail
    with open(f"{book_dir}/index.json", "w", encoding="utf-8") as f:
        import json

        json.dump(book_detail, f, ensure_ascii=False, indent=4)

    # 获取章节列表
    catalog_html = scrape(f"https://www.69shuba.com/book/{book_id}/")
    chapter_links = _get_chapter_links(catalog_html)

    with Progress() as progress:
        task = progress.add_task(
            f"[cyan]Scraping book {book_id}...", total=len(chapter_links)
        )

        for id, link in chapter_links.items():
            progress.update(task, advance=1, description=f"Scraping chapter {id}")

            filename = f"{book_dir}/{id}.txt"
            if os.path.exists(filename):
                log.info(f"Chapter {id} already exists, skipping...")
                continue

            chapter_html = scrape(link)
            chapter_content = _get_chapter_content(chapter_html)
            # 存储章节内容
            with open(filename, "w", encoding="utf-8") as f:
                f.write(chapter_content)

    # 将章节内容合并为一个文件
    title = book_detail.get("title", "full")
    with open(f"{book_dir}/{title}.txt", "w", encoding="utf-8") as full_file:
        for id in sorted(chapter_links.keys()):
            chapter_file = f"{book_dir}/{id}.txt"
            if os.path.exists(chapter_file):
                with open(chapter_file, "r", encoding="utf-8") as f:
                    full_file.write(f.read() + "\n\n")  # 章节间隔两个换行符
