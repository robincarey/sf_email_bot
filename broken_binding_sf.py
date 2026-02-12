import requests
import time
import random
from bs4 import BeautifulSoup


def broken_binding_checks():
    # Checking Broken Binding product pages
    urls = [
        {"url": "https://thebrokenbindingsub.com/collections/to-the-stars", "store": "To The Stars"},
        {"url": "https://thebrokenbindingsub.com/collections/the-infirmary", "store": "The Infirmary"},
        {"url": "https://thebrokenbindingsub.com/collections/dragons-hoard", "store": "Dragon's Hoard"}
    ]
    product_list = []

    # Fire up a session with appropriate headers
    with requests.Session() as session:
        session.headers.update({"User-Agent": "Mozilla/5.0"})

        for entry in urls:
            url = entry['url']
            store = entry['store']

            # Make the HTTP request with headers
            try:
                response = session.get(url, timeout=10)
                response.raise_for_status()  # catches 4xx/5xx
            except requests.exceptions.RequestException as e:
                print(f"Error fetching collection {url}: {e}")
                continue
            soup = BeautifulSoup(response.content, "html.parser")

            # Find all list items with the grid product class
            product_items = soup.find_all("li", class_="grid__item")

            for product in product_items:
                # Extract the product name inside an <h3> with a nested <a>
                heading = product.find("h3", class_="card__heading")
                if heading:
                    link = heading.find("a", class_="full-unstyled-link")
                    product_name = link.get_text(strip=True) if link else "No name found"
                    link = "https://thebrokenbindingsub.com" + link['href']
                    # Check whether product is in stock
                    try:
                        product_response = session.get(link, timeout=10)
                        product_response.raise_for_status() # catches 4xx/5xx
                    except requests.exceptions.RequestException as e:
                        print(f"Error fetching product {link}: {e}")
                        continue
                    product_soup = BeautifulSoup(product_response.content, "html.parser")
                    cart_button = product_soup.find("button", class_="product-form__submit")
                    if not cart_button or "Sold out" in cart_button.get_text(strip=True):
                        in_stock = False
                    else:
                        in_stock = True
                else:
                    product_name = "No name found"

                # Extract the product price: prefer sale price, fall back to regular
                price_span = (
                    product.find("span", class_="price-item--sale") or 
                    product.find("span", class_="price-item--regular")
                )
                product_price = price_span.get_text(strip=True) if price_span else "No price found"

                # Add extracted info to product_list
                product_list.append({
                    'name': product_name,
                    'price': product_price,
                    'store': store,
                    'link': link,
                    'in_stock': in_stock
                })
                
                # Small delay between scraping products to limit hit to server
                time.sleep(random.uniform(0.2, 0.6))

    return product_list

if __name__ == "__main__":
    test_array = broken_binding_checks()
    for entry in test_array:
        for key, value in entry.items():
            print(f"{key}: {value}", end=" | ")
        print()
    