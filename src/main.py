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
    if "page-" in url:
        page_name = url.rstrip("/").split("/")[-1]
    else:
        product_id = url.rstrip("/").split("/")[-2].split("_")[-1]
        page_name = f"detail-{product_id}.html"

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

    html = response.content.decode("utf-8")

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(html, encoding="utf-8")

    print(f"FETCH — {page_name} — {len(html)} bytes")

    time.sleep(0.5)

    return html

def discover_catalogue():
    page_url = URL

    catalogue_pages = 0
    discovered_books = []
    seen_urls = set()

    while page_url and catalogue_pages < 3:
        html = fetch_and_cache(page_url)

        soup = BeautifulSoup(html, "html.parser")

        catalogue_pages += 1

        for link in soup.select("article.product_pod h3 a"):
            href = link.get("href")

            if href:
                book_url = urljoin(page_url, href)

                if book_url not in seen_urls:
                    seen_urls.add(book_url)

                    discovered_books.append({
                    "product_url": book_url,
                    "source_page": page_url
                    })

        next_link = soup.select_one("li.next a")

        if next_link:
            next_href = next_link.get("href")
            page_url = urljoin(page_url, next_href)
        else:
            page_url = None

    print(f"catalogue_pages={catalogue_pages}")
    print(f"discovered={len(discovered_books)}")
    print(f"unique_urls={len(seen_urls)}")

    return discovered_books

def extract_book_details(book):
    html = fetch_and_cache(book["product_url"])

    soup = BeautifulSoup(html, "html.parser")

    product = soup.select_one("article.product_page")

    if product is None:
        raise RuntimeError(
            f"Product area not found: {book['product_url']}"
        )

    title = product.select_one("h1")
    price = product.select_one(".price_color")
    availability = product.select_one(".availability")
    rating = product.select_one("p.star-rating")

    description = product.select_one("#product_description + p")

    rating_text = None

    if rating:
        rating_classes = rating.get("class", [])

        for rating_class in rating_classes:
            if rating_class != "star-rating":
                rating_text = rating_class
                break

    description_text = None

    if description:
        description_text = description.get_text(strip=True)

    return {
        "title": title.get_text(strip=True) if title else None,
        "product_url": book["product_url"],
        "price_text": price.get_text(strip=True) if price else None,
        "availability_text": (
            availability.get_text(" ", strip=True)
            if availability
            else None
        ),
        "rating_text": rating_text,
        "description": description_text,
        "source_page": book["source_page"],
        "fetched_at": time.strftime(
            "%Y-%m-%dT%H:%M:%SZ",
            time.gmtime()
        )
    }

if __name__ == "__main__":
    books = discover_catalogue()

    detail_records = []

    for book in books:
        record = extract_book_details(book)
        detail_records.append(record)

    print(detail_records[0])
    print(f"detail_pages={len(detail_records)}")