import json
import os
import logging
from supabase import create_client

logger = logging.getLogger()
logger.setLevel(logging.INFO)

supabase = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])

def handler(event, context):
    for record in event['Records']:
        message = json.loads(record['Sns']['Message'])
        event_type = message['eventType'].lower()

        if event_type not in ('click', 'open'):
            continue

        ses_message_id = message['mail']['messageId']
        event_timestamp = message['mail']['timestamp']

        log_row = supabase.table('email_log') \
            .select('id, user_id') \
            .eq('ses_message_id', ses_message_id) \
            .maybe_single() \
            .execute()

        email_log_id = log_row.data['id'] if log_row.data else None
        user_id = log_row.data['user_id'] if log_row.data else None

        if not log_row.data:
            logger.warning(f"No email_log row found for ses_message_id={ses_message_id}")

        url_clicked = None
        if event_type == 'click':
            url_clicked = message['click']['link']
        
        item_id = None
        if url_clicked:
            item = supabase.table('items_seen') \
                .select('id') \
                .eq('link', url_clicked) \
                .maybe_single() \
                .execute()

            if item.data:
                item_id = item.data['id']

        try:
            supabase.table('email_engagement_events').insert({
                'ses_message_id': ses_message_id,
                'email_log_id': email_log_id,
                'user_id': user_id,
                'event_type': event_type,
                'event_timestamp': event_timestamp,
                'url_clicked': url_clicked,
                'item_id': item_id
            }).execute()
        except Exception as e:
            logger.error(f"Failed to insert engagement event for {ses_message_id}: {e}")