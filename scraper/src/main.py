import os
import time
from datetime import datetime, timezone
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

    response.encoding = "utf-8"
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

        for article in soup.select("article.product_pod"):
            a_tag = article.select_one("h3 a")
            if a_tag and a_tag.get("href"):
                absolute_url = urljoin(current_url, a_tag["href"])
                all_links.append(absolute_url)

        next_tag = soup.select_one("li.next a")
        if next_tag and next_tag.get("href") and page_number < 3:
            current_url = urljoin(current_url, next_tag["href"])
            page_number += 1
        else:
            current_url = None

    unique_links = list(dict.fromkeys(all_links))

    print(f"catalogue_pages={page_number}")
    print(f"discovered={len(all_links)}")
    print(f"unique_urls={len(unique_links)}")

    return unique_links


def extract_book_record(book_url: str, source_page: str) -> dict:
    """Fetch one book's detail page and pull out the raw fields."""
    # Build a safe cache filename from the URL
    safe_name = book_url.rstrip("/").split("/")[-2] + ".html"
    cache_filename = os.path.join("books", safe_name)

    full_cache_path = os.path.join(CACHE_DIR, cache_filename)
    os.makedirs(os.path.dirname(full_cache_path), exist_ok=True)

    html = fetch_page(book_url, cache_filename)
    soup = BeautifulSoup(html, "html.parser")

    product_main = soup.select_one("div.product_main")

    title = product_main.select_one("h1").get_text(strip=True) if product_main else None

    price_tag = soup.select_one("p.price_color")
    price_text = price_tag.get_text(strip=True) if price_tag else None

    availability_tag = soup.select_one("p.instock.availability")
    availability_text = availability_tag.get_text(strip=True) if availability_tag else None

    rating_tag = soup.select_one("p.star-rating")
    rating_text = None
    if rating_tag:
        classes = rating_tag.get("class", [])
        for c in classes:
            if c != "star-rating":
                rating_text = c

    description_heading = soup.select_one("#product_description")
    description = None
    if description_heading:
        desc_tag = description_heading.find_next_sibling("p")
        if desc_tag:
            description = desc_tag.get_text(strip=True)

    record = {
        "title": title,
        "product_url": book_url,
        "price_text": price_text,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
    return record


def extract_all_books(book_links):
    """Visit every book page and extract raw records."""
    records = []
    for link in book_links:
        record = extract_book_record(link, source_page=BASE_URL)
        records.append(record)

    print(f"detail_pages={len(records)}")
    return records


if __name__ == "__main__":
    links = discover_book_links()
    records = extract_all_books(links)
    print("\nSample record:")
    print(records[0])