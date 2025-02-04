import requests
from bs4 import BeautifulSoup


def broken_binding_sf():
    # Checking Broken Binding SF product page
    url = "https://thebrokenbindingsub.com/collections/to-the-stars"

    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    # Find all list items with the grid item class
    product_items = soup.find_all("li", class_="grid__item")
    product_array = []

    for item in product_items:
        # Extract the product name inside an <h3> with a nested <a>
        heading = item.find("h3", class_="card__heading")
        if heading:
            link = heading.find("a", class_="full-unstyled-link")
            product_name = link.get_text(strip=True) if link else "No name found"
        else:
            product_name = "No name found"

        # Extract the product price.
        price_span = item.find("span", class_="price-item--sale")
        product_price = price_span.get_text(strip=True) if price_span else "No price found"
        product_array.append({'name': product_name, 'price': product_price})

    return product_array
