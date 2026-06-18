import unittest

from silver_catalog import _normalize_isbn, clean_title, normalize_title, normalize_url


class TestSilverCatalog(unittest.TestCase):

    def test_normalize_title(self):
        self.assertEqual(normalize_title("Dune"), "dune")
        self.assertEqual(
            normalize_title("The Bone Season; Books 1-5"),
            "the bone season books 1 5",
        )

    def test_clean_title_strips_edition_suffix(self):
        self.assertEqual(
            clean_title("Hyperion Cantos; Books 1-4 - 2nd Printing"),
            "Hyperion Cantos",
        )
        self.assertEqual(
            clean_title("Sistah Samurai - TBB Press Edition with Slipcase"),
            "Sistah Samurai",
        )

    def test_normalize_url(self):
        self.assertEqual(
            normalize_url("https://example.com/foo/?x=1"),
            "https://example.com/foo",
        )

    def test_normalize_isbn(self):
        self.assertEqual(_normalize_isbn("978-0-123456-78-9"), "9780123456789")
        self.assertIsNone(_normalize_isbn(""))


if __name__ == "__main__":
    unittest.main()
