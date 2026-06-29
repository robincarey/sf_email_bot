import requests
import time
import random
import logging
from bs4 import BeautifulSoup

from open_library import extract_isbn_from_text

logger = logging.getLogger(__name__)

# Cap on any single backoff/Retry-After sleep so one throttled product can't stall a run.
MAX_BACKOFF_SECONDS = 30

# Shopify vendor field is the retailer, not the book author on Broken Binding.
_IGNORED_SHOPIFY_VENDORS = frozenset(
    {
        "the broken binding ltd.",
        "the broken binding",
        "broken binding",
    }
)


def extract_product_author(product_soup) -> str | None:
    """Author from Broken Binding Shopify product detail markup."""
    el = product_soup.select_one("p.productInfo__author, .productInfo__author")
    if not el:
        return None
    text = el.get_text(strip=True)
    return text or None


def extract_isbn_from_html(product_soup) -> str | None:
    """Best-effort ISBN from product detail markup or description."""
    chunks: list[str] = []
    for el in product_soup.select(
        ".productInfo, .product__description, .product__info-container, [class*='product']"
    ):
        text = el.get_text(" ", strip=True)
        if text:
            chunks.append(text)
    return extract_isbn_from_text(" ".join(chunks))


def cover_and_isbn_from_shopify_json(product_data: dict) -> tuple[str | None, str | None]:
    """Extract cover URL and ISBN from a Shopify product JSON payload."""
    product = product_data.get("product") or {}
    images = product.get("images") or []
    cover_url = images[0].get("src") if images else None
    if cover_url:
        cover_url = cover_url.strip() or None

    isbn = None
    for variant in product.get("variants") or []:
        barcode = (variant.get("barcode") or "").strip().replace("-", "")
        if barcode:
            isbn = barcode
            break

    if not isbn:
        isbn = extract_isbn_from_text(product.get("body_html"))

    return cover_url, isbn


def author_from_shopify_json(product_data: dict) -> str | None:
    """Best-effort author from product JSON (vendor is usually the store, not author)."""
    vendor = (product_data.get("product") or {}).get("vendor")
    if not vendor:
        return None
    normalized = vendor.strip().lower()
    if normalized in _IGNORED_SHOPIFY_VENDORS:
        return None
    return vendor.strip()


def item_media_from_shopify_js(data: dict) -> tuple[bool, str | None, str | None]:
    """(in_stock, cover_url, isbn) from a Shopify product `.js` payload.

    Unlike `.json`, the `.js` endpoint includes top-level `available`, so a single
    request yields stock status plus cover/ISBN — no separate product-page fetch.
    """
    in_stock = bool(data.get("available"))

    cover_url = None
    images = data.get("images") or []
    if images:
        cover_url = images[0]
    elif data.get("featured_image"):
        cover_url = data.get("featured_image")
    if cover_url:
        cover_url = cover_url.strip()
        if cover_url.startswith("//"):
            cover_url = "https:" + cover_url
        cover_url = cover_url or None

    isbn = None
    for variant in data.get("variants") or []:
        barcode = (variant.get("barcode") or "").strip().replace("-", "")
        if barcode:
            isbn = barcode
            break

    return in_stock, cover_url, isbn


def shopify_js_tags(data: dict) -> list[str]:
    """Tags from a `.js` payload (list) or `.json` payload (comma string)."""
    raw = data.get("tags") or []
    if isinstance(raw, list):
        return [str(t).strip() for t in raw]
    return [t.strip() for t in str(raw).split(",")]


def _retry_after_seconds(resp) -> float | None:
    """Parse a Retry-After header in delta-seconds form into float seconds."""
    if resp is None:
        return None
    raw = resp.headers.get("Retry-After")
    if not raw:
        return None
    try:
        return max(0.0, float(raw))
    except (TypeError, ValueError):
        # HTTP-date form is uncommon for Shopify; fall back to backoff.
        return None


def _get_with_retry(session, url, max_retries=4, timeout=15):
    """GET with retries. Honors Retry-After on 429; raises on final failure.

    Non-429 client errors (e.g. 404) are not retried since they won't recover.
    """
    for attempt in range(max_retries):
        resp = None
        try:
            resp = session.get(url, timeout=timeout)
            resp.raise_for_status()
            return resp
        except requests.HTTPError:
            status = resp.status_code if resp is not None else None
            if status is not None and status != 429 and 400 <= status < 500:
                raise
            if attempt == max_retries - 1:
                raise
            retry_after = _retry_after_seconds(resp)
            wait = retry_after if retry_after is not None else 2 ** attempt + random.uniform(0, 1)
            wait = min(wait, MAX_BACKOFF_SECONDS)
            logger.warning(
                f"Retry {attempt + 1}/{max_retries} for {url} "
                f"(status={status}, waiting {wait:.1f}s)"
            )
            time.sleep(wait)
        except requests.RequestException:
            if attempt == max_retries - 1:
                raise
            wait = min(2 ** attempt + random.uniform(0, 1), MAX_BACKOFF_SECONDS)
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
                    cover_url = None
                    isbn = None
                    heading = product.find("h3", class_="card__heading")
                    if heading:
                        link_tag = heading.find("a", class_="full-unstyled-link")
                        product_name = link_tag.get_text(strip=True) if link_tag else "No name found"
                        href = link_tag.get('href') if link_tag else None
                        if not href:
                            continue

                        link = "https://thebrokenbindingsub.com" + href

                        # Single request per product: the `.js` endpoint carries stock
                        # status, tags, cover and ISBN. Author lives only in the product
                        # HTML and is not used in notifications, so we skip that extra
                        # page fetch to halve request volume and avoid rate limiting.
                        try:
                            js_data = _get_with_retry(session, link + ".js").json()
                        except (requests.RequestException, ValueError) as e:
                            logger.error(f"Error fetching {link}.js: {e}; skipping product.")
                            continue

                        if "Private Sale" in shopify_js_tags(js_data):
                            logger.info(f"Skipping private sale product: {product_name}")
                            continue

                        in_stock, cover_url, isbn = item_media_from_shopify_js(js_data)
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
                        'in_stock': in_stock,
                        'cover_url': cover_url,
                        'isbn': isbn,
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
