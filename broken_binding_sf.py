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
    # Dedupe by canonical product link. This avoids duplicate constrained-key rows
    # inside a single upsert call to Supabase (e.g. `upsert(... on_conflict="link")`).
    products_by_link = {}

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

                    existing = products_by_link.get(link)
                    if existing:
                        # If any scrape instance shows the item is in stock, keep that.
                        if not existing.get('in_stock') and in_stock:
                            existing['in_stock'] = in_stock

                        # Prefer a real price over "No price found".
                        if (
                            existing.get('price') == 'No price found' and
                            product_price != 'No price found'
                        ):
                            existing['price'] = product_price

                        # Keep the most informative fields we have.
                        if existing.get('name') == 'No name found' and product_name != 'No name found':
                            existing['name'] = product_name

                        # Store naming can differ if a product appears in multiple collections.
                        # Using the latest seen store keeps the catalog updated.
                        existing['store'] = store
                    else:
                        products_by_link[link] = {
                            'name': product_name,
                            'price': product_price,
                            'store': store,
                            'link': link,
                            'in_stock': in_stock
                        }

                    time.sleep(random.uniform(0.2, 0.6))

                logger.info(f"Scraped {store} page {page}: {len(product_items)} products")
                page += 1

    return list(products_by_link.values())


if __name__ == "__main__":
    test_array = broken_binding_checks()
    for entry in test_array:
        for key, value in entry.items():
            print(f"{key}: {value}", end=" | ")
        print()
