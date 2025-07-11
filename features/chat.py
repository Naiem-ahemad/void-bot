from chat.chat_engine import generate_response
from chat.chat_engine import save_message
from chat.chat_engine import list_chats , start_new_chat
from chat.chat_engine import rename_chat_title , get_user_folder
from chat.chat_engine import list_chats, get_user_folder
from chat.chat_engine import find_session_by_title
from chat.intent_detector import detect_intent
from chat.chat_engine import see_msg, get_user_memory, generate_response
import google.generativeai as genai
gemini_model = genai.GenerativeModel("gemini-1.5-flash")
from config import GEMINI_API_KEY
genai.configure(api_key=GEMINI_API_KEY)
from telegram import Update, InputFile , InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ChatAction
from telegram.ext import  CommandHandler, MessageHandler, ContextTypes, filters ,CallbackQueryHandler ,ApplicationBuilder
from telegram.ext import CommandHandler, CallbackQueryHandler
from telegram.ext import CommandHandler
import emoji , os, json  , asyncio , shutil
from images.generator import generate_image
from chat.chat_engine import see_msg, get_user_memory, generate_response
from admin.user_manager import get_all_user_ids
concurrency_semaphore = asyncio.Semaphore(10)
def detect_mood(user_msg):
    model = gemini_model
    prompt = f"""Analyze the emotional mood of this message and respond with only one emoji and a short mood label (max 2 words). Do not explain anything.

Message: "{user_msg}"
Mood:"""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return "😐 Neutral"



