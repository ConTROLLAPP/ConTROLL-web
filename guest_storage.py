
import json
import os
from shared_guest_alerts import check_shared_guest_alert

def save_guest_from_review(handle, result):
    guest_db_path = "guest_db.json"

    try:
        # Use handle if provided, fallback to result handle or Unknown Guest
        name = handle or result.get("handle", "Unknown Guest")
        
        guest_entry = {
            "full_name": name,
            "risk_score": int(result.get('risk_score', 0)),
            "star_rating": int(result.get('star_rating', 1)),
            "matched_platforms": list(result.get('matched_platforms', [])),
            "review_text": str(result.get('original_text', '')),
            "known_aliases": [str(x) for x in result.get('identity_matches', [])] if result.get('identity_matches') else [],
            "last_updated": "2024-01-20"
        }

        # Load existing guest DB
        guest_db = {}
        if os.path.exists(guest_db_path):
            with open(guest_db_path, "r") as f:
                try:
                    guest_db = json.load(f)
                except json.JSONDecodeError:
                    guest_db = {}

        # Check for global network alerts before saving
        email = result.get('email')
        phone = result.get('phone')
        if email or phone:
            shared_alert = check_shared_guest_alert(email, phone)
            if shared_alert:
                print(f"🚨 GLOBAL ALERT: Guest {name} is flagged in ConTROLL network!")
                guest_entry['global_alert'] = True
                guest_entry['shared_details'] = shared_alert

        # Use name as key
        guest_id = name.replace(" ", "_").lower()
        guest_db[guest_id] = guest_entry

        # Save updated DB
        with open(guest_db_path, "w") as f:
            json.dump(guest_db, f, indent=2)

        print(f"✅ Guest auto-saved: {name}")

    except Exception as e:
        print(f"Error saving guest data: {str(e)}")
