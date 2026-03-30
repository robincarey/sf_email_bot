import logging
import random
import time

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BASE_URL = "https://www.foliosociety.com"
LISTING_URL = "https://www.foliosociety.com/usa/sci-fi-fantasy"
STORE_NAME = "Folio Society - Sci-Fi & Fantasy"


def _get_with_retry(session, url, max_retries=3, timeout=15):
    """GET with exponential backoff. Raises on final failure."""
    for attempt in range(max_retries):
        try:
            resp = session.get(url, timeout=timeout)
            resp.raise_for_status()
            return resp
        except requests.RequestException:
            if attempt == max_retries - 1:
                raise
            wait = 2 ** attempt + random.uniform(0, 1)
            logger.warning(
                f"Retry {attempt + 1}/{max_retries} for {url} (waiting {wait:.1f}s)"
            )
            time.sleep(wait)


def _extract_link(product):
    """Extract product URL from the title href block."""
    href_block = product.find("href", class_="block")
    link_tag = href_block.find("a", href=True) if href_block else None
    if not link_tag:
        return None

    href = link_tag["href"]
    if href.startswith("http://") or href.startswith("https://"):
        return href
    if href.startswith("/"):
        return f"{BASE_URL}{href}"
    return f"{BASE_URL}/{href}"


def _extract_in_stock(product):
    """Folio marks out-of-stock products with product-label text."""
    label = product.find("product-label")
    out_of_stock_p = label.find("p") if label else None
    return not (out_of_stock_p and "out of stock" in out_of_stock_p.get_text(strip=True).lower())


def _normalize_price(price_text):
    """Normalize region-prefixed prices like 'US$10' -> '$10'."""
    return price_text.strip().replace("US$", "$").replace("US $", "$")


def folio_society_checks():
    product_list = []

    with requests.Session() as session:
        session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Connection": "keep-alive",
                "Referer": BASE_URL,
            }
        )

        response = _get_with_retry(session, LISTING_URL)
        soup = BeautifulSoup(response.content, "html.parser")
        products = soup.find_all("product")

        logger.info(f"Found {len(products)} products on Folio Society listing page.")

        for product in products:
            name_el = product.find("span", class_="_name")
            price_el = product.find("price")
            link = _extract_link(product)

            if not name_el or not price_el or not link:
                logger.warning("Skipping product due to missing required fields.")
                continue

            product_list.append(
                {
                    "name": name_el.get_text(strip=True),
                    "price": _normalize_price(price_el.get_text(strip=True)),
                    "store": STORE_NAME,
                    "link": link,
                    "in_stock": _extract_in_stock(product),
                }
            )

            time.sleep(random.uniform(0.05, 0.2))

    return product_list


if __name__ == "__main__":
    test_array = folio_society_checks()
    for entry in test_array:
        for key, value in entry.items():
            print(f"{key}: {value}", end=" | ")
        print()
