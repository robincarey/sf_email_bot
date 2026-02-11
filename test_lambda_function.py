import json
import unittest
from unittest.mock import patch, call

import lambda_function as lf


class TestS3ConfigLoading(unittest.TestCase):
    def setUp(self):
        # Ensure module globals are set for tests
        lf.bucket = "test-bucket"
        lf.file_key = "sfbot/stock_files/items_seen.json"

    # --- Recipients: loads flat list JSON from S3 and removes duplicates ---
    @patch("lambda_function.read_file_from_s3")
    def test_load_recipients_from_s3_list(self, mock_read):
        mock_read.return_value = json.dumps([
            "a@example.com",
            "b@example.com",
            "a@example.com"
        ])

        with patch.dict(
            "os.environ",
            {
                "RECIPIENT_EMAILS": "[]",
                "RECIPIENTS_KEY": "config/recipients.json"
            }
        ):
            recipients = lf.load_recipients()

        self.assertEqual(recipients, ["a@example.com", "b@example.com"])

    # --- Recipients: loads dict JSON from S3 using "recipients" key ---
    @patch("lambda_function.read_file_from_s3")
    def test_load_recipients_from_s3_dict(self, mock_read):
        mock_read.return_value = json.dumps({
            "recipients": ["b@example.com", "a@example.com", "a@example.com"]
        })

        with patch.dict(
            "os.environ",
            {
                "RECIPIENT_EMAILS": "[]",
                "RECIPIENTS_KEY": "config/recipients.json"
            }
        ):
            recipients = lf.load_recipients()

        self.assertEqual(recipients, ["a@example.com", "b@example.com"])

    # --- Recipients: falls back to env var when S3 read fails ---
    @patch("lambda_function.read_file_from_s3")
    def test_load_recipients_fallback_to_env_on_s3_error(self, mock_read):
        mock_read.side_effect = Exception("S3 down")

        lf.run_mode = "dev"  # force dev behavior for this test

        with patch.dict(
            "os.environ",
            {
                "RECIPIENT_EMAILS": '["env1@example.com","env2@example.com"]',
                "RECIPIENTS_KEY": "config/recipients.json",
            }
        ):
            recipients = lf.load_recipients()

        self.assertEqual(recipients, ["env1@example.com", "env2@example.com"])

    # --- Seen Items: successfully parses valid JSON list from S3 ---
    @patch("lambda_function.read_file_from_s3")
    def test_load_seen_items_success(self, mock_read):
        mock_read.return_value = json.dumps([
            {"name": "Book A", "price": "$10", "store": "UK", "link": "https://x"},
        ])

        items = lf.load_seen_items()
        self.assertIsInstance(items, list)
        self.assertEqual(items[0]["name"], "Book A")

    # --- Seen Items: returns empty list when JSON is invalid ---
    @patch("lambda_function.read_file_from_s3")
    def test_load_seen_items_bad_json_returns_empty_list(self, mock_read):
        mock_read.return_value = "not json"

        items = lf.load_seen_items()
        self.assertEqual(items, [])

    # --- Seen Items: returns empty list when S3 read throws exception ---
    @patch("lambda_function.read_file_from_s3")
    def test_load_seen_items_exception_returns_empty_list(self, mock_read):
        mock_read.side_effect = Exception("boom")

        items = lf.load_seen_items()
        self.assertEqual(items, [])

    # --- Updates: sends email to all recipients and saves new items when unseen exist ---
    @patch("lambda_function.save_seen_items")
    @patch("lambda_function.send_email")
    @patch("lambda_function.broken_binding_checks")
    @patch("lambda_function.load_seen_items")
    @patch("lambda_function.load_recipients")
    def test_check_for_updates_sends_email_and_saves(
        self,
        mock_load_recipients,
        mock_load_seen_items,
        mock_broken_binding_checks,
        mock_send_email,
        mock_save_seen_items,
    ):
        # Arrange
        mock_load_recipients.return_value = ["a@example.com", "b@example.com"]

        seen_items = [
            {"name": "Old Book", "price": "$10", "store": "UK", "link": "https://old"},
        ]
        new_items = [
            {"name": "Old Book", "price": "$10", "store": "UK", "link": "https://old"},
            {"name": "New Book", "price": "$25", "store": "UK", "link": "https://new"},
        ]

        mock_load_seen_items.return_value = seen_items
        mock_broken_binding_checks.return_value = new_items

        # Act
        lf.check_for_updates()

        # Assert: email sent once per recipient
        self.assertEqual(mock_send_email.call_count, 2)

        calls = mock_send_email.call_args_list
        self.assertEqual(calls[0].args[0], "New Broken Binding Books Available!")
        self.assertIsInstance(calls[0].args[1], str)
        self.assertEqual(calls[0].args[2], "a@example.com")

        self.assertEqual(calls[1].args[0], "New Broken Binding Books Available!")
        self.assertIsInstance(calls[1].args[1], str)
        self.assertEqual(calls[1].args[2], "b@example.com")

        mock_save_seen_items.assert_called_once_with(new_items)

    # --- Updates: sends nothing and does not save when no changes detected ---
    @patch("lambda_function.save_seen_items")
    @patch("lambda_function.send_email")
    @patch("lambda_function.broken_binding_checks")
    @patch("lambda_function.load_seen_items")
    @patch("lambda_function.load_recipients")
    def test_check_for_updates_no_changes_sends_nothing(
        self,
        mock_load_recipients,
        mock_load_seen_items,
        mock_broken_binding_checks,
        mock_send_email,
        mock_save_seen_items,
    ):
        mock_load_recipients.return_value = ["a@example.com", "b@example.com"]

        items = [
            {"name": "Same Book", "price": "$10", "store": "UK", "link": "https://same"},
        ]

        mock_load_seen_items.return_value = items
        mock_broken_binding_checks.return_value = items

        lf.check_for_updates()

        mock_send_email.assert_not_called()
        mock_save_seen_items.assert_not_called()

    # --- Updates: triggers email when price changes for existing item ---
    @patch("lambda_function.save_seen_items")
    @patch("lambda_function.send_email")
    @patch("lambda_function.broken_binding_checks")
    @patch("lambda_function.load_seen_items")
    @patch("lambda_function.load_recipients")
    def test_check_for_updates_sends_on_price_change(
        self,
        mock_load_recipients,
        mock_load_seen_items,
        mock_broken_binding_checks,
        mock_send_email,
        mock_save_seen_items,
    ):
        mock_load_recipients.return_value = ["a@example.com"]

        seen_items = [
            {"name": "Book A", "price": "$10", "store": "UK", "link": "https://a"},
        ]
        new_items = [
            {"name": "Book A", "price": "$12", "store": "UK", "link": "https://a"},
        ]

        mock_load_seen_items.return_value = seen_items
        mock_broken_binding_checks.return_value = new_items

        lf.check_for_updates()

        mock_send_email.assert_called_once()
        mock_save_seen_items.assert_called_once_with(new_items)

        sent_body = mock_send_email.call_args.args[1]
        self.assertIn("Price Change - Previously", sent_body)


if __name__ == "__main__":
    unittest.main()
