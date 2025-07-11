from features.pdf import (
    encrypt_pdf, decrypt_pdf, ocr_pdf,
    merge_pdfs, split_pdf, compress_pdf,
    pdf_to_images
)
from telegram.ext import (
    CommandHandler, MessageHandler, ContextTypes, filters ,
    CallbackQueryHandler ,ApplicationBuilder ,CommandHandler, 
    CallbackQueryHandler
)
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.helpers import escape_markdown
from features.chat import handle_message , handle_chats , resume_chat , handle_new_chat , search_messages
from features.tearbox_extracter import expand_link
import google.generativeai as genai
import os  , asyncio
from features.image_extracter_and_genrater import handle_button , handle_photo
from config import GEMINI_API_KEY
from features.admin import (
    show_main_menu , show_profile , admin_panel , promote ,
      handle_settings_callback , admin_callback_handler , show_settings
)
concurrency_semaphore = asyncio.Semaphore(10)
gemini_model = genai.GenerativeModel("gemini-1.5-flash")
genai.configure(api_key=GEMINI_API_KEY)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    username = f"@{user.username}" if user.username else user.first_name or "there"
    name = escape_markdown(user.full_name or "", version=2)
    welcome_text = (
        f"👋 Hello {name}!\n\n"
        f"I’m *Void ChatBot*, built by *Zero_Spectrum* 💻\n"
        f"You can talk to me, generate images, ask questions, and more.\n\n"
        f"📋 Use the menu or send a message to begin!"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def handle_pdf_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Encrypt", callback_data="pdf_encrypt"),
         InlineKeyboardButton("Decrypt", callback_data="pdf_decrypt")],
        [InlineKeyboardButton("OCR", callback_data="pdf_ocr"),
         InlineKeyboardButton("Split", callback_data="pdf_split")],
        [InlineKeyboardButton("Merge", callback_data="pdf_merge"),
         InlineKeyboardButton("Compress", callback_data="pdf_compress")],
        [InlineKeyboardButton("Convert", callback_data="pdf_convert")]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📄 *PDF Tools* — Choose an option:", reply_markup=markup, parse_mode="Markdown")

async def handle_pdf_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    action = data.replace("pdf_", "" , 1)
    context.user_data["pdf_action"] = action
    if action == "encrypt":
        await query.edit_message_text(
            "🔐 *PDF → Encrypt*\n\n📄 Send the PDF you want to encrypt.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="pdf_back")]
            ]),
            parse_mode="Markdown"
        )
    elif action == "decrypt":
        await query.edit_message_text(
            "🔓 *PDF → Decrypt*\n\n📄 Send the PDF you want to decrypt.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="pdf_back")]
            ]),
            parse_mode="Markdown"
        )
    elif action == "ocr":
        await query.edit_message_text(
            "📝 *PDF → OCR*\n\n📄 Send the PDF to extract text.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="pdf_back")]
            ]),
            parse_mode="Markdown"
        )
    elif action == "compress":
        await query.edit_message_text(
            "📦 *PDF → Compress*\n\n📄 Send the PDF you want to compress.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="pdf_back")]
            ]),
            parse_mode="Markdown"
        )
    elif action == "split":
        await query.edit_message_text(
            "✂️ *PDF → Split*\n\n📄 Send the PDF to split.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="pdf_back")]
            ]),
            parse_mode="Markdown"
        )
    elif action == "merge":
        context.user_data["merge_files"] = []
        await query.edit_message_text(
            "➕ *PDF → Merge*\n\n📄 Send PDFs one by one. Type `done` to finish.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="pdf_back")]
            ]),
            parse_mode="Markdown"
        )
    elif action == "convert":
        keyboard = [
            [
                InlineKeyboardButton("PDF ➝ Image", callback_data="pdf_pdf_to_img"),
                InlineKeyboardButton("Image ➝ PDF", callback_data="pdf_img_to_pdf")
            ],
            [InlineKeyboardButton("🔙 Back", callback_data="pdf_back")]
        ]
        await query.edit_message_text("🔄 *PDF → Convert*\n\nChoose conversion type:", 
                                      reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif action == "pdf_to_img":
        await query.edit_message_text(
            "🖼️ *PDF → Images*\n\n📄 Send the PDF to convert to images.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="pdf_back")]
            ]),
            parse_mode="Markdown"
        )
    elif action == "img_to_pdf":
        context.user_data["image_files"] = []
        await query.edit_message_text(
            "🖼️ *Image → PDF*\n\n📷 Send all images you want to combine, then type `done`.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="pdf_back")]
            ]),
            parse_mode="Markdown"
        )
    elif action == "back":
        keyboard = [
            [InlineKeyboardButton("Encrypt", callback_data="pdf_encrypt"),
             InlineKeyboardButton("Decrypt", callback_data="pdf_decrypt")],
            [InlineKeyboardButton("OCR", callback_data="pdf_ocr"),
             InlineKeyboardButton("Split", callback_data="pdf_split")],
            [InlineKeyboardButton("Merge", callback_data="pdf_merge"),
             InlineKeyboardButton("Compress", callback_data="pdf_compress")],
            [InlineKeyboardButton("Convert", callback_data="pdf_convert")]
        ]
        await query.edit_message_text("📄 *PDF Tools* — Choose an option:",
                                      reply_markup=InlineKeyboardMarkup(keyboard),
                                      parse_mode="Markdown")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from pathlib import Path
    user_id = update.effective_user.id
    action = context.user_data.get("pdf_action")
    if not action:
        await update.message.reply_text("⚠️ No action selected. Use /pdf first.")
        return
    file = update.message.document
    file_name = os.path.basename(file.file_name)
    file_path = f"downloads/{user_id}/pdf/{file_name}"
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)

    os.makedirs("downloads", exist_ok=True)
    telegram_file = await file.get_file()
    await telegram_file.download_to_drive(file_path)

    if action == "encrypt":
        await update.message.reply_text("🔐 Send the password to encrypt this PDF:")
        context.user_data["file_path"] = file_path
        context.user_data["awaiting_password"] = True
    elif action == "decrypt":
        await update.message.reply_text("🔓 Send the password to decrypt this PDF:")
        context.user_data["file_path"] = file_path
        context.user_data["awaiting_password"] = True
    elif action == "ocr":
        text = ocr_pdf(file_path)
        await update.message.reply_text(f"📝 OCR Text:\n\n{text[:4000]}")  # Telegram limit
        context.user_data["pdf_action"] = None
    elif action == "compress":
        output_path = f"downloads/{user_id}/pdf/compressed.pdf"
        compress_pdf(file_path , user_id)
        await update.message.reply_document(document=open(output_path, "rb"))
        context.user_data["pdf_action"] = None
    elif action == "split":
        context.user_data["file_path"] = file_path
        context.user_data["awaiting_ranges"] = True
        await update.message.reply_text("✂️ Enter page ranges to split (e.g. 1-3,5-7):")
        context.user_data["pdf_action"] = None
    elif action == "merge":
        if "merge_files" not in context.user_data:
            context.user_data["merge_files"] = []
        context.user_data["merge_files"].append(file_path)
        await update.message.reply_text("✅ PDF added. Send more PDFs or type 'done' to finish merge.")
        # 🛑 DO NOT CLEAR `pdf_action` HERE
    elif action == "pdf_to_img":
        zip_path = pdf_to_images(file_path)  # now a string
        await update.message.reply_document(document=open(zip_path, "rb"))
        context.user_data["pdf_action"] = None

