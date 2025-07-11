import os , json

USERS_DB = "data/users.json"
os.makedirs("data", exist_ok=True)
CHAT_LOGS_DIR = "data/chat_logs"

def get_total_users():
    if not os.path.exists(CHAT_LOGS_DIR):
        return 0
    user_dirs = [d for d in os.listdir(CHAT_LOGS_DIR) if os.path.isdir(os.path.join(CHAT_LOGS_DIR, d))]
    return len(user_dirs)

def get_all_user_ids():
    if not os.path.exists(CHAT_LOGS_DIR):
        return []
    return [d for d in os.listdir(CHAT_LOGS_DIR) if os.path.isdir(os.path.join(CHAT_LOGS_DIR, d))]

def load_users():
    if not os.path.exists(USERS_DB):
        return []
    with open(USERS_DB, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_DB, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)

def is_registered_user(user_id: int) -> bool:
    users = load_users()
    return user_id in users

def register_user(user) -> None:
    users = load_users()
    if user.id not in users:
        users.append(user.id)
        save_users(users)