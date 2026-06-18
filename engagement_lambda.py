import json
import os
import logging
import re
from datetime import datetime, timezone

from supabase import create_client

logger = logging.getLogger()
logger.setLevel(logging.INFO)

supabase = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])

INVALID_ADDRESS_PATTERNS = [
    re.compile(r'invalid\s+domain', re.I),
    re.compile(r'user\s+unknown', re.I),
    re.compile(r'no\s+such\s+user', re.I),
    re.compile(r'550\s+5\.4\.4', re.I),
    re.compile(r'550\s+5\.1\.1', re.I),
]


def should_suppress_bounce(bounce_type, diagnostic_code=None, status=None):
    """Return (should_suppress, reason) for a bounce event."""
    if (bounce_type or '').lower() == 'permanent':
        return True, 'permanent_bounce'

    combined = f"{diagnostic_code or ''} {status or ''}"
    for pattern in INVALID_ADDRESS_PATTERNS:
        if pattern.search(combined):
            return True, 'invalid_address'
    return False, None


def lookup_email_log(ses_message_id):
    log_row = (
        supabase.table('email_log')
        .select('id, user_id')
        .eq('ses_message_id', ses_message_id)
        .maybe_single()
        .execute()
    )
    if log_row.data:
        return log_row.data['id'], log_row.data.get('user_id')
    return None, None


def lookup_user_by_email(email_address):
    if not email_address:
        return None
    profile = (
        supabase.table('profiles')
        .select('id')
        .ilike('email', email_address)
        .maybe_single()
        .execute()
    )
    return profile.data['id'] if profile.data else None


def resolve_user(ses_message_id, email_address):
    email_log_id, user_id = lookup_email_log(ses_message_id)
    if user_id:
        return email_log_id, user_id
    if email_address:
        user_id = lookup_user_by_email(email_address)
    return email_log_id, user_id


def log_delivery_event(
    ses_message_id, email_log_id, user_id, event_type, event_timestamp,
    delivery_metadata=None, url_clicked=None, item_id=None,
):
    row = {
        'ses_message_id': ses_message_id,
        'email_log_id': email_log_id,
        'user_id': user_id,
        'event_type': event_type,
        'event_timestamp': event_timestamp,
    }
    if delivery_metadata is not None:
        row['delivery_metadata'] = delivery_metadata
    if url_clicked is not None:
        row['url_clicked'] = url_clicked
    if item_id is not None:
        row['item_id'] = item_id
    supabase.table('email_engagement_events').insert(row).execute()


def mark_email_log_failed(ses_message_id, error_message):
    if not ses_message_id:
        return
    supabase.table('email_log').update({
        'success': False,
        'error_message': error_message,
    }).eq('ses_message_id', ses_message_id).execute()


def suppress_user(user_id, reason):
    if not user_id:
        return

    profile = (
        supabase.table('profiles')
        .select('id, pause_all_alerts')
        .eq('id', user_id)
        .maybe_single()
        .execute()
    )
    if not profile.data:
        logger.warning(f"No profile found for user_id={user_id}")
        return

    if profile.data.get('pause_all_alerts'):
        logger.info(f"User {user_id} already has pause_all_alerts=true; skipping suppression update")
        return

    now = datetime.now(timezone.utc).isoformat()
    supabase.table('profiles').update({
        'pause_all_alerts': True,
        'email_suppressed_at': now,
        'email_suppressed_reason': reason,
    }).eq('id', user_id).execute()
    logger.info(f"Suppressed alerts for user_id={user_id} reason={reason}")


def handle_click_open(message, event_type):
    ses_message_id = message['mail']['messageId']
    event_timestamp = message['mail']['timestamp']

    email_log_id, user_id = lookup_email_log(ses_message_id)
    if email_log_id is None:
        logger.warning(f"No email_log row found for ses_message_id={ses_message_id}")

    url_clicked = None
    if event_type == 'click':
        url_clicked = message['click']['link']

    item_id = None
    if url_clicked:
        item = (
            supabase.table('items_seen')
            .select('id')
            .eq('link', url_clicked)
            .maybe_single()
            .execute()
        )
        if item.data:
            item_id = item.data['id']

    log_delivery_event(
        ses_message_id, email_log_id, user_id, event_type, event_timestamp,
        url_clicked=url_clicked, item_id=item_id,
    )


