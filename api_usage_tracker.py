
import os
import json
from datetime import datetime

API_TRACK_FILE = "api_usage_log.json"
DAILY_LIMIT = 5000

def _load_log():
    if not os.path.exists(API_TRACK_FILE):
        return {}
    with open(API_TRACK_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def _save_log(log):
    with open(API_TRACK_FILE, "w") as f:
        json.dump(log, f, indent=4)

def check_api_quota():
    today = datetime.now().strftime("%Y-%m-%d")
    log = _load_log()
    if today not in log:
        log[today] = 0
    if log[today] >= DAILY_LIMIT:
        return False
    log[today] += 1
    _save_log(log)
    return True
