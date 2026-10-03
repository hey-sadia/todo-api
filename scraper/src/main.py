import os
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

USER_AGENT = "FlyRankInternshipA9/1.0 (+https://github.com/hey-sadia/todo-api)"
TIMEOUT = 10  # seconds
DELAY = 0.5   # seconds between real requests
CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "cache")

BASE_URL = "https://books.toscrape.com/catalogue/page-1.html"


def fetch_page(url: str, cache_filename: str) -> str:
    """Fetch a page, using a cached copy if we already have one."""
    cache_path = os.path.join(CACHE_DIR, cache_filename)

    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            html = f.read()
        print(f"CACHE HIT: {cache_filename} ({len(html)} bytes)")
        return html

    headers = {"User-Agent": USER_AGENT}
    response = requests.get(url, headers=headers, timeout=TIMEOUT)

    if response.status_code != 200:
        raise Exception(f"Failed to fetch {url}: status code {response.status_code}")

    html = response.text

    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"FETCH: {cache_filename} ({len(html)} bytes)")
    time.sleep(DELAY)  # be polite only on real requests
    return html


def discover_book_links():
    """Visit the first 3 catalogue pages and collect all unique book URLs."""
    all_links = []
    current_url = BASE_URL
    page_number = 1

    while current_url and page_number <= 3:
        cache_filename = f"catalogue-page-{page_number}.html"
        html = fetch_page(current_url, cache_filename)
        soup = BeautifulSoup(html, "html.parser")

        # Collect book links on this page
        for article in soup.select("article.product_pod"):
            a_tag = article.select_one("h3 a")
            if a_tag and a_tag.get("href"):
                absolute_url = urljoin(current_url, a_tag["href"])
                all_links.append(absolute_url)

        # Find the "next" link, if any
        next_tag = soup.select_one("li.next a")
        if next_tag and next_tag.get("href") and page_number < 3:
            current_url = urljoin(current_url, next_tag["href"])
            page_number += 1
        else:
            current_url = None

    unique_links = list(dict.fromkeys(all_links))  # remove duplicates, keep order

    print(f"catalogue_pages={page_number}")
    print(f"discovered={len(all_links)}")
    print(f"unique_urls={len(unique_links)}")

    return unique_links


if __name__ == "__main__":
    links = discover_book_links()