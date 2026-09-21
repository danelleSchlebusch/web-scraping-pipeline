from pathlib import Path
from urllib.parse import urljoin
import time

import requests
from bs4 import BeautifulSoup


URL = "https://books.toscrape.com/catalogue/page-1.html"

CACHE_DIR = Path("cache")

HEADERS = {
    "User-Agent": "FlyRankInternshipA9/1.0 (+https://github.com/danelleSchlebusch/web-scraping-pipeline.git)"
}


def fetch_and_cache(url):
    page_name = url.rstrip("/").split("/")[-1]
    cache_file = CACHE_DIR / page_name

    if cache_file.exists():
        html = cache_file.read_text(encoding="utf-8")
        print(f"CACHE HIT — {page_name} — {len(html)} bytes")
        return html

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=5
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Fetch failed with status code {response.status_code}"
        )

    html = response.text

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(html, encoding="utf-8")

    print(f"FETCH — {page_name} — {len(html)} bytes")

    time.sleep(0.5)

    return html

def discover_catalogue():
    page_url = URL

    catalogue_pages = 0
    discovered_urls = []
    seen_urls = set()

    while page_url and catalogue_pages < 3:
        html = fetch_and_cache(page_url)

        soup = BeautifulSoup(html, "html.parser")

        catalogue_pages += 1

        for link in soup.select("article.product_pod h3 a"):
            href = link.get("href")

            if href:
                book_url = urljoin(page_url, href)
                discovered_urls.append(book_url)

        next_link = soup.select_one("li.next a")

        if next_link:
            next_href = next_link.get("href")
            page_url = urljoin(page_url, next_href)
        else:
            page_url = None

    for url in discovered_urls:
        seen_urls.add(url)

    print(f"catalogue_pages={catalogue_pages}")
    print(f"discovered={len(discovered_urls)}")
    print(f"unique_urls={len(seen_urls)}")

    return seen_urls

if __name__ == "__main__":
    discover_catalogue()