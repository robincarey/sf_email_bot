import unittest
from unittest import mock

import requests
from bs4 import BeautifulSoup

import scrapers.broken_binding_sf as bb
from scrapers.broken_binding_sf import (
    author_from_shopify_json,
    cover_and_isbn_from_shopify_json,
    extract_product_author,
    item_media_from_shopify_js,
    shopify_js_tags,
    _get_with_retry,
)


class _FakeResponse:
    def __init__(self, status_code=200, headers=None):
        self.status_code = status_code
        self.headers = headers or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            err = requests.HTTPError(f"{self.status_code} error")
            err.response = self
            raise err


class _FakeSession:
    def __init__(self, responses):
        self._responses = list(responses)
        self.urls = []

    def get(self, url, timeout=None):
        self.urls.append(url)
        item = self._responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


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


class TestShopifyJs(unittest.TestCase):

    def test_item_media_in_stock_with_cover_and_isbn(self):
        data = {
            "available": True,
            "images": ["//cdn.shopify.com/files/cover.png?v=1"],
            "variants": [{"barcode": ""}, {"barcode": "978-1-78108-970-1"}],
        }
        in_stock, cover_url, isbn = item_media_from_shopify_js(data)
        self.assertTrue(in_stock)
        self.assertEqual(cover_url, "https://cdn.shopify.com/files/cover.png?v=1")
        self.assertEqual(isbn, "9781781089701")

    def test_item_media_falls_back_to_featured_image(self):
        data = {"available": False, "featured_image": "//cdn.shopify.com/f.jpg", "variants": []}
        in_stock, cover_url, isbn = item_media_from_shopify_js(data)
        self.assertFalse(in_stock)
        self.assertEqual(cover_url, "https://cdn.shopify.com/f.jpg")
        self.assertIsNone(isbn)

    def test_item_media_empty(self):
        in_stock, cover_url, isbn = item_media_from_shopify_js({})
        self.assertFalse(in_stock)
        self.assertIsNone(cover_url)
        self.assertIsNone(isbn)

    def test_tags_from_list(self):
        self.assertEqual(shopify_js_tags({"tags": ["Private Sale", "Fantasy"]}),
                         ["Private Sale", "Fantasy"])

    def test_tags_from_comma_string(self):
        self.assertEqual(shopify_js_tags({"tags": "Private Sale, Fantasy"}),
                         ["Private Sale", "Fantasy"])


class TestGetWithRetry(unittest.TestCase):

    def test_honors_retry_after_then_succeeds(self):
        ok = _FakeResponse(200)
        throttled = _FakeResponse(429, headers={"Retry-After": "7"})
        session = _FakeSession([throttled, ok])
        with mock.patch.object(bb.time, "sleep") as sleep:
            result = _get_with_retry(session, "https://x/p.js", max_retries=3)
        self.assertIs(result, ok)
        sleep.assert_called_once_with(7.0)

    def test_does_not_retry_404(self):
        session = _FakeSession([_FakeResponse(404)])
        with mock.patch.object(bb.time, "sleep"):
            with self.assertRaises(requests.HTTPError):
                _get_with_retry(session, "https://x/p.js", max_retries=3)
        self.assertEqual(len(session.urls), 1)

    def test_retry_after_capped_at_max_backoff(self):
        throttled = _FakeResponse(429, headers={"Retry-After": "999"})
        ok = _FakeResponse(200)
        session = _FakeSession([throttled, ok])
        with mock.patch.object(bb.time, "sleep") as sleep:
            _get_with_retry(session, "https://x/p.js", max_retries=3)
        sleep.assert_called_once_with(float(bb.MAX_BACKOFF_SECONDS))


if __name__ == "__main__":
    unittest.main()
