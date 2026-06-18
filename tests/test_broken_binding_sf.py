import unittest

from bs4 import BeautifulSoup

from scrapers.broken_binding_sf import (
    author_from_shopify_json,
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


if __name__ == "__main__":
    unittest.main()