async def handle_image_to_pdf_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from PIL import Image
    user_id = update.effective_user.id
    image_files = context.user_data.get("image_files")

    if not image_files or len(image_files) < 1:
        await update.message.reply_text("⚠️ No images received yet.")
        return
    os.makedirs(f"downloads/{user_id}" , exist_ok=True)
    output_path = f"downloads/{user_id}/pdf/images_output.pdf"
    images = [Image.open(p).convert("RGB") for p in image_files]

    images[0].save(output_path, save_all=True, append_images=images[1:])
    await update.message.reply_document(document=open(output_path, "rb"))
    
    # Cleanup
    context.user_data.pop("image_files", None)
    context.user_data["pdf_action"] = None

from pdf2image import convert_from_path
import zipfile
import os

def pdf_to_images(pdf_path , update : Update):
    user_id = update.effective_user.id
    output_dir = (f"downloads/{user_id}/pdf/pdf_images")
    os.makedirs(output_dir, exist_ok=True)

    images = convert_from_path(pdf_path)
    image_paths = []

    for i, image in enumerate(images):
        img_path = os.path.join(output_dir, f"page_{i+1}.jpg")
        image.save(img_path, "JPEG")
        image_paths.append(img_path)

    # Zip the images
    zip_path = os.path.join("downloads", os.path.basename(pdf_path).replace(".pdf", "_images.zip"))
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for img in image_paths:
            zipf.write(img, os.path.basename(img))

    return zip_path  # 🟢 return zip path, not list

async def handle_pdf_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    action = context.user_data.get("pdf_action")
    if action != "img_to_pdf":
        return  # Not relevant

    user_id = update.effective_user.id
    photo = update.message.photo[-1]
    file = await photo.get_file()

    os.makedirs("downloads", exist_ok=True)
    file_path = f"downloads/{user_id}/pdf/{user_id}_{photo.file_unique_id}.jpg"
    await file.download_to_drive(file_path)

    context.user_data.setdefault("image_files", []).append(file_path)

    await update.message.reply_text("🖼️ Image added. Send more or type 'done' to finish.")

from fpdf import FPDF
from PIL import Image

def convert_images_to_pdf(image_paths, output_path):
    pdf = FPDF()
    for img_path in image_paths:
        cover = Image.open(img_path)
        width, height = cover.size
        width_mm = width * 0.264583
        height_mm = height * 0.264583

        pdf.add_page()
        pdf.image(img_path, 0, 0, width_mm, height_mm)
    pdf.output(output_path)

