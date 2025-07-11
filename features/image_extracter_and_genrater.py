from telegram.ext import (
     ContextTypes, filters
)
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
import os ,uuid
from images.extractor import extract_text_from_image , clean_text_with_gemini

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 1. Show "Extracting..." lo
    loading_msg = await update.message.reply_text("⏳ Extracting...")

    try:
        # 2. Download image
        photo_file = await update.message.photo[-1].get_file()
        filename = f"{uuid.uuid4()}.jpg"
        file_path = os.path.join("downloads/images", filename)
        await photo_file.download_to_drive(file_path)

        # 3. Extract and clean text
        raw_text = extract_text_from_image(file_path)
        clean_text = clean_text_with_gemini(raw_text)

        # 4. Delete "Extracting..." message
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=loading_msg.message_id)

        # 5. Add copy button
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 Copy Text", callback_data="copy_text")]
        ])

        # 6. Send final cleaned text with button
        sent_msg = await update.message.reply_text(
            f"📝 Extracted & Cleaned Text:\n\n<code>{clean_text}</code>",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

        context.user_data["last_extracted_text"] = clean_text
        context.user_data["copy_message_id"] = sent_msg.message_id
        # Optional: Save clean text to context for later copy
        context.user_data["last_extracted_text"] = clean_text
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to process image: {e}")
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("✅ Ready to copy!", show_alert=False)

    if query.data == "copy_text":
        text = context.user_data.get("last_extracted_text", "❌ Nothing to copy.")
        message_id = context.user_data.get("copy_message_id", None)

        if message_id:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=message_id,
                text=f"✅ Click to Copy:\n\n<code>{text}</code>",
                parse_mode="HTML"
            )
