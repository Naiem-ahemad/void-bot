import os
import json
from datetime import datetime

USERS_DIR = "data/users"

DEFAULT_SETTINGS = {
    "style": "friendly",
    "length": "medium",
    "language": "english"
}

DEFAULT_PROFILE = {
    "user_id": None,
    "name": "",
    "username": "",
    "joined_at": None,
    "message_count": 0,
    "role": "user",  # 👈 add this
    "settings": DEFAULT_SETTINGS.copy()
}

def ensure_user_profile(user):
    os.makedirs(USERS_DIR, exist_ok=True)
    user_file = os.path.join(USERS_DIR, f"{user.id}.json")

    DEFAULT_ROLE = "user"
    DEFAULT_SETTINGS = {
        "style": "friendly",
        "length": "medium",
        "language": "english"
    }

    if not os.path.exists(user_file):
        profile = {
            "user_id": user.id,
            "name": user.full_name,
            "username": user.username,
            "joined_at": datetime.now().isoformat(),
            "message_count": 1,
            "role": DEFAULT_ROLE,
            "settings": DEFAULT_SETTINGS.copy()
        }
    else:
        with open(user_file, "r", encoding="utf-8") as f:
            profile = json.load(f)

        profile["message_count"] += 1

        # Ensure 'settings' exists
        if "settings" not in profile:
            profile["settings"] = DEFAULT_SETTINGS.copy()
        else:
            for key, value in DEFAULT_SETTINGS.items():
                if key not in profile["settings"]:
                    profile["settings"][key] = value

        # Ensure 'role' exists
        if "role" not in profile:
            profile["role"] = DEFAULT_ROLE

    with open(user_file, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2)

def get_user_profile(user_id):
    user_file = os.path.join(USERS_DIR, f"{user_id}.json")
    if not os.path.exists(user_file):
        return None
    with open(user_file, "r", encoding="utf-8") as f:
        return json.load(f)

