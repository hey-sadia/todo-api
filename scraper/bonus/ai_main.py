import json
import logging
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field, HttpUrl, ValidationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Constants
BASE_URL = "https://books.toscrape.com/"
CACHE_DIR = Path(".cache")
DATA_DIR = Path("data")
DELAY_SECONDS = 1.0
TIMEOUT_SECONDS = 10
HEADERS = {
    "User-Agent": (
        "PoliteScraperBot/1.0 (+https://github.com/example/politescraper; "
        "contact@example.com)"
    )
}

# Rating mapping from CSS class names to numbers
RATING_MAP = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
}


# --- Pydantic Data Model ---
class BookSchema(BaseModel):
    title: str = Field(..., min_length=1)
    price: float = Field(..., ge=0.0)
    availability: str = Field(..., min_length=1)
    rating: Optional[int] = Field(None, ge=1, le=5)
    description: str
    product_url: HttpUrl
    source_page: HttpUrl
    fetched_time: str


# --- Helper Functions ---
def sanitize_filename(url: str) -> str:
    """Create a safe filesystem filename from a URL."""
    sanitized = re.sub(r"[^a-zA-Z0-9_-]", "_", url)
    return f"{sanitized}.html"


def fetch_page_with_cache(url: str, session: requests.Session) -> str:
    """Fetch HTML content from cache if available, otherwise fetch from web and cache it."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / sanitize_filename(url)

    if cache_file.exists():
        logger.info(f"Loading from cache: {url}")
        return cache_file.read_text(encoding="utf-8")

    logger.info(f"Fetching from web: {url}")
    # Politeness delay before network requests
    time.sleep(DELAY_SECONDS)

    response = session.get(url, headers=HEADERS, timeout=TIMEOUT_SECONDS)
    response.raise_for_status()

    # Save to cache
    cache_file.write_text(response.text, encoding="utf-8")
    return response.text


def parse_price(price_str: str) -> float:
    """Convert price string like '£51.77' to float 51.77."""
    clean_price = re.sub(r"[^\d.]", "", price_str)
    return float(clean_price)


def parse_rating(tag: BeautifulSoup) -> Optional[int]:
    """Extract rating integer from star-rating class."""
    rating_tag = tag.find(class_=re.compile(r"star-rating"))
    if not rating_tag:
        return None
    
    classes = rating_tag.get("class", [])
    for cls in classes:
        cls_lower = cls.lower()
        if cls_lower in RATING_MAP:
            return RATING_MAP[cls_lower]
    return None


def parse_book_detail(html_content: str, product_url: str, source_page: str) -> dict:
    """Extract book details from product page HTML."""
    soup = BeautifulSoup(html_content, "html.parser")

    # Title
    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else ""

    # Price
    price_tag = soup.find("p", class_="price_color")
    price_raw = price_tag.get_text(strip=True) if price_tag else "0.0"
    price = parse_price(price_raw)

    # Availability
    avail_tag = soup.find("p", class_="instock availability")
    availability = avail_tag.get_text(strip=True) if avail_tag else ""

    # Rating
    rating = parse_rating(soup)

    # Description
    desc_header = soup.find("div", id="product_description")
    description = ""
    if desc_header:
        desc_p = desc_header.find_next_sibling("p")
        if desc_p:
            description = desc_p.get_text(strip=True)

    fetched_time = datetime.now(timezone.utc).isoformat()

    return {
        "title": title,
        "price": price,
        "availability": availability,
        "rating": rating,
        "description": description,
        "product_url": product_url,
        "source_page": source_page,
        "fetched_time": fetched_time,
    }


def extract_book_urls(catalog_html: str, source_page_url: str) -> List[str]:
    """Extract product detail page URLs from a catalogue page."""
    soup = BeautifulSoup(catalog_html, "html.parser")
    article_tags = soup.find_all("article", class_="product_pod")

    urls = []
    for article in article_tags:
        a_tag = article.find("h3").find("a") if article.find("h3") else None
        if a_tag and a_tag.get("href"):
            full_url = urljoin(source_page_url, a_tag["href"])
            urls.append(full_url)
    return urls


# --- Main Execution ---
def main():
    start_time = time.time()
    session = requests.Session()

    valid_books: List[dict] = []
    error_records: List[dict] = []
    catalogue_pages_processed = 0

    # Process first 3 catalogue pages
    catalogue_urls = [
        urljoin(BASE_URL, "catalogue/page-1.html"),
        urljoin(BASE_URL, "catalogue/page-2.html"),
        urljoin(BASE_URL, "catalogue/page-3.html"),
    ]

    for source_url in catalogue_urls:
        logger.info(f"Processing catalogue page: {source_url}")
        try:
            cat_html = fetch_page_with_cache(source_url, session)
            book_urls = extract_book_urls(cat_html, source_url)
            catalogue_pages_processed += 1
        except Exception as e:
            logger.error(f"Failed to fetch catalogue page {source_url}: {e}")
            error_records.append({
                "page_url": source_url,
                "error": f"Catalogue fetch failed: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            continue

        for book_url in book_urls:
            try:
                book_html = fetch_page_with_cache(book_url, session)
                raw_data = parse_book_detail(book_html, book_url, source_url)

                # Validate record using Pydantic
                validated_book = BookSchema(**raw_data)
                # Convert model to json-serializable dict
                valid_books.append(validated_book.model_dump(mode="json"))

            except ValidationError as ve:
                logger.warning(f"Validation failed for {book_url}: {ve}")
                error_records.append({
                    "product_url": book_url,
                    "source_page": source_url,
                    "error": ve.errors(),
                    "raw_data": raw_data if "raw_data" in locals() else None,
                })
            except Exception as e:
                logger.error(f"Failed to process book page {book_url}: {e}")
                error_records.append({
                    "product_url": book_url,
                    "source_page": source_url,
                    "error": str(e),
                })

    # Save output JSON files
    with open("books.json", "w", encoding="utf-8") as f:
        json.dump(valid_books, f, indent=2, ensure_ascii=False)

    with open("errors.json", "w", encoding="utf-8") as f:
        json.dump(error_records, f, indent=2, ensure_ascii=False)

    end_time = time.time()
    duration = round(end_time - start_time, 2)

    # Save run report
    report = {
        "catalogue_pages_requested": len(catalogue_urls),
        "catalogue_pages_processed": catalogue_pages_processed,
        "valid_books_count": len(valid_books),
        "errors_count": len(error_records),
        "execution_time_seconds": duration,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    with open("run-report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info("Scraping completed!")
    logger.info(f"Summary: {len(valid_books)} valid books saved to books.json")
    logger.info(f"Errors: {len(error_records)} saved to errors.json")
    logger.info(f"Report saved to run-report.json in {duration}s")


if __name__ == "__main__":
    main()