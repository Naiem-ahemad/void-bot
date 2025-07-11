import os , json
from telegram.ext import (
  ContextTypes, filters 
)
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from admin.user_profiles import USERS_DIR, get_user_profile
from admin.user_profiles import get_user_profile, ensure_user_profile
from admin.handler import admin_panel, admin_callback_handler , is_admin
from telegram.helpers import escape_markdown

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # Ensure profile exists and is safe
    ensure_user_profile(user)
    profile = get_user_profile(user.id)

    if not profile:
        await update.message.reply_text("❌ Profile not found.")
        return

    # Extract info with fallback
    name = escape_markdown(profile.get("name", ""), version=2)
    username = profile.get("username") or "N/A"
    user_id = str(profile.get("user_id", user.id))
    joined = escape_markdown(profile.get("joined_at", "")[:10], version=2)
    count = str(profile.get("message_count", 0))

    # Optional: show settings too
    settings = profile.get("settings", {})
    style = settings.get("style", "friendly")
    length = settings.get("length", "medium")
    language = settings.get("language", "english")

    text = (
        f"🧑 *Name:* {name}\n"
        f"🔗 *Username:* `@{escape_markdown(username, version=2)}`\n"
        f"🆔 *ID:* `{user_id}`\n"
        f"📅 *Joined:* {joined}\n"
        f"💬 *Messages:* {count}\n\n"
        f"⚙️ *Chat Style:* `{style}`\n"
        f"📏 *Reply Length:* `{length}`\n"
        f"🌐 *Language:* `{language}`"
    )

    await update.message.reply_text(text, parse_mode="MarkdownV2")

from admin.user_profiles import get_user_profile
async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    profile = get_user_profile(user_id)

    settings = profile.get("settings", {})
    style = settings.get("style", "friendly")
    length = settings.get("length", "medium")
    lang = settings.get("language", "english")

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Style: {style.capitalize()}", callback_data="set_style")],
        [InlineKeyboardButton(f"Reply Length: {length.capitalize()}", callback_data="set_length")],
        [InlineKeyboardButton(f"Language: {lang.capitalize()}", callback_data="set_lang")]
    ])
    await update.message.reply_text("🛠️ Your Current Settings:", reply_markup=keyboard)


from admin.user_profiles import get_user_profile, ensure_user_profile, USERS_DIR, DEFAULT_SETTINGS
async def handle_settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    # Ensure profile exists with default structure
    ensure_user_profile(query.from_user)
    profile = get_user_profile(user_id)

    # Ensure settings key is always present
    if "settings" not in profile:
        profile["settings"] = DEFAULT_SETTINGS.copy()
    settings = profile["settings"]

    # Style selection menu
    if query.data == "set_style":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Friendly 😊", callback_data="style_friendly"),
             InlineKeyboardButton("Formal 🧑‍💼", callback_data="style_formal")],
            [InlineKeyboardButton("Sarcastic 😏", callback_data="style_sarcastic"),
             InlineKeyboardButton("🖊️ Custom", callback_data="style_custom")]
        ])
        await query.edit_message_text("🧠 Choose your chat style:", reply_markup=keyboard)

    # Length menu
    elif query.data == "set_length":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Short", callback_data="length_short"),
             InlineKeyboardButton("Medium", callback_data="length_medium"),
             InlineKeyboardButton("Long", callback_data="length_long")]
        ])
        await query.edit_message_text("📝 Choose reply length:", reply_markup=keyboard)

    # Language menu
    elif query.data == "set_lang":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("English 🇺🇸", callback_data="lang_english"),
             InlineKeyboardButton("Hindi 🇮🇳", callback_data="lang_hindi")]
        ])
        await query.edit_message_text("🌐 Choose language:", reply_markup=keyboard)

    # Handle updates to values
    elif query.data.startswith("style_"):
        new_style = query.data.split("_", 1)[1]
        settings["style"] = new_style
        await query.edit_message_text(f"✅ Style set to: *{new_style}*", parse_mode="Markdown")
        
    elif query.data.startswith("length_"):
        new_length = query.data.split("_", 1)[1]
        settings["length"] = new_length
        await query.edit_message_text(f"✅ Length set to: *{new_length}*", parse_mode="Markdown")
        
    elif query.data.startswith("lang_"):
        new_lang = query.data.split("_", 1)[1]
        settings["language"] = new_lang
        await query.edit_message_text(f"✅ Language set to: *{new_lang}*", parse_mode="Markdown")

    elif query.data == "style_custom":
        await query.edit_message_text("✏️ Send your custom style (e.g., 'sarcastic like Deadpool'):")
        context.user_data["awaiting_custom_style"] = True
        return

    else:
        return  # Unknown callback, ignore

    # Save back to file
    profile["settings"] = settings
    with open(os.path.join(USERS_DIR, f"{user_id}.json"), "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2)



async def handle_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "menu_profile":
        await query.edit_message_text("👤 *Profile*: Type /profile to view your full profile.", parse_mode="Markdown")
    elif data == "menu_settings":
        await query.edit_message_text("⚙️ *Settings*: Type /settings to customize chat style, language, and more.", parse_mode="Markdown")
    elif data == "menu_stats":
        await query.edit_message_text("📊 Stats feature coming soon!")
    elif data == "menu_logs":
        await query.edit_message_text("📁 Logs are admin-only. If you're an admin, use /admin.")
    elif data == "menu_chat":
        await query.edit_message_text("💬 Just send me a message and I'll reply with AI magic ✨")
    elif data == "menu_help":
        await query.edit_message_text("ℹ️ *Help*\n\nCommands:\n/start – Start Bot\n/menu – Main Menu\n/profile – View profile\n/settings – Change style\n/help – Show help", parse_mode="Markdown")

from telegram import InlineKeyboardMarkup, InlineKeyboardButton

async def promote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Only admins can promote.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /promote <user_id>")
        return

    target_id = context.args[0]

    try:
        uid = int(target_id)
        user_file = os.path.join(USERS_DIR, f"{uid}.json")
        if not os.path.exists(user_file):
            await update.message.reply_text("❌ User not found.")
            return

        with open(user_file, "r", encoding="utf-8") as f:
            profile = json.load(f)

        profile["role"] = "admin"

        with open(user_file, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2)

        # Notify admin and the user
        await update.message.reply_text(f"✅ User `{uid}` promoted to admin.", parse_mode="Markdown")
        await context.bot.send_message(chat_id=uid, text="🎉 You have been promoted to *Admin*!", parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 Profile", callback_data="menu_profile"),
         InlineKeyboardButton("⚙️ Settings", callback_data="menu_settings")],
        [InlineKeyboardButton("📊 Stats", callback_data="menu_stats"),
         InlineKeyboardButton("📁 Logs", callback_data="menu_logs")],
        [InlineKeyboardButton("🧠 Chat with AI", callback_data="menu_chat")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="menu_help")]
    ])

    await update.message.reply_text("📋 *Main Menu* — Select an option below:", 
                                    reply_markup=keyboard, parse_mode="Markdown")