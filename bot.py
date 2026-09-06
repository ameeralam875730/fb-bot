import os
import requests
import random
import string
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Keep-Alive Server for Render
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot Active")

def run_health_check():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

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
        return datetime.now() < USERS_DB[user_id]
    return False

def download_audio_multi_api(video_url, output_path):
    """ YouTube aur Facebook ke Cloud Blocking bypass karne ke multi-engine endpoints """
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    # Engine 1: Rapid Multi Downloader API
    try:
        api_res = requests.post("https://co.wuk.sh/api/json", json={
            "url": video_url,
            "downloadMode": "audio",
            "audioFormat": "mp3"
        }, headers={"Accept": "application/json", "Content-Type": "application/json"}, timeout=15)
        
        if api_res.status_code == 200:
            audio_link = api_res.json().get("url")
            if audio_link:
                with requests.get(audio_link, headers=headers, stream=True, timeout=30) as r:
                    r.raise_for_status()
                    with open(output_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                if os.path.exists(output_path) and os.path.getsize(output_path) > 5000:
                    return True
    except Exception:
        pass

    # Engine 2: Fallback Audio Stream Fetcher
    try:
        api_res2 = requests.get(f"https://api.vyt.workers.dev/?url={video_url}", headers=headers, timeout=15)
        if api_res2.status_code == 200 and "url" in api_res2.json():
            dl_url = api_res2.json()["url"]
            with requests.get(dl_url, headers=headers, stream=True, timeout=30) as r:
                with open(output_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            if os.path.exists(output_path) and os.path.getsize(output_path) > 5000:
                return True
    except Exception:
        pass

    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    welcome_msg = f"✨ **Welcome to {BOT_NAME}!** ✨\n\nVideo link bhej kar voice/text extract karein."
    
    if user_id == ADMIN_ID or is_user_active(user_id):
        keyboard = [[InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/AmeerBro786")]]
        await update.message.reply_text(welcome_msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        restricted_msg = f"⛔ **ACCESS RESTRICTED!**\nKey ke liye admin se contact karein: {BOT_OWNER}\n\n`/redeem YOUR_KEY`"
        await update.message.reply_text(restricted_msg, parse_mode="Markdown")

async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    try:
        user_key = context.args[0].strip()
    except IndexError:
        await update.message.reply_text("⚠️ Key format: `/redeem YOUR_KEY`")
        return

    if user_key in KEYS_DB:
        USERS_DB[user_id] = datetime.now() + timedelta(days=KEYS_DB[user_key]["days"])
        await update.message.reply_text("🎉 **VIP ACCESS ACTIVATED!**")
    else:
        await update.message.reply_text("❌ Galat Key!")

async def process_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not is_user_active(user_id):
        await update.message.reply_text(f"⛔ Access Expired! Contact: {BOT_OWNER}")
        return

    raw_url = update.message.text.strip()
    status_msg = await update.message.reply_text("⚡ Cloud Proxies dwara Audio Fetch ho raha hai...")
    audio_file = f"audio_{update.message.message_id}.mp3"

    # API Downloading
    success = download_audio_multi_api(raw_url, audio_file)

    if not success or not os.path.exists(audio_file):
        await status_msg.edit_text("❌ Cloud IP Blocked: Is link ko direct stream nahi kiya ja saka. Dusri video link bhejein.")
        return

    await status_msg.edit_text("🎙️ Audio Stream Received! AI Text Extract kar raha hai...")

    try:
        with open(audio_file, "rb") as file:
            groq_res = requests.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                files={"file": (audio_file, file, "audio/mp3")},
                data={"model": "whisper-large-v3"}
            )

        if os.path.exists(audio_file):
            os.remove(audio_file)

        extracted_text = groq_res.json().get("text", "").strip()

        if extracted_text:
            await status_msg.delete()
            await update.message.reply_text(f"🎬 **EXTRACTED LYRICS / SPEECH:**\n\n{extracted_text}", parse_mode="Markdown")
        else:
            await status_msg.edit_text("❌ No Speech Found in video!")

    except Exception as e:
        await status_msg.edit_text(f"❌ Error: `{str(e)}`")
        if os.path.exists(audio_file):
            os.remove(audio_file)

def main():
    threading.Thread(target=run_health_check, daemon=True).start()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("redeem", redeem))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_video))
    app.run_polling()

if __name__ == "__main__":
    main()
