# test_engagement.py
from engagement_lambda import handler
from supabase import create_client
import os, json
from dotenv import load_dotenv
load_dotenv()

supabase = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])

# Insert a fake email_log row to test the join
supabase.table('email_log').insert({
    'ses_message_id': 'test-message-id-123',
    'subject': 'Test',
    'success': True
}).execute()

mock_event = {
    "Records": [{
        "Sns": {
            "Message": json.dumps({
                "eventType": "click",
                "mail": {
                    "messageId": "test-message-id-123",
                    "timestamp": "2026-04-20T10:00:00.000Z"
                },
                "click": {
                    "link": "https://thebrokenbindingsub.com/products/test",
                    "timestamp": "2026-04-20T10:01:00.000Z"
                }
            })
        }
    }]
}

handler(mock_event, {})
print("Done — check email_engagement_events in Supabase")

# Cleanup reminder:
# Delete from email_engagement_events where ses_message_id = 'test-message-id-123'
# Delete from email_log where ses_message_id = 'test-message-id-123'