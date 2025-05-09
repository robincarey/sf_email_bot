import requests
from bs4 import BeautifulSoup


def broken_binding_checks():
    # Checking Broken Binding product pages
    urls = [
        {"url": "https://thebrokenbindingsub.com/collections/to-the-stars", "store": "To The Stars"},
        {"url": "https://thebrokenbindingsub.com/collections/the-infirmary", "store": "The Infirmary"},
        {"url": "https://thebrokenbindingsub.com/collections/dragons-hoard", "store": "Dragon's Hoard"}
    ]
    product_array = []

    # Define headers to mimic a real browser request (helps avoid being blocked)
    headers = {"User-Agent": "Mozilla/5.0"}

    for entry in urls:
        url = entry['url']
        store = entry['store']

        # Make the HTTP request with headers
        response = requests.get(url, headers=headers)
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
            else:
                product_name = "No name found"

            # Extract the product price: prefer sale price, fall back to regular
            price_span = (
                product.find("span", class_="price-item--sale") or 
                product.find("span", class_="price-item--regular")
            )
            product_price = price_span.get_text(strip=True) if price_span else "No price found"

            # Append extracted info to product_array
            product_array.append({
                'name': product_name,
                'price': product_price,
                'store': store,
                'link': link
            })

    return product_array

if __name__ == "__main__":
    test_array = broken_binding_checks()
    for entry in test_array:
        for key, value in entry.items():
            print(f"{key}: {value}", end=" | ")
        print()
    