def handle_bounce(message):
    bounce = message['bounce']
    ses_message_id = message['mail']['messageId']
    bounce_type = bounce.get('bounceType', '')
    bounce_subtype = bounce.get('bounceSubType', '')
    event_timestamp = bounce.get('timestamp') or message['mail']['timestamp']

    for recipient in bounce.get('bouncedRecipients', []):
        email_address = recipient.get('emailAddress')
        diagnostic_code = recipient.get('diagnosticCode', '')
        status = recipient.get('status', '')

        email_log_id, user_id = resolve_user(ses_message_id, email_address)
        if not user_id:
            logger.warning(
                f"No user resolved for bounce ses_message_id={ses_message_id} email={email_address}"
            )

        delivery_metadata = {
            'bounce_type': bounce_type,
            'bounce_subtype': bounce_subtype,
            'email_address': email_address,
            'diagnostic_code': diagnostic_code,
            'status': status,
            'feedback_id': bounce.get('feedbackId'),
        }

        try:
            log_delivery_event(
                ses_message_id, email_log_id, user_id, 'bounce', event_timestamp, delivery_metadata,
            )
        except Exception as e:
            logger.error(f"Failed to log bounce event for {ses_message_id}: {e}")
            continue

        error_summary = f"SES bounce ({bounce_type}/{bounce_subtype}): {diagnostic_code or status}"
        try:
            mark_email_log_failed(ses_message_id, error_summary)
        except Exception as e:
            logger.error(f"Failed to update email_log for bounce {ses_message_id}: {e}")

        should_suppress, reason = should_suppress_bounce(bounce_type, diagnostic_code, status)
        if should_suppress and user_id:
            try:
                suppress_user(user_id, reason)
            except Exception as e:
                logger.error(f"Failed to suppress user {user_id} after bounce: {e}")


def handle_complaint(message):
    complaint = message['complaint']
    ses_message_id = message['mail']['messageId']
    event_timestamp = complaint.get('timestamp') or message['mail']['timestamp']

    for recipient in complaint.get('complainedRecipients', []):
        email_address = recipient.get('emailAddress')
        email_log_id, user_id = resolve_user(ses_message_id, email_address)
        if not user_id:
            logger.warning(
                f"No user resolved for complaint ses_message_id={ses_message_id} email={email_address}"
            )

        delivery_metadata = {
            'email_address': email_address,
            'feedback_id': complaint.get('feedbackId'),
            'complaint_feedback_type': complaint.get('complaintFeedbackType'),
        }

        try:
            log_delivery_event(
                ses_message_id, email_log_id, user_id, 'complaint', event_timestamp, delivery_metadata,
            )
        except Exception as e:
            logger.error(f"Failed to log complaint event for {ses_message_id}: {e}")
            continue

        error_summary = "SES complaint: recipient marked message as spam"
        try:
            mark_email_log_failed(ses_message_id, error_summary)
        except Exception as e:
            logger.error(f"Failed to update email_log for complaint {ses_message_id}: {e}")

        if user_id:
            try:
                suppress_user(user_id, 'complaint')
            except Exception as e:
                logger.error(f"Failed to suppress user {user_id} after complaint: {e}")


def handler(event, context):
    for record in event['Records']:
        message = json.loads(record['Sns']['Message'])
        event_type = message['eventType'].lower()

        try:
            if event_type in ('click', 'open'):
                handle_click_open(message, event_type)
            elif event_type == 'bounce':
                handle_bounce(message)
            elif event_type == 'complaint':
                handle_complaint(message)
            else:
                logger.info(f"Ignoring unsupported SES event type: {event_type}")
        except Exception as e:
            logger.error(f"Failed to process SES {event_type} event: {e}")
