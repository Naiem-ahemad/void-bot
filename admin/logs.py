import os
import json
from datetime import datetime

LOGS_DIR = "data/chat_logs"

def get_latest_logs(limit=5):
    logs = []
    if not os.path.exists(LOGS_DIR):
        return ["❌ No logs found."]

    for user_id in os.listdir(LOGS_DIR):
        user_path = os.path.join(LOGS_DIR, user_id)
        if not os.path.isdir(user_path):
            continue

        for session_file in os.listdir(user_path):
            if session_file.endswith(".json"):
                file_path = os.path.join(user_path, session_file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    title = data.get("title", "No Title")
                    messages = data.get("messages", [])[-3:]  # Get last 3 messages
                    convo = f"👤 User ID: `{user_id}`\n📁 Chat: *{title}*\n"

                    for msg in messages:
                        role = "🧑 You" if msg["role"] == "user" else "🤖 Bot"
                        content = msg["content"]
                        convo += f"{role}: {content}\n"

                    logs.append(convo)
                except Exception as e:
                    logs.append(f"❌ Error reading log for {user_id}: {e}")

    return logs[-limit:]
