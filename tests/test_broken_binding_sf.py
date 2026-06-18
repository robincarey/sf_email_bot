import unittest

from bs4 import BeautifulSoup

from scrapers.broken_binding_sf import (
    author_from_shopify_json,
    cover_and_isbn_from_shopify_json,
    extract_product_author,
)


class TestBrokenBindingAuthor(unittest.TestCase):

    def test_extract_product_author_from_page_markup(self):
        html = """
        <div class="productInfo">
          <p class="text productInfo__author">Ryan Rose</p>
          <h1>What We Eat; Books 1-2</h1>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        self.assertEqual(extract_product_author(soup), "Ryan Rose")

    def test_ignores_store_vendor_in_json(self):
        payload = {"product": {"vendor": "The Broken Binding Ltd."}}
        self.assertIsNone(author_from_shopify_json(payload))

    def test_accepts_non_store_vendor_in_json(self):
        payload = {"product": {"vendor": "Jane Author"}}
        self.assertEqual(author_from_shopify_json(payload), "Jane Author")

    def test_cover_and_isbn_from_shopify_json(self):
        payload = {
            "product": {
                "images": [{"src": "https://cdn.shopify.com/cover.jpg"}],
                "variants": [
                    {"barcode": ""},
                    {"barcode": "978-0-123456-78-9"},
                ],
            }
        }
        cover_url, isbn = cover_and_isbn_from_shopify_json(payload)
        self.assertEqual(cover_url, "https://cdn.shopify.com/cover.jpg")
        self.assertEqual(isbn, "9780123456789")

    def test_cover_and_isbn_from_body_html(self):
        payload = {
            "product": {
                "images": [],
                "variants": [{"barcode": ""}],
                "body_html": "<p>ISBN-13: 978-1-78108-970-1</p>",
            }
        }
        cover_url, isbn = cover_and_isbn_from_shopify_json(payload)
        self.assertIsNone(cover_url)
        self.assertEqual(isbn, "9781781089701")

    def test_cover_and_isbn_empty_when_missing(self):
        cover_url, isbn = cover_and_isbn_from_shopify_json({"product": {}})
        self.assertIsNone(cover_url)
        self.assertIsNone(isbn)


if __name__ == "__main__":
    unittest.main()
