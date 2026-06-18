import unittest
from unittest.mock import MagicMock, patch

from open_library import (
    extract_isbn_from_text,
    lookup_metadata,
    normalize_isbn,
    normalize_ol_work_key,
    ol_cover_url_by_isbn,
    ol_cover_url_by_olid,
)


class TestOpenLibrary(unittest.TestCase):

    def test_normalize_isbn(self):
        self.assertEqual(normalize_isbn("978-0-123456-78-9"), "9780123456789")
        self.assertIsNone(normalize_isbn("123"))

    def test_extract_isbn_from_text(self):
        self.assertEqual(
            extract_isbn_from_text("ISBN-13: 978-0-123456-78-9"),
            "9780123456789",
        )

    def test_ol_cover_urls(self):
        self.assertEqual(
            ol_cover_url_by_isbn("978-0-123456-78-9"),
            "https://covers.openlibrary.org/b/isbn/9780123456789-M.jpg",
        )
        self.assertEqual(
            ol_cover_url_by_olid("/works/OL123456W"),
            "https://covers.openlibrary.org/b/olid/OL123456W-M.jpg",
        )
        self.assertEqual(normalize_ol_work_key("OL123456W"), "OL123456W")

    @patch("open_library._search_docs")
    def test_lookup_metadata_by_work_key(self, search_docs):
        search_docs.return_value = [
            {
                "key": "/works/OL45804W",
                "title": "Dune",
                "isbn_13": ["9780441172719"],
            }
        ]
        session = MagicMock()
        meta = lookup_metadata(ol_work_key="OL45804W", session=session)
        self.assertIsNotNone(meta)
        assert meta is not None
        self.assertEqual(meta["isbn"], "9780441172719")
        self.assertEqual(
            meta["cover_url"],
            "https://covers.openlibrary.org/b/olid/OL45804W-M.jpg",
        )


if __name__ == "__main__":
    unittest.main()
