import os
import time
import requests

USER_AGENT = "FlyRankInternshipA9/1.0 (+https://github.com/hey-sadia/todo-api)"
TIMEOUT = 10  # seconds
CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "cache")


def fetch_page(url: str, cache_filename: str) -> str:
    """Fetch a page, using a cached copy if we already have one."""
    cache_path = os.path.join(CACHE_DIR, cache_filename)

    # If we already have a cached copy, use it instead of hitting the site again.
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            html = f.read()
        print(f"CACHE HIT: {cache_filename} ({len(html)} bytes)")
        return html

    # Otherwise, fetch it for real.
    headers = {"User-Agent": USER_AGENT}
    response = requests.get(url, headers=headers, timeout=TIMEOUT)

    if response.status_code != 200:
        raise Exception(f"Failed to fetch {url}: status code {response.status_code}")

    html = response.text

    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"FETCH: {cache_filename} ({len(html)} bytes)")
    return html


if __name__ == "__main__":
    url = "https://books.toscrape.com/catalogue/page-1.html"
    fetch_page(url, "catalogue-page-1.html")