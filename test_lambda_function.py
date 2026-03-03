import json
import unittest
from unittest.mock import patch, MagicMock

import lambda_function as lf


class TestParsePriceCents(unittest.TestCase):

    def test_dollar_price(self):
        self.assertEqual(lf.parse_price_cents("$10.99"), 1099)

    def test_pound_price(self):
        self.assertEqual(lf.parse_price_cents("£24.99"), 2499)

    def test_whole_dollar(self):
        self.assertEqual(lf.parse_price_cents("$10"), 1000)

    def test_no_symbol(self):
        self.assertEqual(lf.parse_price_cents("10.50"), 1050)

    def test_none_input(self):
        self.assertIsNone(lf.parse_price_cents(None))

    def test_empty_string(self):
        self.assertIsNone(lf.parse_price_cents(""))

    def test_no_digits(self):
        self.assertIsNone(lf.parse_price_cents("No price found"))


class TestGetRecipientsForRun(unittest.TestCase):

    @patch.object(lf, "get_supabase")
    def test_prod_mode_returns_id_and_email(self, mock_get_sb):
        lf.run_mode = "prod"
        mock_sb = MagicMock()
        mock_get_sb.return_value = mock_sb
        mock_resp = MagicMock()
        mock_resp.data = [
            {"id": "uid-1", "email": "a@test.com"},
            {"id": "uid-2", "email": "b@test.com"},
        ]
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_resp

        result = lf.get_recipients_for_run("test-run-id")
        self.assertEqual(result, [
            {"id": "uid-1", "email": "a@test.com"},
            {"id": "uid-2", "email": "b@test.com"},
        ])

    @patch.object(lf, "get_supabase")
    def test_dev_mode_looks_up_user_ids(self, mock_get_sb):
        lf.run_mode = "dev"
        mock_sb = MagicMock()
        mock_get_sb.return_value = mock_sb
        mock_resp = MagicMock()
        mock_resp.data = [{"id": "uid-dev", "email": "dev@test.com"}]
        mock_sb.table.return_value.select.return_value.in_.return_value.execute.return_value = mock_resp

        with patch.dict("os.environ", {"ADMIN_EMAILS": '["dev@test.com"]'}):
            result = lf.get_recipients_for_run("test-run-id")
        self.assertEqual(result, [{"id": "uid-dev", "email": "dev@test.com"}])

    @patch.object(lf, "get_supabase")
    def test_dev_mode_falls_back_to_none_id_on_db_error(self, mock_get_sb):
        lf.run_mode = "dev"
        mock_sb = MagicMock()
        mock_get_sb.return_value = mock_sb
        mock_sb.table.return_value.select.return_value.in_.return_value.execute.side_effect = Exception("db down")

        with patch.dict("os.environ", {"ADMIN_EMAILS": '["dev@test.com"]'}):
            result = lf.get_recipients_for_run("test-run-id")
        self.assertEqual(result, [{"id": None, "email": "dev@test.com"}])


class TestLoadSeenItems(unittest.TestCase):

    @patch.object(lf, "get_supabase")
    def test_success(self, mock_get_sb):
        mock_sb = MagicMock()
        mock_get_sb.return_value = mock_sb
        mock_resp = MagicMock()
        mock_resp.data = [
            {"name": "Book A", "price": "$10", "store": "UK", "link": "https://a", "in_stock": True},
        ]
        mock_sb.table.return_value.select.return_value.execute.return_value = mock_resp

        items = lf.load_seen_items("test-run-id")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["name"], "Book A")

    @patch.object(lf, "get_supabase")
    def test_error_returns_empty(self, mock_get_sb):
        mock_sb = MagicMock()
        mock_get_sb.return_value = mock_sb
        mock_sb.table.return_value.select.return_value.execute.side_effect = Exception("boom")
        items = lf.load_seen_items("test-run-id")
        self.assertEqual(items, [])


