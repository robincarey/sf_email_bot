import json
import unittest
from unittest.mock import MagicMock, patch

import engagement_lambda as el


def _sns_event(message):
    return {"Records": [{"Sns": {"Message": json.dumps(message)}}]}


def _bounce_message(
    bounce_type="Permanent",
    bounce_subtype="General",
    email="bad@example.com",
    diagnostic_code="smtp; 550 5.1.1 User unknown",
    status="5.1.1",
    ses_message_id="msg-bounce-1",
):
    return {
        "eventType": "Bounce",
        "bounce": {
            "feedbackId": "fb-1",
            "bounceType": bounce_type,
            "bounceSubType": bounce_subtype,
            "bouncedRecipients": [{
                "emailAddress": email,
                "action": "failed",
                "status": status,
                "diagnosticCode": diagnostic_code,
            }],
            "timestamp": "2026-06-18T14:36:50.634Z",
        },
        "mail": {
            "messageId": ses_message_id,
            "timestamp": "2026-06-18T14:36:50.394Z",
        },
    }


def _complaint_message(email="spam@example.com", ses_message_id="msg-complaint-1"):
    return {
        "eventType": "Complaint",
        "complaint": {
            "feedbackId": "fb-2",
            "complaintFeedbackType": "abuse",
            "complainedRecipients": [{"emailAddress": email}],
            "timestamp": "2026-06-18T15:00:00.000Z",
        },
        "mail": {
            "messageId": ses_message_id,
            "timestamp": "2026-06-18T14:59:00.000Z",
        },
    }


class TestShouldSuppressBounce(unittest.TestCase):
    def test_permanent_bounce(self):
        suppress, reason = el.should_suppress_bounce("Permanent")
        self.assertTrue(suppress)
        self.assertEqual(reason, "permanent_bounce")

    def test_transient_invalid_domain(self):
        suppress, reason = el.should_suppress_bounce(
            "Transient",
            diagnostic_code="smtp; 550 5.4.4 Invalid domain",
            status="5.4.4",
        )
        self.assertTrue(suppress)
        self.assertEqual(reason, "invalid_address")

    def test_transient_mailbox_full(self):
        suppress, reason = el.should_suppress_bounce(
            "Transient",
            diagnostic_code="smtp; 452 4.2.2 Mailbox full",
            status="4.2.2",
        )
        self.assertFalse(suppress)
        self.assertIsNone(reason)


class TestBounceHandler(unittest.TestCase):
    def setUp(self):
        self.insert_mock = MagicMock()
        self.update_mock = MagicMock()
        table_mock = MagicMock()
        table_mock.insert.return_value = table_mock
        table_mock.update.return_value = table_mock
        table_mock.select.return_value = table_mock
        table_mock.eq.return_value = table_mock
        table_mock.ilike.return_value = table_mock
        table_mock.maybe_single.return_value = table_mock
        table_mock.execute.return_value = MagicMock(data=None)
        self.table_mock = table_mock
        el.supabase = MagicMock()
        el.supabase.table.return_value = table_mock

    def _email_log_lookup(self, user_id="uid-1", email_log_id=10):
        result = MagicMock()
        result.data = {"id": email_log_id, "user_id": user_id}
        return result

    def _profile_lookup(self, pause_all_alerts=False):
        result = MagicMock()
        result.data = {"id": "uid-1", "pause_all_alerts": pause_all_alerts}
        return result

    def test_permanent_bounce_suppresses_user(self):
        self.table_mock.execute.side_effect = [
            self._email_log_lookup(),
            MagicMock(data=None),  # insert
            MagicMock(data=None),  # email_log update
            self._profile_lookup(pause_all_alerts=False),
            MagicMock(data=None),  # profile update
        ]
        el.handler(_sns_event(_bounce_message()), None)
        update_calls = [c[0][0] for c in self.table_mock.update.call_args_list]
        self.assertTrue(any(
            u.get("pause_all_alerts") is True and u.get("email_suppressed_reason") == "permanent_bounce"
            for u in update_calls
        ))
        insert_call = self.table_mock.insert.call_args_list[0][0][0]
        self.assertEqual(insert_call["event_type"], "bounce")

    def test_complaint_suppresses_user(self):
        self.table_mock.execute.side_effect = [
            self._email_log_lookup(),
            MagicMock(data=None),
            MagicMock(data=None),
            self._profile_lookup(pause_all_alerts=False),
            MagicMock(data=None),
        ]
        el.handler(_sns_event(_complaint_message()), None)
        update_calls = [c[0][0] for c in self.table_mock.update.call_args_list]
        self.assertTrue(any(u.get("email_suppressed_reason") == "complaint" for u in update_calls))

    def test_transient_invalid_domain_suppresses(self):
        self.table_mock.execute.side_effect = [
            self._email_log_lookup(),
            MagicMock(data=None),
            MagicMock(data=None),
            self._profile_lookup(pause_all_alerts=False),
            MagicMock(data=None),
        ]
        msg = _bounce_message(
            bounce_type="Transient",
            diagnostic_code="smtp; 550 5.4.4 Invalid domain",
            status="5.4.4",
            email="typo@gmail.coms",
        )
        el.handler(_sns_event(msg), None)
        update_calls = [c[0][0] for c in self.table_mock.update.call_args_list]
        self.assertTrue(any(u.get("email_suppressed_reason") == "invalid_address" for u in update_calls))

    def test_transient_mailbox_full_does_not_suppress(self):
        self.table_mock.execute.side_effect = [
            self._email_log_lookup(),
            MagicMock(data=None),
            MagicMock(data=None),
        ]
        msg = _bounce_message(
            bounce_type="Transient",
            diagnostic_code="smtp; 452 4.2.2 Mailbox full",
            status="4.2.2",
        )
        el.handler(_sns_event(msg), None)
        profile_updates = [
            c[0][0] for c in self.table_mock.update.call_args_list
            if c[0][0].get("pause_all_alerts") is True
        ]
        self.assertEqual(profile_updates, [])

    def test_fallback_lookup_by_email(self):
        profile_result = MagicMock()
        profile_result.data = {"id": "uid-fallback"}

        self.table_mock.execute.side_effect = [
            MagicMock(data=None),
            profile_result,
            MagicMock(data=None),
            MagicMock(data=None),
            MagicMock(data={"id": "uid-fallback", "pause_all_alerts": False}),
            MagicMock(data=None),
        ]
        msg = _bounce_message(email="orphan@example.com", ses_message_id="msg-no-log")
        el.handler(_sns_event(msg), None)
        self.table_mock.ilike.assert_called_with("email", "orphan@example.com")

    def test_already_suppressed_skips_profile_update(self):
        self.table_mock.execute.side_effect = [
            self._email_log_lookup(),
            MagicMock(data=None),
            MagicMock(data=None),
            self._profile_lookup(pause_all_alerts=True),
        ]
        el.handler(_sns_event(_bounce_message()), None)
        profile_updates = [
            c[0][0] for c in self.table_mock.update.call_args_list
            if c[0][0].get("pause_all_alerts") is True
        ]
        self.assertEqual(profile_updates, [])


if __name__ == "__main__":
    unittest.main()
