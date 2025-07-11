from telegram.ext import (
    CommandHandler, MessageHandler, ContextTypes, filters ,
    CallbackQueryHandler ,ApplicationBuilder ,CommandHandler, 
    CallbackQueryHandler
)
from telegram import  InlineKeyboardMarkup, InlineKeyboardButton , Update
from telegram.constants import ChatAction
import requests 

TERABOX_API = "https://teraboxx.vercel.app/api?url="

async def expand_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text(
            "❗ Please provide a TeraBox link to expand.\n\nExample:\n`/expand https://terabox.com/s/xyz...`",
            parse_mode="Markdown"
        )
    short_url = context.args[0].strip()
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    loading_msg = await update.message.reply_text("⏳ Expanding your TeraBox link...")
    try:
        response = requests.get(TERABOX_API + short_url, timeout=15)
        response.raise_for_status()
        data = response.json()

        # Handle API failure
        if data.get("status") != "success" or not data.get("Extracted Info"):
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=loading_msg.message_id)
            return await update.message.reply_text("❌ Could not expand link or no downloadable files found.")

        # Delete loading message for smooth Telegram UI
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=loading_msg.message_id)

        # Format message
        lines = []
        buttons = []

        for item in data["Extracted Info"]:
            title = item.get("Title", "Untitled File")
            size = item.get("Size", "Unknown Size")
            dl_link = item.get("Direct Download Link")
            lines.append(f"*🎬{title}*\n\n📦 Size: `{size}`")
            buttons.append([InlineKeyboardButton("📥 Download", url=dl_link)])
        reply_markup = InlineKeyboardMarkup(buttons)

        # Send final message
        await update.message.reply_text(
            "\n\n".join(lines),
            parse_mode="Markdown",
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
    except Exception as e:
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=loading_msg.message_id)
        await update.message.reply_text(f"❌ Error expanding link:\n`{e}`", parse_mode="Markdown")