class TestCheckForUpdates(unittest.TestCase):

    def _patch_all(self):
        """Return a dict of active mocks for every external dependency."""
        patchers = {
            "get_recipients_for_run": patch.object(lf, "get_recipients_for_run"),
            "load_seen_items": patch.object(lf, "load_seen_items"),
            "broken_binding_checks": patch.object(lf, "broken_binding_checks"),
            "send_email": patch("lambda_function.send_email"),
            "save_seen_items": patch.object(lf, "save_seen_items"),
            "fetch_item_ids_by_link": patch.object(lf, "fetch_item_ids_by_link"),
            "insert_events": patch.object(lf, "insert_events"),
            "insert_email_log": patch.object(lf, "insert_email_log"),
            "insert_email_log_events": patch.object(lf, "insert_email_log_events"),
            "insert_run_log": patch.object(lf, "insert_run_log"),
            "update_run_log": patch.object(lf, "update_run_log"),
            "insert_daily_snapshots": patch.object(lf, "insert_daily_snapshots"),
        }
        mocks = {}
        for name, p in patchers.items():
            mocks[name] = p.start()
            self.addCleanup(p.stop)
        mocks["insert_events"].return_value = []
        mocks["insert_email_log"].return_value = []
        return mocks

    def _recip(self, email, uid=None):
        """Helper to build a recipient dict."""
        return {"id": uid or f"uid-{email.split('@')[0]}", "email": email}

    def test_new_item_sends_email_and_logs_events(self):
        m = self._patch_all()
        m["get_recipients_for_run"].return_value = [self._recip("a@test.com", "uid-a")]
        m["load_seen_items"].return_value = [
            {"name": "Old Book", "price": "$10", "store": "UK", "link": "https://old", "in_stock": True},
        ]
        m["broken_binding_checks"].return_value = [
            {"name": "Old Book", "price": "$10", "store": "UK", "link": "https://old", "in_stock": True},
            {"name": "New Book", "price": "$25", "store": "UK", "link": "https://new", "in_stock": True},
        ]
        m["fetch_item_ids_by_link"].return_value = {"https://old": 1, "https://new": 42}
        m["insert_events"].return_value = [{"id": 100, "item_id": 42, "event_type": "New Item"}]
        m["insert_email_log"].return_value = [{"id": 200, "user_id": "uid-a"}]

        lf.check_for_updates()

        m["save_seen_items"].assert_called_once()
        m["send_email"].assert_called_once()
        m["insert_events"].assert_called_once()
        m["insert_email_log"].assert_called_once()
        m["insert_email_log_events"].assert_called_once()

        event_rows = m["insert_events"].call_args[0][0]
        self.assertEqual(len(event_rows), 1)
        self.assertEqual(event_rows[0]["event_type"], "New Item")
        self.assertEqual(event_rows[0]["item_id"], 42)
        self.assertEqual(event_rows[0]["store"], "UK")
        self.assertTrue(event_rows[0]["in_stock"])

        sent_body = m["send_email"].call_args[0][1]
        self.assertIn("New Item", sent_body)

        log_rows = m["insert_email_log"].call_args[0][0]
        self.assertEqual(len(log_rows), 1)
        self.assertEqual(log_rows[0]["user_id"], "uid-a")
        self.assertTrue(log_rows[0]["success"])

        junction_rows = m["insert_email_log_events"].call_args[0][0]
        self.assertEqual(len(junction_rows), 1)
        self.assertEqual(junction_rows[0]["email_log_id"], 200)
        self.assertEqual(junction_rows[0]["event_id"], 100)

    def test_no_changes_sends_nothing(self):
        m = self._patch_all()
        m["get_recipients_for_run"].return_value = [self._recip("a@test.com")]
        items = [
            {"name": "Same Book", "price": "$10", "store": "UK", "link": "https://same", "in_stock": True},
        ]
        m["load_seen_items"].return_value = items
        m["broken_binding_checks"].return_value = items
        m["fetch_item_ids_by_link"].return_value = {"https://same": 1}

        lf.check_for_updates()

        m["send_email"].assert_not_called()
        m["save_seen_items"].assert_called_once()
        m["insert_daily_snapshots"].assert_called_once()

    def test_price_change_includes_store_and_in_stock(self):
        m = self._patch_all()
        m["get_recipients_for_run"].return_value = [self._recip("a@test.com")]
        m["load_seen_items"].return_value = [
            {"name": "Book A", "price": "$10", "store": "UK", "link": "https://a", "in_stock": True},
        ]
        m["broken_binding_checks"].return_value = [
            {"name": "Book A", "price": "$12", "store": "UK", "link": "https://a", "in_stock": True},
        ]
        m["fetch_item_ids_by_link"].return_value = {"https://a": 1}
        m["insert_events"].return_value = [{"id": 10, "item_id": 1, "event_type": "Price Change"}]
        m["insert_email_log"].return_value = [{"id": 50, "user_id": "uid-a"}]

        lf.check_for_updates()

        event_rows = m["insert_events"].call_args[0][0]
        self.assertEqual(event_rows[0]["event_type"], "Price Change")
        self.assertEqual(event_rows[0]["old_value"], "$10")
        self.assertEqual(event_rows[0]["new_value"], "$12")
        self.assertEqual(event_rows[0]["store"], "UK")
        self.assertTrue(event_rows[0]["in_stock"])

    def test_restock_event(self):
        m = self._patch_all()
        m["get_recipients_for_run"].return_value = [self._recip("a@test.com")]
        m["load_seen_items"].return_value = [
            {"name": "Book A", "price": "$10", "store": "UK", "link": "https://a", "in_stock": False},
        ]
        m["broken_binding_checks"].return_value = [
            {"name": "Book A", "price": "$10", "store": "UK", "link": "https://a", "in_stock": True},
        ]
        m["fetch_item_ids_by_link"].return_value = {"https://a": 1}
        m["insert_events"].return_value = [{"id": 10, "item_id": 1, "event_type": "Restocked"}]
        m["insert_email_log"].return_value = [{"id": 50, "user_id": "uid-a"}]

        lf.check_for_updates()

        event_rows = m["insert_events"].call_args[0][0]
        self.assertEqual(event_rows[0]["event_type"], "Restocked")
        self.assertTrue(event_rows[0]["in_stock"])

    def test_out_of_stock_does_not_email(self):
        m = self._patch_all()
        m["get_recipients_for_run"].return_value = [self._recip("a@test.com")]
        m["load_seen_items"].return_value = [
            {"name": "Book A", "price": "$10", "store": "UK", "link": "https://a", "in_stock": True},
        ]
        m["broken_binding_checks"].return_value = [
            {"name": "Book A", "price": "$10", "store": "UK", "link": "https://a", "in_stock": False},
        ]
        m["fetch_item_ids_by_link"].return_value = {"https://a": 1}
        m["insert_events"].return_value = [{"id": 10, "item_id": 1, "event_type": "Out of Stock"}]

        lf.check_for_updates()

        event_rows = m["insert_events"].call_args[0][0]
        self.assertEqual(event_rows[0]["event_type"], "Out of Stock")
        self.assertFalse(event_rows[0]["in_stock"])
        m["send_email"].assert_not_called()

    def test_empty_scraper_skips_all(self):
        m = self._patch_all()
        m["get_recipients_for_run"].return_value = [self._recip("a@test.com")]
        m["load_seen_items"].return_value = [
            {"name": "Book", "price": "$10", "store": "UK", "link": "https://x", "in_stock": True},
        ]
        m["broken_binding_checks"].return_value = []

        lf.check_for_updates()

        m["save_seen_items"].assert_not_called()
        m["send_email"].assert_not_called()
        m["insert_events"].assert_not_called()
        m["insert_email_log"].assert_not_called()
        m["insert_daily_snapshots"].assert_not_called()
        m["update_run_log"].assert_called_once()
        self.assertEqual(m["update_run_log"].call_args[1]["status"], "empty_scrape")

    def test_run_log_called_at_start_and_end(self):
        m = self._patch_all()
        m["get_recipients_for_run"].return_value = [self._recip("a@test.com", "uid-a")]
        m["load_seen_items"].return_value = []
        m["broken_binding_checks"].return_value = [
            {"name": "Book", "price": "$10", "store": "UK", "link": "https://x", "in_stock": True},
        ]
        m["fetch_item_ids_by_link"].return_value = {"https://x": 1}
        m["insert_events"].return_value = [{"id": 10, "item_id": 1, "event_type": "New Item"}]
        m["insert_email_log"].return_value = [{"id": 50, "user_id": "uid-a"}]

        lf.check_for_updates()

        m["insert_run_log"].assert_called_once()
        m["update_run_log"].assert_called_once()
        update_kwargs = m["update_run_log"].call_args[1]
        self.assertEqual(update_kwargs["items_scraped"], 1)
        self.assertEqual(update_kwargs["events_created"], 1)
        self.assertEqual(update_kwargs["emails_attempted"], 1)
        self.assertEqual(update_kwargs["emails_sent"], 1)
        self.assertEqual(update_kwargs["status"], "success")

    def test_daily_snapshots_called_with_all_items(self):
        m = self._patch_all()
        m["get_recipients_for_run"].return_value = [self._recip("a@test.com")]
        m["load_seen_items"].return_value = [
            {"name": "Old Book", "price": "$10", "store": "UK", "link": "https://old", "in_stock": True},
        ]
        m["broken_binding_checks"].return_value = [
            {"name": "Old Book", "price": "$10", "store": "UK", "link": "https://old", "in_stock": True},
            {"name": "New Book", "price": "$25", "store": "UK", "link": "https://new", "in_stock": True},
        ]
        m["fetch_item_ids_by_link"].return_value = {"https://old": 1, "https://new": 42}
        m["insert_events"].return_value = [{"id": 100, "item_id": 42, "event_type": "New Item"}]
        m["insert_email_log"].return_value = [{"id": 200, "user_id": "uid-a"}]

        lf.check_for_updates()

        m["insert_daily_snapshots"].assert_called_once()
        snapshot_items = m["insert_daily_snapshots"].call_args[0][0]
        snapshot_link_to_id = m["insert_daily_snapshots"].call_args[0][1]
        self.assertEqual(len(snapshot_items), 2)
        self.assertEqual(snapshot_link_to_id, {"https://old": 1, "https://new": 42})

    def test_typed_price_attached_before_upsert(self):
        m = self._patch_all()
        m["get_recipients_for_run"].return_value = []
        m["load_seen_items"].return_value = []
        m["broken_binding_checks"].return_value = [
            {"name": "Book", "price": "$10.99", "store": "UK", "link": "https://x", "in_stock": True},
        ]
        m["fetch_item_ids_by_link"].return_value = {}

        lf.check_for_updates()

        saved_items = m["save_seen_items"].call_args[0][0]
        self.assertEqual(saved_items[0]["typed_price_cents"], 1099)

    def test_email_failure_logged_with_error(self):
        m = self._patch_all()
        m["get_recipients_for_run"].return_value = [self._recip("a@test.com", "uid-a")]
        m["load_seen_items"].return_value = []
        m["broken_binding_checks"].return_value = [
            {"name": "Book", "price": "$10", "store": "UK", "link": "https://x", "in_stock": True},
        ]
        m["fetch_item_ids_by_link"].return_value = {"https://x": 1}
        m["insert_events"].return_value = [{"id": 10, "item_id": 1, "event_type": "New Item"}]
        m["insert_email_log"].return_value = [{"id": 50, "user_id": "uid-a"}]
        m["send_email"].side_effect = Exception("SMTP timeout")

        lf.check_for_updates()

        log_rows = m["insert_email_log"].call_args[0][0]
        self.assertEqual(len(log_rows), 1)
        self.assertFalse(log_rows[0]["success"])
        self.assertEqual(log_rows[0]["error_message"], "SMTP timeout")

        update_kwargs = m["update_run_log"].call_args[1]
        self.assertEqual(update_kwargs["emails_attempted"], 1)
        self.assertEqual(update_kwargs["emails_sent"], 0)

    def test_multiple_recipients_produce_multiple_log_rows(self):
        m = self._patch_all()
        m["get_recipients_for_run"].return_value = [
            self._recip("a@test.com", "uid-a"),
            self._recip("b@test.com", "uid-b"),
        ]
        m["load_seen_items"].return_value = []
        m["broken_binding_checks"].return_value = [
            {"name": "Book", "price": "$10", "store": "UK", "link": "https://x", "in_stock": True},
        ]
        m["fetch_item_ids_by_link"].return_value = {"https://x": 1}
        m["insert_events"].return_value = [{"id": 10, "item_id": 1, "event_type": "New Item"}]
        m["insert_email_log"].return_value = [
            {"id": 50, "user_id": "uid-a"},
            {"id": 51, "user_id": "uid-b"},
        ]

        lf.check_for_updates()

        self.assertEqual(m["send_email"].call_count, 2)

        log_rows = m["insert_email_log"].call_args[0][0]
        self.assertEqual(len(log_rows), 2)

        junction_rows = m["insert_email_log_events"].call_args[0][0]
        self.assertEqual(len(junction_rows), 2)
        self.assertEqual({r["email_log_id"] for r in junction_rows}, {50, 51})


if __name__ == "__main__":
    unittest.main()