async def handle_merge_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    action = context.user_data.get("pdf_action")

    if action == "merge":
        files = context.user_data.get("merge_files", [])
        if len(files) < 2:
            await update.message.reply_text("⚠️ At least 2 PDFs needed to merge.")
            return

        output_path = f"downloads/{update.effective_user.id}/pdf/merged.pdf"
        merge_pdfs(files, output_path)
        await update.message.reply_document(document=open(output_path, "rb"))
        context.user_data.clear()

    elif action == "img_to_pdf":
        images = context.user_data.get("image_files", [])
        if not images:
            await update.message.reply_text("⚠️ No images received.")
            return

        output_path = f"downloads/{update.effective_user.id}/pdf/converted.pdf"
        convert_images_to_pdf(images, output_path)
        await update.message.reply_document(document=open(output_path, "rb"))
        context.user_data.clear()

async def handle_password_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    password = update.message.text.strip()
    file_path = context.user_data.get("file_path")
    mode = context.user_data.get("awaiting_password")

    if not file_path or not mode:
        return

    if mode == "encrypt":
        output_path = f"downloads/{user_id}/pdf/encrypted.pdf"
        encrypt_pdf(file_path, password, output_path)
        await update.message.reply_document(document=open(output_path, "rb"))

    elif mode == "decrypt":
        output_path = f"downloads/{user_id}/pdf/decrypted.pdf"
        success = decrypt_pdf(file_path, password, output_path)
        if success:
            await update.message.reply_document(document=open(output_path, "rb"))
        else:
            await update.message.reply_text("❌ Failed to decrypt. Wrong password?")

    # Clear memory
    context.user_data.pop("file_path", None)
    context.user_data.pop("awaiting_password", None)

async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.effective_user.id

    try:
        # 🟡 Password for encryption/decryption
        if context.user_data.get("awaiting_password"):
            file_path = context.user_data.get("file_path")
            password = text
            action = context.user_data.get("pdf_action")
            output = f"downloads/{user_id}/pdf/{action}.pdf"

            if action == "encrypt":
                encrypt_pdf(file_path, password, output)
            elif action == "decrypt":
                decrypt_pdf(file_path, password, output)
            else:
                await update.message.reply_text("⚠️ Invalid PDF action.")
                return

            await update.message.reply_document(document=open(output, "rb"))
            context.user_data.clear()
            return

        # 🟡 Split PDF
        if context.user_data.get("awaiting_ranges"):
            file_path = context.user_data.get("file_path")
            output_paths = split_pdf(file_path, text, user_id)

            for path in output_paths:
                await update.message.reply_document(document=open(path, "rb"))
            context.user_data.clear()
            return

        # 🟡 Merge PDF
        if text.lower() == "done" and "merge_files" in context.user_data:
            files = context.user_data["merge_files"]
            if len(files) < 2:
                await update.message.reply_text("⚠️ At least 2 PDFs needed to merge.")
                return

            output_path = f"downloads/{user_id}/pdf/merged.pdf"
            merge_pdfs(files, output_path)
            await update.message.reply_document(document=open(output_path, "rb"))

            # ✅ Clear everything
            context.user_data.clear()
            return
        # 🔄 If not related to PDF, fallback to AI/chat
        await handle_message(update, context)

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

def main():
    from config import BOT_TOKEN
    from telegram import BotCommand
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # PDF features
    app.add_handler(CommandHandler("pdf", handle_pdf_command))
    app.add_handler(CallbackQueryHandler(handle_pdf_button, pattern="^pdf_"))
    app.add_handler(CallbackQueryHandler(handle_pdf_button, pattern="^(pdf_|img_to_pdf|pdf_to_img)$"))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("(?i)^done$"), handle_merge_done))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_document))
    app.add_handler(MessageHandler(filters.PHOTO, handle_pdf_photos))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("(?i)^done$"), handle_text_input))  # Merge "done"
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))  # Password, ranges, etc.
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("(?i)^done$"), handle_image_to_pdf_done))

    # Admin things
    app.add_handler(CommandHandler("menu", show_main_menu))
    app.add_handler(CommandHandler("settings", show_settings))
    app.add_handler(CommandHandler("promote", promote))
    app.add_handler(CallbackQueryHandler(handle_settings_callback, pattern="^(set_|style_|length_|lang_)"))
    app.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^admin_"))
    app.add_handler(CallbackQueryHandler(handle_button, pattern="^copy_text$"))
    app.add_handler(CommandHandler("admin", admin_panel)) 
    app.add_handler(CommandHandler("profile", show_profile))
    
    # AI Chat / General
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("chats", handle_chats))
    app.add_handler(CommandHandler("newchat", handle_new_chat))
    app.add_handler(CommandHandler("resume", resume_chat))
    app.add_handler(CommandHandler("search", search_messages))
    app.add_handler(CommandHandler("expand", expand_link))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))  # Catch everything else

    #Finally Running.
    print("✅ Bot is running...")
    app.run_polling()

#Warping all The Stuff as usual
if __name__ == "__main__":
    main()
