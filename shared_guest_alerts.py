
import json
import os
from datetime import datetime

SHARED_ALERTS_FILE = "shared_guest_alerts.json"

def add_shared_guest_profile(guest_id, name, email, phone, risk_score, platforms):
    """Add guest to shared alert system"""
    try:
        with open(SHARED_ALERTS_FILE, "r") as f:
            alerts_data = json.load(f)
    except FileNotFoundError:
        alerts_data = {"profiles": []}
    
    if "profiles" not in alerts_data:
        alerts_data["profiles"] = []
    
    profile = {
        "guest_id": guest_id,
        "name": name,
        "email": email,
        "phone": phone,
        "risk_score": risk_score,
        "platforms": platforms,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    alerts_data["profiles"].append(profile)
    
    with open(SHARED_ALERTS_FILE, "w") as f:
        json.dump(alerts_data, f, indent=2)

def check_shared_guest_alert(email, phone):
    """Check if guest is in shared alert system"""
    try:
        with open(SHARED_ALERTS_FILE, "r") as f:
            alerts_data = json.load(f)
        
        for profile in alerts_data.get("profiles", []):
            if (email and profile.get("email") == email) or \
               (phone and profile.get("phone") == phone):
                return profile
        
        return None
    except FileNotFoundError:
        return None

def get_shared_guest_count():
    """Get count of shared guest alerts"""
    try:
        with open(SHARED_ALERTS_FILE, "r") as f:
            alerts_data = json.load(f)
        return len(alerts_data.get("profiles", []))
    except FileNotFoundError:
        return 0
