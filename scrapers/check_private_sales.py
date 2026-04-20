import logging
import random
import time

import requests
from bs4 import BeautifulSoup

from .broken_binding_sf import _get_with_retry

logger = logging.getLogger(__name__)


def find_private_sale_products():
    urls = [
        {"url": "https://thebrokenbindingsub.com/collections/to-the-stars", "store": "Broken Binding - To The Stars"},
        {"url": "https://thebrokenbindingsub.com/collections/the-infirmary", "store": "Broken Binding - The Infirmary"},
        {"url": "https://thebrokenbindingsub.com/collections/dragons-hoard", "store": "Broken Binding - Dragon's Hoard"},
        {"url": "https://thebrokenbindingsub.com/collections/the-graveyard", "store": "Broken Binding - The Graveyard"},
    ]

    report_rows = []

    with requests.Session() as session:
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Referer": "https://thebrokenbindingsub.com/",
        })

        try:
            _get_with_retry(session, "https://thebrokenbindingsub.com/")
            time.sleep(random.uniform(0.2, 0.5))
        except requests.RequestException:
            pass

        for entry in urls:
            base_url = entry["url"]
            store = entry["store"]
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
                    heading = product.find("h3", class_="card__heading")
                    if not heading:
                        continue

                    link_tag = heading.find("a", class_="full-unstyled-link")
                    if not link_tag:
                        continue

                    product_name = link_tag.get_text(strip=True) or "No name found"
                    href = link_tag.get("href")
                    if not href:
                        continue

                    link = "https://thebrokenbindingsub.com" + href

                    tags = []
                    is_private_sale = False
                    try:
                        json_response = _get_with_retry(session, link + ".json")
                        product_data = json_response.json()
                        raw_tags = product_data.get("product", {}).get("tags", "")
                        tags = [t.strip() for t in raw_tags.split(",") if t.strip()]
                        is_private_sale = "Private Sale" in tags
                    except requests.RequestException as e:
                        logger.warning(f"Could not fetch product JSON for {link}: {e}")
                    except ValueError as e:
                        logger.warning(f"Invalid JSON for {link}.json: {e}")

                    report_rows.append({
                        "store": store,
                        "name": product_name,
                        "url": link,
                        "tags": tags,
                        "private_sale": is_private_sale,
                    })

                    status = "SKIP (Private Sale)" if is_private_sale else "KEEP"
                    print(
                        f"[{status}] store={store} | name={product_name} | url={link} | tags={tags}"
                    )
                    time.sleep(random.uniform(0.2, 0.6))

                logger.info(f"Scanned {store} page {page}: {len(product_items)} products")
                page += 1

    private_rows = [r for r in report_rows if r["private_sale"]]
    print("\n=== Private Sale Summary ===")
    print(f"Total products scanned: {len(report_rows)}")
    print(f"Private Sale products: {len(private_rows)}")
    print(f"Non-Private products: {len(report_rows) - len(private_rows)}")

    if private_rows:
        print("\nProducts that would be skipped:")
        for row in private_rows:
            print(f"- {row['name']} | {row['store']} | {row['url']}")

    return report_rows


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    find_private_sale_products()
