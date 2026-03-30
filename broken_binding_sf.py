import requests
import time
import random
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def _get_with_retry(session, url, max_retries=3, timeout=10):
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
            logger.warning(f"Retry {attempt + 1}/{max_retries} for {url} (waiting {wait:.1f}s)")
            time.sleep(wait)


def broken_binding_checks():
    urls = [
        {"url": "https://thebrokenbindingsub.com/collections/to-the-stars", "store": "Broken Binding - To The Stars"},
        {"url": "https://thebrokenbindingsub.com/collections/the-infirmary", "store": "Broken Binding - The Infirmary"},
        {"url": "https://thebrokenbindingsub.com/collections/dragons-hoard", "store": "Broken Binding - Dragon's Hoard"},
        {"url": "https://thebrokenbindingsub.com/collections/the-graveyard", "store": "Broken Binding - The Graveyard"},
    ]
    # Intentionally do NOT dedupe by `link` here.
    # The same product URL can appear in multiple Broken Binding collections; the
    # lambda will canonicalize per-link for items_seen/events, while still preserving
    # multi-store membership for email/store matching.
    product_list = []

    with requests.Session() as session:
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Referer": "https://thebrokenbindingsub.com/"
        })
        # Warm up the session; best-effort, failures are non-fatal
        try:
            _get_with_retry(session, "https://thebrokenbindingsub.com/")
            time.sleep(random.uniform(0.2, 0.5))
        except requests.RequestException:
            pass

        for entry in urls:
            base_url = entry['url']
            store = entry['store']
            page = 1

            while True:
                paginated_url = f"{base_url}?page={page}"
                try:
                    response = _get_with_retry(session, paginated_url)
                except requests.RequestException as e:
                    logger.error(f"Error fetching collection {paginated_url}: {e}")
                    break
                soup = BeautifulSoup(response.content, "html.parser")

                time.sleep(random.uniform(0.2, 0.5))

                product_items = soup.find_all("li", class_="grid__item")
                if not product_items:
                    break

                for product in product_items:
                    # Ensure these variables always exist even if the page structure changes.
                    in_stock = False
                    link = None
                    heading = product.find("h3", class_="card__heading")
                    if heading:
                        link_tag = heading.find("a", class_="full-unstyled-link")
                        product_name = link_tag.get_text(strip=True) if link_tag else "No name found"
                        href = link_tag.get('href') if link_tag else None
                        if not href:
                            continue

                        link = "https://thebrokenbindingsub.com" + href
                        try:
                            product_response = _get_with_retry(session, link)
                        except requests.RequestException as e:
                            logger.error(f"Error fetching product {link}: {e}")
                            continue
                        product_soup = BeautifulSoup(product_response.content, "html.parser")
                        cart_button = product_soup.find("button", class_="product-form__submit")
                        if not cart_button or "Sold out" in cart_button.get_text(strip=True):
                            in_stock = False
                        else:
                            in_stock = True
                    else:
                        product_name = "No name found"

                    price_span = (
                        product.find("span", class_="price-item--sale") or
                        product.find("span", class_="price-item--regular")
                    )
                    product_price = price_span.get_text(strip=True) if price_span else "No price found"

                    if not link:
                        continue

                    product_list.append({
                        'name': product_name,
                        'price': product_price,
                        'store': store,
                        'link': link,
                        'in_stock': in_stock
                    })

                    time.sleep(random.uniform(0.2, 0.6))

                logger.info(f"Scraped {store} page {page}: {len(product_items)} products")
                page += 1

    return product_list


if __name__ == "__main__":
    test_array = broken_binding_checks()
    for entry in test_array:
        for key, value in entry.items():
            print(f"{key}: {value}", end=" | ")
        print()
