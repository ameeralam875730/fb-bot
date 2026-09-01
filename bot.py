import os
import requests
import yt_dlp
import random
import string
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Dummy Web Server (Render Keep-Alive Ke Liye)
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot 24/7 Running!")

def run_health_check_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

# CONFIGURATION
BOT_TOKEN = os.getenv("BOT_TOKEN", "8811073395:AAHSWle6K63IwF4f2lvotJHCyQyZwYLasrY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")
ADMIN_ID = 1523935298

BOT_NAME = "MediaLyrics AI Pro"
BOT_OWNER = "@AmeerBro786"

KEYS_DB = {}
USERS_DB = {}

def generate_random_key(prefix="AMEER-", length=10):
    chars = string.ascii_uppercase + string.digits
    return prefix + "".join(random.choice(chars) for _ in range(length))

def is_user_active(user_id):
    if user_id == ADMIN_ID:
        return True
    if user_id in USERS_DB:
        expiry = USERS_DB[user_id]
        if datetime.now() < expiry:
            return True
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    welcome_msg = (
        f"✨ **Welcome to {BOT_NAME}!** ✨\n\n"
        "Main aapke bhejey hue video se poora **Speech / Lyrics** extract karke de sakta hoon.\n\n"
        "🌐 **Supported Platforms:**\n"
        "• 📘 Facebook Videos & Reels\n"
        "• 🔴 YouTube Videos & Shorts\n"
        "• 📸 Instagram Reels & Posts\n\n"
        "📌 **Kaise use karein?**\n"
        "Bas kisi bhi video ka link niche chat me send karein!"
    )

    if user_id == ADMIN_ID:
        keyboard = [
            [
                InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/AmeerBro786"),
                InlineKeyboardButton("🔑 Generate Key", callback_data="admin_genkey_type")
            ]
        ]
    elif is_user_active(user_id):
        keyboard = [[InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/AmeerBro786")]]
    else:
        restricted_msg = (
            f"⛔ **ACCESS RESTRICTED!**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Aap is bot ko bina **Activation Key** ke use nahi kar sakte.\n\n"
            f"🔑 **Key prapt karne ke liye Admin se contact karein:**\n👉 {BOT_OWNER}\n\n"
            f"--------------------------------------\n"
            f"Aapke paas key hai toh redeem karein:\n`/redeem YOUR_KEY_HERE`"
        )
        keyboard = [[InlineKeyboardButton("💬 Contact Admin to Get Key", url="https://t.me/AmeerBro786")]]
        await update.message.reply_text(restricted_msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    await update.message.reply_text(welcome_msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        await query.message.reply_text("❌ Aap Admin nahi hain!")
        return

    if query.data == "admin_genkey_type":
        keyboard = [
            [InlineKeyboardButton("👤 Single User Key", callback_data="menu_single")],
            [InlineKeyboardButton("🌐 Multi User Key", callback_data="menu_multi")]
        ]
        await query.message.reply_text("🔑 **Kis type ki key generate karni hai?**", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "menu_single":
        keyboard = [[InlineKeyboardButton("7 Days", callback_data="gen_s_7"), InlineKeyboardButton("30 Days", callback_data="gen_s_30"), InlineKeyboardButton("365 Days", callback_data="gen_s_365")]]
        await query.message.reply_text("👤 **Single User Key Validity Chunein:**", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "menu_multi":
        keyboard = [[InlineKeyboardButton("7 Days", callback_data="gen_m_7"), InlineKeyboardButton("30 Days", callback_data="gen_m_30"), InlineKeyboardButton("365 Days", callback_data="gen_m_365")]]
        await query.message.reply_text("🌐 **Multi User Key Validity Chunein:**", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("gen_s_") or query.data.startswith("gen_m_"):
        is_multi = query.data.startswith("gen_m_")
        days = int(query.data.split("_")[2])
        prefix = "MULTI-" if is_multi else "AMEER-"
        new_key = generate_random_key(prefix=prefix)
        KEYS_DB[new_key] = {"days": days, "multi": is_multi, "used_by": []}

        type_str = "MULTI-USER (UNLIMITED USERS)" if is_multi else "SINGLE USER (1 PERSON ONLY)"
        note_str = "Yeh key koi bhi kitne bhi log use kar sakte hain." if is_multi else "Yeh key ek hi user ke liye hai. Single use only."

        msg = (
            f"🎉 **VIP ACCESS ACTIVATION KEY** 🎉\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔑 **Your Key:** `{new_key}`\n⏳ **Validity:** {days} Days\n👥 **Type:** {type_str}\n\n"
            f"📋 **KAISE USE KAREIN:**\n1. Bot par ja kar `/start` dabayein.\n2. Command bhejhein:\n\n`/redeem {new_key}`\n\n"
            f"⚠️ **Note:** {note_str}\n\n"
            f"🚫 **ADMIN CONTROL (To Turn Off Key):**\n`/revoke {new_key}`\n\n👨‍💻 **Owner:** {BOT_OWNER}"
        )
        await query.message.reply_text(msg, parse_mode="Markdown")

async def revoke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    try:
        target_key = context.args[0].strip()
    except IndexError:
        await update.message.reply_text("⚠️ **Format:** `/revoke <KEY_CODE>`")
        return

    if target_key in KEYS_DB:
        for uid in KEYS_DB[target_key]["used_by"]:
            if uid in USERS_DB:
                del USERS_DB[uid]
        del KEYS_DB[target_key]
        await update.message.reply_text(f"🚫 Key `{target_key}` revoke kar di gayi hai.", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Key nahi mili!")

async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id == ADMIN_ID:
        await update.message.reply_text("👑 Aap Owner hain!")
        return

    try:
        user_key = context.args[0].strip()
    except IndexError:
        await update.message.reply_text("⚠️ Key daalein: `/redeem YOUR_KEY`")
        return

    if user_key in KEYS_DB:
        key_data = KEYS_DB[user_key]
        if not key_data["multi"] and len(key_data["used_by"]) > 0:
            await update.message.reply_text("❌ Ye Key use ho chuki hai!")
            return
        if user_id in key_data["used_by"]:
            await update.message.reply_text("⚠️ Aap ise redeem kar chuke hain!")
            return

        days = key_data["days"]
        KEYS_DB[user_key]["used_by"].append(user_id)
        current_expiry = USERS_DB.get(user_id, datetime.now())
        if current_expiry < datetime.now():
            current_expiry = datetime.now()
        new_expiry = current_expiry + timedelta(days=days)
        USERS_DB[user_id] = new_expiry

        await update.message.reply_text(f"🎉 **KEY ACTIVATED!** ({days} Days)", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Galat ya Expired Key!")

async def process_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not is_user_active(user_id):
        await update.message.reply_text(f"⛔ Access Expired! Contact: {BOT_OWNER}")
        return

    url = update.message.text.strip()
    if not any(d in url for d in ["facebook.com", "fb.watch", "youtube.com", "youtu.be", "instagram.com"]):
        await update.message.reply_text("⚠️ Valid video link send karein.")
        return

    status_msg = await update.message.reply_text("⚡ Processing Video...")
    audio_file = f"audio_{update.message.message_id}.mp3"

    ydl_opts = {'format': 'bestaudio/best', 'outtmpl': f'audio_{update.message.message_id}', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '128'}], 'quiet': True}

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        await status_msg.edit_text("🎙️ Audio Extracted! Extracting text...")

        with open(audio_file, "rb") as file:
            response = requests.post("https://api.groq.com/openai/v1/audio/transcriptions", headers={"Authorization": f"Bearer {GROQ_API_KEY}"}, files={"file": (audio_file, file, "audio/mp3")}, data={"model": "whisper-large-v3"})

        if os.path.exists(audio_file):
            os.remove(audio_file)

        extracted_text = response.json().get("text", "").strip()
        if extracted_text:
            await status_msg.delete()
            await update.message.reply_text(f"🎬 **EXTRACTED LYRICS:**\n\n{extracted_text}", parse_mode="Markdown")
        else:
            await status_msg.edit_text("❌ No Speech Found!")
    except Exception as e:
        await status_msg.edit_text(f"❌ Error: `{str(e)}`")
        if os.path.exists(audio_file):
            os.remove(audio_file)

def main():
    threading.Thread(target=run_health_check_server, daemon=True).start()

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("revoke", revoke))
    app.add_handler(CommandHandler("redeem", redeem))
    app.add_handler(CallbackQueryHandler(admin_button_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_video))
    app.run_polling()

if __name__ == "__main__":
    main()
