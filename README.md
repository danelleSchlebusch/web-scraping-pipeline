# Polite Scraper

A Python web scraper that collects and normalizes book information from the **Books to Scrape** sandbox website.

The scraper discovers the first three catalogue pages, collects book URLs, fetches the individual book pages, extracts the required information, validates the records with Pydantic, and writes the normalized results to JSON.

---

## Target classification

**Books to Scrape sandbox**

The scraper targets the first **3 catalogue pages** and collects:

* Book title
* Price
* Availability
* Rating
* Book URL

The scraper also records additional metadata such as the source catalogue page and the time the record was fetched.

---

## Project lane

**Polite web scraper**

This project is designed to demonstrate responsible web scraping practices, including identifying the scraper, using timeouts, caching responses, limiting requests, and handling failures without crashing the entire run.

---

## Requirements

* Python 3.12+
* pip

---

## Installation

Clone the repository and navigate into the project:

```bash
git clone https://github.com/danelleSchlebusch/web-scraping-pipeline.git
cd web-scraping-pipeline
```

Install the project and its dependencies:

```bash
pip install -e .
```

---

## Run the scraper

Run the scraper with:

```bash
python src/main.py
```

The scraper writes its results to the `output/` directory:

```text
output/
├── books.json
├── errors.json
└── run-report.json
```

### Output files

**`books.json`**

Contains the normalized and validated book records successfully collected by the scraper.

**`errors.json`**

Contains information about records or requests that could not be processed successfully.

**`run-report.json`**

Contains a summary of the scraper run, including timing, page activity, cache usage, valid records, invalid records, and failed pages.

---

## Record schema

Each normalized book record contains the following fields:

| Field               | Description                                  |
| ------------------- | -------------------------------------------- |
| `title`             | Book title                                   |
| `price_text`        | Original price text                          |
| `price_gbp`         | Price converted to a numeric GBP value       |
| `product_url`       | URL of the individual book page              |
| `availability_text` | Availability information                     |
| `rating_text`       | Book rating                                  |
| `description`       | Book description when available              |
| `source_page`       | Catalogue page where the book was discovered |
| `fetched_at`        | Time the record was fetched                  |

The records are validated using **Pydantic** before being written to `books.json`.

---

## Scraping process

The scraper follows this process:

1. Fetch the catalogue page.
2. Cache the HTML response locally.
3. Discover product URLs from the catalogue.
4. Follow the catalogue's next-page links until 3 catalogue pages have been processed.
5. Fetch each individual product page.
6. Cache the product-page HTML.
7. Extract and normalize the book information.
8. Validate each record using Pydantic.
9. Save valid records to `books.json`.
10. Save errors to `errors.json`.
11. Write a run summary to `runreport.json`.

The scraper discovered **60 unique book URLs** across the first three catalogue pages.

---

## Politeness rules

The scraper follows several rules to reduce unnecessary load on the website.

### User-Agent

The scraper identifies itself with the following User-Agent:

```text
FlyRankInternshipA9/1.0 (+https://github.com/danelleSchlebusch/web-scraping-pipeline.git)
```

### Request timeout

HTTP requests use a **5-second timeout** so that an unresponsive request does not cause the scraper to wait indefinitely.

### Delay

A **0.5-second delay** is used between requests.

### Caching

Fetched HTML pages are stored locally in the `cache/` directory.

If a cached page already exists, the scraper uses the cached response instead of making another HTTP request.

The cache directory is excluded from Git so that the repository does not contain hundreds of cached HTML files.

### Catalogue limit

The scraper deliberately stops catalogue discovery after **3 catalogue pages** rather than crawling the entire website.

### Failure handling

The scraper records failures and continues processing where possible instead of allowing one failed request or invalid record to terminate the entire run.

---

## Why this scraper does not need a browser

This assignment does not need a browser because the required data is already present in the HTML sent by the server. A browser would only add unnecessary cost and complexity.

---

## Limitation

The scraper depends on the current HTML structure of the target website.

If the website changes its page structure, HTML elements, or CSS classes used by the scraper, some fields may no longer be extracted correctly and the scraper may need to be updated.

---

## Ethics

This scraper is intended for responsible data collection.

Use an official API when one exists. Never bypass logins, paywalls, or blocks. Collect only the data that is needed for the task.

The fact that a website does not have a `robots.txt` file should not automatically be treated as permission to scrape it.

I will not reuse this code on another site without checking its rules and terms first.

---

## Sample run report

The following is a real run report generated by the scraper:

```json
{
  "start_time": "2026-09-23T12:11:48Z",
  "duration": 3.48,
  "pages_fetched": 0,
  "cache_hits": 63,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 0
}
```

> The exact `start_time` and `duration` values will vary between runs. The report above documents the structure and evidence from a real scraper run.

---

## Repository structure

```text
web-scraping-pipeline/
│
├── src/
│   ├── main.py
│   └── models.py
│
├── output/
│   ├── books.json
│   ├── errors.json
│   └── run-report.json
│
├── .gitignore
├── README.md
└── pyproject.toml
```

The local `cache/` directory is used by the scraper but is excluded from the Git repository.

---

## Evidence

The project includes:

* Normalized book records in `output/books.json`
* Error information in `output/errors.json`
* A run summary in `output/run-report.json`
* Pydantic validation of normalized records
* Multiple meaningful stage commits documenting development

A stranger should be able to clone the repository, install the project, run the documented command, and obtain the scraper output without needing the cached HTML files.
