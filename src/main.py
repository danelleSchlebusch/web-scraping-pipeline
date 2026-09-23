from pathlib import Path
from urllib.parse import urljoin
import json
import time

import requests
from bs4 import BeautifulSoup
from pydantic import ValidationError

from models import Book

URL = "https://books.toscrape.com/catalogue/page-1.html"

CACHE_DIR = Path("cache")
OUTPUT_DIR = Path("output")

HEADERS = {
    "User-Agent": "FlyRankInternshipA9/1.0 (+https://github.com/danelleSchlebusch/web-scraping-pipeline.git)"
}

def normalize_price(price_text: str) -> float:
    return float(price_text.replace("£", "").strip())

BASE_URL = "https://books.toscrape.com/"

def normalize_url(product_url: str) -> str:
    return urljoin(BASE_URL, product_url)

def fetch_and_cache(url, stats):
    if "page-" in url:
        page_name = url.rstrip("/").split("/")[-1]
    else:
        product_id = url.rstrip("/").split("/")[-2].split("_")[-1]
        page_name = f"detail-{product_id}.html"

    cache_file = CACHE_DIR / page_name

    if cache_file.exists():
        html = cache_file.read_text(encoding="utf-8")
        stats["cache_hits"] += 1

        print(f"CACHE HIT — {page_name} — {len(html)} bytes")
        return html

    attempts = 2

    for attempt in range(1, attempts + 1):
        try:
            response = requests.get(
                url,
                headers=HEADERS,
                timeout=5
            )

            if response.status_code == 200:
                html = response.content.decode("utf-8")

                CACHE_DIR.mkdir(parents=True, exist_ok=True)
                cache_file.write_text(html, encoding="utf-8")

                stats["pages_fetched"] += 1

                print(f"FETCH — {page_name} — {len(html)} bytes")

                time.sleep(0.5)

                return html

            if response.status_code == 404:
                raise RuntimeError(
                    f"Fetch failed with status code 404"
                )

            if response.status_code == 403:
                raise RuntimeError(
                    f"Fetch failed with status code 403"
                )

            if 500 <= response.status_code <= 599:
                if attempt == 1:
                    print(
                        f"SERVER ERROR {response.status_code} — "
                        f"retrying {page_name}"
                    )
                    time.sleep(1)
                    continue

                raise RuntimeError(
                    f"Fetch failed with status code {response.status_code}"
                )

            raise RuntimeError(
                f"Fetch failed with status code {response.status_code}"
            )

        except requests.Timeout:
            if attempt == 1:
                print(
                    f"TIMEOUT — retrying {page_name}"
                )
                time.sleep(1)
                continue

            raise RuntimeError(
                f"Fetch timed out after {attempts} attempts"
            )

def discover_catalogue(stats):
    page_url = URL

    catalogue_pages = 0
    discovered_books = []
    seen_urls = set()

    while page_url and catalogue_pages < 3:
        try:
            html = fetch_and_cache(page_url, stats)

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

        except Exception as error:
            stats["failed_pages"] += 1

            print(
                f"FAILED CATALOGUE PAGE — {page_url} — {error}"
            )

            break

    print(f"catalogue_pages={catalogue_pages}")
    print(f"discovered={len(discovered_books)}")
    print(f"unique_urls={len(seen_urls)}")

    return discovered_books

def extract_book_details(book, stats):
    html = fetch_and_cache(book["product_url"], stats)

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
    start_time = time.time()

    stats = {
        "pages_fetched": 0,
        "cache_hits": 0,
        "valid_records": 0,
        "invalid_records": 0,
        "failed_pages": 0
    }

    books = discover_catalogue(stats)

    detail_records = {}
    errors = []

    for book in books:
        try:
            record = extract_book_details(book, stats)

            record["price_gbp"] = normalize_price(record["price_text"])
            record["product_url"] = normalize_url(record["product_url"])
            record["source_page"] = normalize_url(record["source_page"])

            validated_book = Book(**record)

            detail_records[validated_book.product_url] = validated_book

        except ValidationError as error:
            stats["invalid_records"] += 1

            errors.append({
                "product_url": book["product_url"],
                "reason": error.errors()
            })

        except Exception as error:
            stats["failed_pages"] += 1

            errors.append({
                "product_url": book["product_url"],
                "reason": str(error)
            })

            print(
                f"FAILED — {book['product_url']} — {error}"
            )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    books_output = [
        book.model_dump(mode="json")
        for book in detail_records.values()
    ]

    books_file = OUTPUT_DIR / "books.json"
    books_file.write_text(
        json.dumps(books_output, indent=2),
        encoding="utf-8"
    )

    errors_file = OUTPUT_DIR / "errors.json"
    errors_file.write_text(
        json.dumps(errors, indent=2),
        encoding="utf-8"
    )

    duration = time.time() - start_time

    stats["valid_records"] = len(detail_records)

    run_report = {
        "start_time": time.strftime(
            "%Y-%m-%dT%H:%M:%SZ",
            time.gmtime(start_time)
        ),
        "duration": round(duration, 2),
        "pages_fetched": stats["pages_fetched"],
        "cache_hits": stats["cache_hits"],
        "valid_records": stats["valid_records"],
        "invalid_records": stats["invalid_records"],
        "failed_pages": stats["failed_pages"]
    }

    run_report_file = OUTPUT_DIR / "run-report.json"

    run_report_file.write_text(
        json.dumps(run_report, indent=2),
        encoding="utf-8"
    )

    print(f"valid_records={stats['valid_records']}")
    print(f"invalid_records={stats['invalid_records']}")
    print(f"failed_pages={stats['failed_pages']}")