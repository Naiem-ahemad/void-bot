import os, json, uuid
import tiktoken
from config import GEMINI_API_KEY
import google.generativeai as genai
from datetime import datetime
from config import CHAT_LOG_FOLDER
from chat.summarizer import summarize_title  # You write this using Gemini

def get_user_folder(user_id):
    folder = os.path.join(CHAT_LOG_FOLDER, str(user_id))
    os.makedirs(folder, exist_ok=True)
    return folder
# chat/chat_sessions.py

def rename_chat_title(user_id, session_id, new_title):
    path = os.path.join(get_user_folder(user_id), session_id)
    if not os.path.exists(path):
        return False

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    data["title"] = new_title

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return True

def list_chats(user_id):
    folder = get_user_folder(user_id)
    sessions = []
    for file in os.listdir(folder):
        if file.endswith(".json"):
            with open(os.path.join(folder, file), "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    sessions.append({"id": file, "title": data.get("title", "Unnamed Chat")})
                except: pass
    return sessions

def start_new_chat(user_id):
    folder = get_user_folder(user_id)
    session_id = f"{uuid.uuid4().hex[:8]}.json"
    path = os.path.join(folder, session_id)

    chat_data = {
        "title": "New Chat",
        "created": datetime.now().isoformat(),
        "history": []
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(chat_data, f, indent=2)
    return session_id

def save_message(user_id, session_id, user_msg, bot_reply):
    path = os.path.join(get_user_folder(user_id), session_id)
    if not os.path.exists(path): return False

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    data["history"].append({
        "timestamp": datetime.now().isoformat(),
        "user": user_msg,
        "bot": bot_reply,
    })

    # Update title using summary
    if data["title"] == "New Chat" and len(data["history"]) >= 2:
        data["title"] = summarize_title([m["user"] for m in data["history"]])

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return True

def find_session_by_title(user_id, title):
    folder = get_user_folder(user_id)
    for file in os.listdir(folder):
        if file.endswith(".json"):
            path = os.path.join(folder, file)
            with open(path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    if data.get("title") == title:
                        return file  # return session ID
                except:
                    continue
    return None

def get_chat_history(user_id, session_id):
    path = os.path.join(get_user_folder(user_id), session_id)
    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    history = []
    for entry in data.get("history", []):
        history.append({
            "text": entry["user"],
            "timestamp": entry["timestamp"],
        })
    return history


# Init model
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# -------------------------------
# Token helpers
# -------------------------------
def count_tokens_gemini(messages, model_name="gpt-3.5-turbo"):
    enc = tiktoken.encoding_for_model(model_name)
    total = 0
    for msg in messages:
        for part in msg["parts"]:
            total += len(enc.encode(part))
    return total
    print(total)

def estimate_token_count(text: str) -> int:
    enc = tiktoken.encoding_for_model("gpt-3.5-turbo")
    return len(enc.encode(text))
    print(len(enc.encode(text)))
# -------------------------------
# File paths
# -------------------------------
def get_session_file_path(user_id: str, session_id: str) -> str:
    return os.path.join(CHAT_LOG_FOLDER, str(user_id), f"{session_id}.json")


def get_user_memory_folder(user_id: int) -> str:
    folder = os.path.join("data", "chat_logs", str(user_id), "memory")
    os.makedirs(folder, exist_ok=True)
    return folder


def get_long_term_memory_file_path(user_id: int) -> str:
    return os.path.join(get_user_memory_folder(user_id), "long_term_memory.json")


def get_weekly_summary_path(user_id: int) -> str:
    return os.path.join(get_user_memory_folder(user_id), "weekly_summary.txt")

# -------------------------------
# Memory summarizer
# -------------------------------
def load_memory_summary(user_id: str, session_id: str) -> str:
    path = get_session_file_path(user_id, session_id)
    
    if not os.path.exists(path):
        return ""

    with open(path, "r", encoding="utf-8") as f:
        chat_data = json.load(f)

    if "summary" in chat_data:
        return chat_data["summary"]

    # Build memory lines
    lines = []
    for entry in chat_data.get("history", []):
        user_msg = entry.get("user", "").strip()
        mood = entry.get("mood", "").strip() if "mood" in entry else ""
        if user_msg:
            line = f"User: {user_msg}"
            if mood:
                line += f" (Mood: {mood})"
            lines.append(line)

    full_text = "\n".join(lines)

    if estimate_token_count(full_text) > 300:
        try:
            response = model.generate_content(f"Summarize this chat for memory like perfectly and only the memory no extra parts:\n{full_text}")
            summary_text = response.text.strip()
            chat_data["summary"] = summary_text
            with open(path, "w", encoding="utf-8") as fw:
                json.dump(chat_data, fw, indent=2)
            return summary_text
        except Exception as e:
            return f"⚠️ Summarization failed: {e}\n\n{full_text}"
    else:
        return full_text
    print(full_text)


# -------------------------------
# 1. See Msg – extract real memory
# -------------------------------
def see_msg(user_id: int, user_msg: str):
    if len(user_msg.strip()) < 4:
        return

    prompt = f"""
Extract useful memory info from this message:
"{user_msg}"

Only return a valid JSON dictionary of facts like name, city, goal etc.
Ignore small talk or greetings. Example output:

{{
  "name": "Naiem",
  "city": "Delhi"
}}
"""

    try:
        response = model.generate_content(prompt)
        raw = response.text.strip()

        # ✅ Fix: Safely find and parse the first JSON block
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1:
            print(f"[Memory Extract Error] No JSON in output:\n{raw}")
            return

        json_str = raw[start:end+1]
        facts = json.loads(json_str)

        if isinstance(facts, dict):
            append_user_memory(user_id, facts)
    except json.JSONDecodeError as e:
        print(f"[Memory Extract Error] Invalid JSON from model:\n{e}\nRaw:\n{response.text}")
    except Exception as e:
        print(f"[Memory Extract Error] {e}")


# -------------------------------
# 2. Append user memory
# -------------------------------
def append_user_memory(user_id, facts):
    path = get_long_term_memory_file_path(user_id)
    existing = {}

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            existing = json.load(f)

    conflicts = {}
    for key, new_val in facts.items():
        old_val = existing.get(key)
        if old_val and old_val != new_val:
            conflicts[key] = (old_val, new_val)

    # Notify if conflicts
    if conflicts:
        conflict_msg = "\n".join([f"{k}: {v[0]} ➤ {v[1]}" for k, v in conflicts.items()])
        print(f"⚠️ Memory conflict for user {user_id}:\n{conflict_msg}")
        # Optionally: send alert to admin or ask user to confirm

    existing.update(facts)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)

# -------------------------------
# 3. Load memory before reply
# -------------------------------
def get_user_memory(user_id: int) -> str:
    path = get_long_term_memory_file_path(user_id)
    if not os.path.exists(path):
        return ""
    
    with open(path, "r", encoding="utf-8") as f:
        memory = json.load(f)

    memory_lines = [f"{k.capitalize()}: {', '.join(v) if isinstance(v, list) else v}" for k, v in memory.items()]
    return "\n".join(memory_lines)

# -------------------------------
# 4. Final Response Generator
# -------------------------------
from admin.user_profiles import get_user_profile
from chat.chat_engine import get_user_memory  # Make sure this is available

def get_recent_chat_history(user_id, session_id, limit=5):
    path = os.path.join(get_user_folder(user_id), session_id)
    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data.get("history", [])[-limit:]

def run_weekly_summary(user_id):
    folder = get_user_folder(user_id)
    summaries = []
    
    for file in os.listdir(folder):
        if file.endswith(".json"):
            path = os.path.join(folder, file)
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                text = "\n".join([m["user"] for m in data.get("history", [])])
                if text.strip():
                    summaries.append(text)

    full_text = "\n\n---\n\n".join(summaries)
    if full_text.strip():
        response = model.generate_content(f"Summarize this week's chat:\n\n{full_text}")
        summary = response.text.strip()
        summary_path = get_weekly_summary_path(user_id)
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(summary)

def generate_response(prompt, user_id, session_id, memory=None):
    from admin.user_profiles import get_user_profile
    from chat.chat_engine import get_user_memory
    # Load user profile settings
    profile = get_user_profile(user_id)
    style = profile["settings"].get("style", "friendly")
    length = profile["settings"].get("length", "medium")
    language = profile["settings"].get("language", "english")

    # Load memory
    if memory is None:
        memory = get_user_memory(user_id)

    # Load recent chat history
    history_items = get_recent_chat_history(user_id, session_id, limit=5)
    history_text = "\n".join(
        f"User: {m['user']}\nBot: {m['bot']}" for m in history_items
    )

    # Prompt instructions
    style_map = {
        "friendly": "Be casual, warm, and friendly.",
        "formal": "Be clear, respectful, and formal.",
        "sarcastic": "Be witty and sarcastic, but not rude."
    }

    length_map = {
        "short": "Keep the response brief and concise.",
        "medium": "Use moderate length, explain with clarity.",
        "long": "Give detailed explanation with rich examples."
    }

    language_instruction = {
        "english": "Reply in English.",
        "hindi": "Reply in Hindi.",
        "bengali": "Reply in Bengali.",
        "urdu": "Reply in Urdu."
    }

    instructions = f"{style_map.get(style)} {length_map.get(length)} {language_instruction.get(language)}"

    # 🧠 Full prompt with memory + history
    full_prompt = f"""{instructions}

Known facts about the user:
{memory}

Recent chat history:
{history_text}

Now respond to the user's message:
User: {prompt}
"""

    try:
        response = model.generate_content(full_prompt)
        return response.text.strip()
    except Exception as e:
        return f"❌ Error from Gemini: {e}"

