import json
import os
from broken_binding_sf import broken_binding_sf
from email_notifier import send_email
import schedule
import time
from tabulate import tabulate

RECIPIENT_EMAIL = "robin.carey@gmail.com"
DATA_FILE = "items_seen.json"


def load_seen_items():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as file:
            try:
                return {tuple(item) for item in json.load(file)}  # Ensure tuples are returned
            except json.JSONDecodeError:
                return set()  # Handle potential JSON corruption
    return set()


def save_seen_items(items):
    with open(DATA_FILE, 'w') as file:
        json.dump(list(items), file)


def check_for_updates():
    seen_items = load_seen_items()
    new_items = broken_binding_sf()
    current_item_names = {(item['name'], item['price']) for item in new_items}

    # Find new unseen items
    unseen_items = current_item_names - seen_items

    if unseen_items:
        headers = ["Item Name", "Price"]
        table = tabulate(unseen_items, headers=headers, tablefmt="grid")
        message = f"New items available:\n{table}"
        send_email("New Store Items Available!", message, RECIPIENT_EMAIL)
        print("New items found and email sent!")
        save_seen_items(current_item_names)
    else:
        print("No new items found.")


# Schedule the bot to run every hour
schedule.every(1).hour.do(check_for_updates)

if __name__ == "__main__":
    print("Starting bot...")
    check_for_updates()  # Run immediately once
    while True:
        schedule.run_pending()
        time.sleep(1)
