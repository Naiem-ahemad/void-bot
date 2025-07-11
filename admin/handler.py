# tg_bots/admin/handler.py

from telegram import Update
from telegram.ext import ContextTypes
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from admin.user_manager import get_total_users
from admin.logs import get_latest_logs
import os , json
USERS_DIR = "data/users"
ADMIN_IDS = [7840020962] # replace with your Telegram ID

def is_admin(user_id):
    try:
        user_file = os.path.join(USERS_DIR, f"{user_id}.json")
        if not os.path.exists(user_file):
            return False
        with open(user_file, "r", encoding="utf-8") as f:
            profile = json.load(f)
            return profile.get("role") == "admin"
    except:
        return False


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ Access Denied.")
        return

    keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("📊 Users", callback_data="admin_users"),
     InlineKeyboardButton("📁 Logs", callback_data="admin_logs")],
    [InlineKeyboardButton("📨 Broadcast", callback_data="admin_broadcast"),
     InlineKeyboardButton("🗑️ Delete User", callback_data="admin_delete_user")],
    [InlineKeyboardButton("👑 Admins", callback_data="admin_list_admins")]  # <-- new
    ])

    await update.message.reply_text("Welcome to the Admin Panel:", reply_markup=keyboard)

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if not is_admin(user_id):
        await query.edit_message_text("❌ Access Denied.")
        return

    if query.data == "admin_users":
        total = get_total_users()
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Back", callback_data="admin_back")]
        ])
        await query.edit_message_text(f"👥 Total users: {total}", reply_markup=keyboard)

    elif query.data == "admin_logs":
        logs = get_latest_logs()
        text = "\n\n---\n\n".join(logs)
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="admin_back")]])
        await query.edit_message_text(f"📁 Recent Logs:\n\n{text}", parse_mode="Markdown", reply_markup=keyboard)

    elif query.data == "admin_broadcast":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Back", callback_data="admin_back")]
        ])
        await query.edit_message_text("✉️ Send the broadcast message now:", reply_markup=keyboard)
        context.user_data["awaiting_broadcast"] = True

    elif query.data == "admin_delete_user":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Back", callback_data="admin_back")]
        ])
        await query.edit_message_text("🗑️ Send the user ID to delete:", reply_markup=keyboard)
        context.user_data["awaiting_delete_user"] = True
    elif query.data == "admin_list_admins":
        admin_profiles = []
        for file in os.listdir(USERS_DIR):
            path = os.path.join(USERS_DIR, file)
            with open(path, encoding="utf-8") as f:
                profile = json.load(f)
                if profile.get("role") == "admin":
                    name = profile.get("name", "Unknown")
                    uid = profile.get("user_id", "")
                    admin_profiles.append(f"👑 {name} (`{uid}`)")

        if not admin_profiles:
            await query.edit_message_text("❌ No admins found.")
        else:
            await query.edit_message_text("👑 *Admins List:*\n\n" + "\n".join(admin_profiles), parse_mode="Markdown")
    elif query.data == "admin_back":
    # Resend main admin panel
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 Users", callback_data="admin_users"),
            InlineKeyboardButton("📁 Logs", callback_data="admin_logs")],
            [InlineKeyboardButton("📨 Broadcast", callback_data="admin_broadcast"),
            InlineKeyboardButton("🗑️ Delete User", callback_data="admin_delete_user")]
        ])
        await query.edit_message_text("🔙 Back to Admin Panel:", reply_markup=keyboard)
