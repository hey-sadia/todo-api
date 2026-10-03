import os
import json
import re
import time
from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel

USER_AGENT = "FlyRankInternshipA9/1.0 (+https://github.com/hey-sadia/todo-api)"
TIMEOUT = 10  # seconds
DELAY = 0.5   # seconds between real requests
CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "cache")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")

SITE = "https://books.toscrape.com/catalogue/"


def fetch_page(url, cache_filename):
    """Fetch a page, using a cached copy if we already have one."""
    cache_path = os.path.join(CACHE_DIR, cache_filename)

    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            html = f.read()
        print(f"CACHE HIT: {cache_filename} ({len(html)} bytes)")
        return html

    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
    if response.status_code != 200:
        raise Exception(f"status code {response.status_code}")

    response.encoding = "utf-8"
    html = response.text

    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"FETCH: {cache_filename} ({len(html)} bytes)")
    time.sleep(DELAY)  # be polite only on real requests
    return html


def discover_book_links():
    """Visit the first 3 catalogue pages, return unique (book_url, source_page)."""
    found = []
    seen = set()
    pages = 0
    for n in range(1, 4):
        page_url = f"{SITE}page-{n}.html"
        html = fetch_page(page_url, f"catalogue/page-{n}.html")
        pages += 1
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.select("article.product_pod h3 a"):
            book_url = urljoin(page_url, a["href"])
            if book_url not in seen:
                seen.add(book_url)
                found.append((book_url, page_url))
    print(f"catalogue_pages={pages} unique_urls={len(found)}")
    return found


def extract_book_record(url, source_page):
    """Download one book page and pull out the raw fields."""
    slug = url.rstrip("/").split("/")[-2]
    html = fetch_page(url, f"books/{slug}.html")
    soup = BeautifulSoup(html, "html.parser")

    title = soup.select_one("div.product_main h1").get_text(strip=True)
    price_text = soup.select_one("p.price_color").get_text(strip=True)
    availability_text = " ".join(
        soup.select_one("p.availability").get_text().split()
    )
    rating_classes = soup.select_one("p.star-rating")["class"]
    rating_text = [c for c in rating_classes if c != "star-rating"][0]

    description = ""
    desc_box = soup.select_one("#product_description")
    if desc_box:
        p = desc_box.find_next_sibling("p")
        if p:
            description = p.get_text(strip=True)

    return {
        "title": title,
        "product_url": url,
        "price_text": price_text,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def extract_all_books(book_links):
    """Visit every book page. A failed page is logged, not fatal."""
    records = []
    fetch_errors = []
    for url, source_page in book_links:
        try:
            records.append(extract_book_record(url, source_page))
        except Exception as e:
            print(f"FAILED: {url} -> {e}")
            fetch_errors.append({"product_url": url, "error": str(e)})

    print(f"detail_pages={len(records)} failed={len(fetch_errors)}")
    return records, fetch_errors


class Book(BaseModel):
    title: str
    product_url: str
    price_gbp: float
    availability_text: str
    rating_text: str
    description: str = ""
    source_page: str
    fetched_at: str


def parse_price(price_text):
    """Turn '£51.77' into 51.77"""
    match = re.search(r"\d+(?:\.\d+)?", price_text)
    if not match:
        raise ValueError(f"Cannot parse price: {price_text!r}")
    return float(match.group())


def validate_books(records):
    """Split records into valid books and errors."""
    valid = []
    errors = []
    for record in records:
        try:
            data = dict(record)
            data["price_gbp"] = parse_price(data.pop("price_text"))
            valid.append(Book(**data).model_dump())
        except Exception as e:
            errors.append({
                "product_url": record.get("product_url"),
                "error": str(e),
            })
    return valid, errors


def save_json(data, filename):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, filename), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    started = datetime.now(timezone.utc)
    links = discover_book_links()

    # Stage 5 test: add one bad URL on purpose
    links.append((
        "https://books.toscrape.com/catalogue/this-page-does-not-exist_999/index.html",
        "https://books.toscrape.com/catalogue/page-1.html",
    ))

    records, fetch_errors = extract_all_books(links)
    valid, validation_errors = validate_books(records)
    all_errors = fetch_errors + validation_errors

    save_json(valid, "books.json")
    save_json(all_errors, "errors.json")

    finished = datetime.now(timezone.utc)
    report = {
        "started_at": started.isoformat(),
        "finished_at": finished.isoformat(),
        "duration_seconds": round((finished - started).total_seconds(), 2),
        "urls_attempted": len(links),
        "pages_fetched": len(records),
        "fetch_failures": len(fetch_errors),
        "records_valid": len(valid),
        "records_invalid": len(validation_errors),
    }
    save_json(report, "run-report.json")
    print(f"\nvalid={len(valid)} errors={len(all_errors)}")
