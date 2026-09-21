from pathlib import Path
import requests


URL = "https://books.toscrape.com/catalogue/page-1.html"

CACHE_FILE = Path("cache/catalogue-page-1.html")

HEADERS = {
    "User-Agent": "FlyRankInternshipA9/1.0 (+https://github.com/danelleSchlebusch/web-scraping-pipeline.git)"
}


def fetch_and_cache():
    if CACHE_FILE.exists():
        html = CACHE_FILE.read_text(encoding="utf-8")
        print(f"CACHE HIT — {len(html)} bytes")
        return html

    response = requests.get(
        URL,
        headers=HEADERS,
        timeout=5
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Fetch failed with status code {response.status_code}"
        )

    html = response.text

    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(html, encoding="utf-8")

    print(f"FETCH — {len(html)} bytes")

    return html


if __name__ == "__main__":
    fetch_and_cache()