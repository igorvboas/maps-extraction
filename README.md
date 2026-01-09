# Google Maps Leads Scraper API

A FastAPI-based REST API that extracts business leads (Name, Category, Phone) from Google Maps using Playwright.

## Prerequisites

- Python 3.8+
- [Playwright interactions](https://playwright.dev/python/docs/intro)

## Setup

1.  **Clone the repository** (or navigate to current directory).
2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Install Playwright browsers**:
    ```bash
    playwright install chromium
    ```

## Running the API

1.  Start the server:
    ```bash
    uvicorn app.main:app --reload
    ```
2.  The API will be available at `http://localhost:8000`.
3.  Interactive documentation (Swagger UI) at `http://localhost:8000/docs`.

## Usage

**Endpoint**: `POST /search`

**Request Body**:
```json
{
  "city": "London",
  "state": "England",
  "country": "UK",
  "query": "pubs"
}
```

**Response**:
```json
[
  {
    "name": "The Churchill Arms",
    "category": "Pub",
    "phone": "+44 20 7727 4242",
    "address": null,
    "url": null
  },
  ...
]
```

## Configuration

- `HEADLESS=True` in `.env` to run browser in headless mode. Set to `False` for debugging.
