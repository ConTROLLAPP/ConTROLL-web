import json
import os
from datetime import datetime

SHARED_FILE = "shared_contributions.json"

def get_shared_notes(name):
    if not os.path.exists(SHARED_FILE):
        return []
    with open(SHARED_FILE, "r") as f:
        try:
            data = json.load(f)
            return data.get(name, [])
        except json.JSONDecodeError:
            return []

def add_guest_note(name, note):
    if not os.path.exists(SHARED_FILE):
        data = {}
    else:
        with open(SHARED_FILE, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {}

    data.setdefault(name, []).append(note)

    with open(SHARED_FILE, "w") as f:
        json.dump(data, f, indent=2)

def add_global_identity(identity_data):
    """Add verified identity to global contributions for alerting"""
    try:
        with open("shared_contributions.json", "r") as f:
            shared_data = json.load(f)
    except:
        shared_data = {"global_identities": []}

    if "global_identities" not in shared_data:
        shared_data["global_identities"] = []

    # Add timestamp
    from datetime import datetime
    identity_data["timestamp"] = datetime.now().isoformat()

    shared_data["global_identities"].append(identity_data)

    with open("shared_contributions.json", "w") as f:
        json.dump(shared_data, f, indent=2)

    print(f"🌐 Global identity logged: {identity_data.get('full_name')} (Risk: {identity_data.get('risk_score')})")

# DO NOT DELETE — Global Alert Lookup
def check_global_alert_db(name, email=None, phone=None):
    try:
        with open("shared_contributions.json", "r") as f:
            shared = json.load(f)
    except FileNotFoundError:
        return None

    for entry in shared.values():
        if (
            name.strip().lower() == entry.get("name", "").strip().lower()
            or (email and email.strip().lower() == entry.get("email", "").strip().lower())
            or (phone and phone.strip() == entry.get("phone", "").strip())
        ):
            return {
                "name": entry.get("name"),
                "risk_score": entry.get("risk_score", 0),
                "platforms": entry.get("matched_platforms", []),
            }
    return None

def check_global_alert(name, email=None, phone=None):
    """Check if guest is flagged in global ConTROLL network"""
    try:
        with open("shared_contributions.json", "r") as f:
            shared_data = json.load(f)

        global_identities = shared_data.get("global_identities", [])

        for identity in global_identities:
            # Check name match
            if name and identity.get('full_name'):
                if name.lower() in identity.get('full_name', '').lower():
                    return f"Name match: {identity.get('full_name')} - Risk: {identity.get('risk_score', 0)}"

            # Check email match
            if email and identity.get('email'):
                if email.lower() == identity.get('email', '').lower():
                    return f"Email match: {identity.get('email')} - Risk: {identity.get('risk_score', 0)}"

            # Check phone match
            if phone and identity.get('phone'):
                clean_phone = ''.join(filter(str.isdigit, phone))
                clean_identity_phone = ''.join(filter(str.isdigit, identity.get('phone', '')))
                if clean_phone and clean_identity_phone and clean_phone == clean_identity_phone:
                    return f"Phone match: {identity.get('phone')} - Risk: {identity.get('risk_score', 0)}"

        return None

    except Exception as e:
        print(f"Error checking global alerts: {e}")
        return None

def update_global_contributions(guest_data):
    """Update global contributions with enriched guest data"""
    try:
        # Load existing shared contributions
        try:
            with open("shared_contributions.json", "r") as f:
                shared_data = json.load(f)
        except FileNotFoundError:
            shared_data = {"global_identities": []}

        if "global_identities" not in shared_data:
            shared_data["global_identities"] = []

        # Clean phone for comparison
        guest_phone = guest_data.get("phone")
        guest_email = guest_data.get("email")
        guest_name = guest_data.get("name", "Unknown")

        # Check if this identity already exists
        existing_entry = None
        for i, identity in enumerate(shared_data["global_identities"]):
            # Match by phone or email
            if guest_phone and identity.get("phone"):
                clean_guest_phone = ''.join(filter(str.isdigit, guest_phone))
                clean_identity_phone = ''.join(filter(str.isdigit, identity.get("phone", "")))
                if clean_guest_phone == clean_identity_phone:
                    existing_entry = i
                    break
            
            if guest_email and identity.get("email"):
                if guest_email.lower() == identity.get("email", "").lower():
                    existing_entry = i
                    break

        # Prepare new/updated entry
        new_entry = {
            "alias": guest_data.get("alias", "Unknown"),
            "full_name": guest_name,
            "email": guest_email,
            "phone": guest_phone,
            "platform": guest_data.get("platform", "Unknown"),
            "risk_score": guest_data.get("risk", 0),
            "star_rating": guest_data.get("stars", 1),
            "stylometry": guest_data.get("stylometry", []),
            "critic_flag": guest_data.get("critic", False),
            "matched_platforms": guest_data.get("matched_platforms", []),
            "timestamp": datetime.now().isoformat()
        }

        if existing_entry is not None:
            # Update existing entry - merge data
            old_entry = shared_data["global_identities"][existing_entry]
            
            # Keep highest risk score
            new_entry["risk_score"] = max(old_entry.get("risk_score", 0), new_entry["risk_score"])
            
            # Keep lowest star rating
            new_entry["star_rating"] = min(old_entry.get("star_rating", 5), new_entry["star_rating"])
            
            # Merge stylometry flags
            old_stylometry = old_entry.get("stylometry", [])
            new_stylometry = new_entry.get("stylometry", [])
            merged_stylometry = list(set(old_stylometry + new_stylometry))
            new_entry["stylometry"] = merged_stylometry
            
            # Merge matched platforms
            old_platforms = old_entry.get("matched_platforms", [])
            new_platforms = new_entry.get("matched_platforms", [])
            merged_platforms = list(set(old_platforms + new_platforms))
            new_entry["matched_platforms"] = merged_platforms
            
            # Keep critic flag if either is true
            new_entry["critic_flag"] = old_entry.get("critic_flag", False) or new_entry["critic_flag"]
            
            # Update the entry
            shared_data["global_identities"][existing_entry] = new_entry
            print(f"🔄 Updated global identity: {guest_name} (Risk: {new_entry['risk_score']})")
        else:
            # Add new entry
            shared_data["global_identities"].append(new_entry)
            print(f"🌐 Added new global identity: {guest_name} (Risk: {new_entry['risk_score']})")

        # Save updated data
        with open("shared_contributions.json", "w") as f:
            json.dump(shared_data, f, indent=2)

        print(f"✅ Global contributions updated successfully")

    except Exception as e:
        print(f"⚠️ Error updating global contributions: {e}")