async def resume_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Get title from user argument (like /resume Naiem's Name)
    if not context.args:
        await update.message.reply_text("❌ Please provide a chat title. Usage: /resume <chat_title>")
        return

    title = " ".join(context.args).strip()

    session_id = find_session_by_title(user_id, title)
    if session_id:
        context.user_data["session_id"] = session_id  # 🔥 this is what your bot uses
        await update.message.reply_text(f"✅ Resumed your chat: {title}")
    else:
        await update.message.reply_text(f"❌ No chat found with title: {title}")

async def handle_new_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    session_id = start_new_chat(user_id)

    # Store this session in user_data
    context.user_data["session_id"] = session_id
    await update.message.reply_text(f"✅ New chat started!\nSession ID: `{session_id}`", parse_mode="Markdown")

def extract_emojis(text: str) -> list:
    """Extracts emojis from a string"""
    return [char for char in text if char in emoji.EMOJI_DATA]
# chat/emoji_detector.py
def detect_emoji_response(text: str) -> str | None:
    emojis = extract_emojis(text)
    if not emojis:
        return None

    prompt = (
        f"The user sent these emojis: {' '.join(emojis)}.\n"
        f"Reply with exactly ONE emoji that best expresses a creative, meaningful or playful reaction."
    )

    try:
        response = gemini_model.generate_content(prompt)
        # Filter response to include only valid emojis
        emoji_response = ''.join([char for char in response.text if char in emoji.EMOJI_DATA])
        return emoji_response[0] if emoji_response else None  # only return one emoji
    except Exception:
        return None

# Start command
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

async def handle_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    sessions = list_chats(user_id)

    if not sessions:
        await update.message.reply_text("❌ No previous chats found.")
        return

    msg = "🗂️ Your previous chats:\n\n"
    for i, chat in enumerate(sessions, 1):
        msg += f"{i}. {chat['title']} — ID: `{chat['id']}`\n"

    await update.message.reply_text(msg, parse_mode="Markdown")


async def handle_user_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from admin.user_profiles import ensure_user_profile
    ensure_user_profile(update.message.from_user)
    user_msg = update.message.text
    user_id = update.message.from_user.id

    emoji_reply = detect_emoji_response(user_msg)
    if emoji_reply:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        await asyncio.sleep(10)
        await update.message.reply_text(emoji_reply)
        return

    intent = detect_intent(user_msg)
    print(intent)
    if intent == "image":
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        loading_msg = await update.message.reply_text("⏳ Generating image...")
        try:
            img_path = generate_image(user_msg , user_id)
            img_path = os.path.abspath(img_path)
            if not os.path.exists(img_path):
                await update.message.reply_text("❌ Image file not found.")
                return
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=loading_msg.message_id)
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_PHOTO)
            with open(img_path, 'rb') as photo:
                await update.message.reply_photo(photo=InputFile(photo), caption=f"🎨 Generated for: '{user_msg}'")
        except Exception as e:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=loading_msg.message_id)
            await update.message.reply_text(f"❌ Failed to generate image: {e}")
        return

    if intent == "search":
        from chat.summarizer import Real_time_summary , web_search
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        loading_msg = await update.message.reply_text("🔍 Searching...")
        try:
            raw_results = web_search(user_msg)
            summary = Real_time_summary(raw_results)
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=loading_msg.message_id)
            await update.message.reply_text(f"📄 Summary:\n\n{summary}")
        except Exception as e:
            await update.message.reply_text(f"❌ Search failed: {e}")
        return

    if intent == "chat":
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        await asyncio.sleep(min(len(user_msg) * 0.03, 3))
        mood = detect_mood(user_msg)
        # ✅ Step 1: Ensure session exists
        session_id = context.user_data.get("session_id")
        if not session_id:
            session_id = start_new_chat(user_id)
            context.user_data["session_id"] = session_id
        # ✅ Step 2: Extract memory from message (for future)
        see_msg(user_id, user_msg)
        # ✅ Step 3: Load memory (summarized or raw)
        from chat.chat_engine import load_memory_summary
        memory_summary = load_memory_summary(user_id, session_id)
        full_memory = get_user_memory(user_id)
        # ✅ Step 4: Generate response using full memory
        bot_reply = generate_response(user_msg, user_id, session_id, memory=full_memory)
        # ✅ Step 5: Save message
        success = save_message(user_id, session_id, user_msg, bot_reply)
        # ✅ Step 6: Reply to user
        await update.message.reply_text(f"{bot_reply}\n\n🧠 Detected Mood: {mood}")
        from chat.chat_engine import run_weekly_summary
        from datetime import datetime
        # Maybe run it once every 7 days using a timestamp in context or file
        last_summary_path = os.path.join("data", "chat_logs", str(user_id), str("memory") ,"last_summary.txt")
        if not os.path.exists(last_summary_path) or (
            (datetime.now() - datetime.fromisoformat(open(last_summary_path).read())).days >= 7
        ):
            run_weekly_summary(user_id)
            with open(last_summary_path, "w") as f:
                f.write(datetime.now().isoformat())
        return

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    user_id = update.message.from_user.id
    if context.user_data.get("awaiting_broadcast"):
        context.user_data["awaiting_broadcast"] = False
        success = 0
        failed = 0

        users = get_all_user_ids()
        for uid in users:
            try:
                await context.bot.send_message(chat_id=int(uid), text=text)
                success += 1
            except Exception:
                failed += 1

        await update.message.reply_text(f"📢 Broadcast sent to {success} users ✅, failed for {failed} ❌")
        return

    # ✅ Awaiting delete user
    if context.user_data.get("awaiting_delete_user"):
        context.user_data["awaiting_delete_user"] = False
        uid = text
        user_path = os.path.join("data/chat_logs", uid)

        if os.path.exists(user_path):
            shutil.rmtree(user_path)
            await update.message.reply_text(f"✅ Deleted all data for user: {uid}")
        else:
            await update.message.reply_text(f"❌ User ID not found: {uid}")
        return

    # ✅ Awaiting custom style
    if context.user_data.get("awaiting_custom_style"):
        from admin.user_profiles import get_user_profile, USERS_DIR
        profile = get_user_profile(user_id)
        style_text = text

        profile.setdefault("settings", {})["style"] = style_text
        with open(os.path.join(USERS_DIR, f"{user_id}.json"), "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2)

        context.user_data["awaiting_custom_style"] = False
        await update.message.reply_text(f"✅ Custom style saved: `{style_text}`", parse_mode="Markdown")
        return

    # ✅ Default logic
    async def limited_user_handler():
        async with concurrency_semaphore:
            await handle_user_logic(update, context)

    asyncio.create_task(limited_user_handler())

async def search_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("❌ Please provide a keyword to search.\nUsage: `/search hello`", parse_mode="Markdown")
        return

    keyword = " ".join(context.args).lower()
    from chat.chat_engine import get_user_folder

    user_folder = get_user_folder(user_id)
    if not os.path.exists(user_folder):
        await update.message.reply_text("❌ No previous chats found.")
        return

    results = []
    for filename in os.listdir(user_folder):
        if not filename.endswith(".json"):
            continue
        with open(os.path.join(user_folder, filename), "r", encoding="utf-8") as f:
            data = json.load(f)
            for item in data.get("history", []):
                user_msg = item.get("user", "").lower()
                bot_msg = item.get("bot", "")
                if keyword in user_msg:
                    results.append(f"🗨️ *You:* {user_msg}\n🤖 *Bot:* {bot_msg}\n")

    if not results:
        await update.effective_message.reply_text("🔍 No results found.")
    else:
        chunks = [results[i:i+3] for i in range(0, len(results), 3)]
        for chunk in chunks[:5]:  # Limit to first 5 chunks
            await update.effective_message.reply_text("\n".join(chunk), parse_mode="Markdown")