import json
import os

CLUE_QUEUE_FILE = "clue_queue.json"

def load_clue_queue():
    if not os.path.exists(CLUE_QUEUE_FILE):
        return []
    try:
        with open(CLUE_QUEUE_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def save_clue_queue(queue):
    with open(CLUE_QUEUE_FILE, "w") as f:
        json.dump(queue, f, indent=2)

def add_clue(clue):
    queue = load_clue_queue()
    if clue not in queue:
        queue.append(clue)
        save_clue_queue(queue)

def get_next_clue():
    queue = load_clue_queue()
    if queue:
        clue = queue.pop(0)
        save_clue_queue(queue)
        return clue
    return None

def peek_clues():
    return load_clue_queue()

def clear_clue_queue():
    save_clue_queue([])
