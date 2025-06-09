
import json
import os

def add_to_guest_queue(guest):
    queue_path = "guest_queue.json"

    # Load queue
    if os.path.exists(queue_path):
        with open(queue_path, "r") as f:
            queue = json.load(f)
    else:
        queue = []

    # Avoid duplicates
    if not any(g['name'] == guest['name'] and g['email'] == guest['email'] for g in queue):
        queue.append(guest)

        with open(queue_path, "w") as f:
            json.dump(queue, f, indent=2)

        print(f"📥 Guest added to queue: {guest['name']}")
    else:
        print(f"⚠️ Guest already in queue: {guest['name']}")
