import os
import requests
import yt_dlp
import random
import string
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# CONFIGURATION
BOT_TOKEN = os.getenv("BOT_TOKEN", "8811073395:AAHSWle6K63IwF4f2lvotJHCyQyZwYLasrY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")
ADMIN_ID = 1523935298  # Ameer Bro's Telegram ID

BOT_NAME = "MediaLyrics AI Pro"
BOT_OWNER = "@AmeerBro786"

# Database Storage
KEYS_DB = {}   # Format: {"KEY_CODE": {"days": 30, "multi": False, "used_by": []}}
USERS_DB = {}  # Format: {user_id: expiry_datetime}

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
            f"⛔ **ACCESS RESTRICTED!**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Aap is bot ko bina **Activation Key** ke use nahi kar sakte.\n\n"
            f"🔑 **Key prapt karne ke liye Admin se contact karein:**\n"
            f"👉 **Admin Contact:** {BOT_OWNER}\n\n"
            f"--------------------------------------\n"
            f"Aapke paas key hai toh redeem karein:\n"
            f"`/redeem YOUR_KEY_HERE`"
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
            [InlineKeyboardButton("👤 Single User Key (1 Person)", callback_data="menu_single")],
            [InlineKeyboardButton("🌐 Multi User Key (Unlimited Log)", callback_data="menu_multi")]
        ]
        await query.message.reply_text(
            "🔑 **Kis type ki key generate karni hai?**",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "menu_single":
        keyboard = [
            [
                InlineKeyboardButton("7 Days", callback_data="gen_s_7"),
                InlineKeyboardButton("30 Days", callback_data="gen_s_30"),
                InlineKeyboardButton("365 Days", callback_data="gen_s_365")
            ]
        ]
        await query.message.reply_text("👤 **Single User Key Validity Chunein:**", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "menu_multi":
        keyboard = [
            [
                InlineKeyboardButton("7 Days", callback_data="gen_m_7"),
                InlineKeyboardButton("30 Days", callback_data="gen_m_30"),
                InlineKeyboardButton("365 Days", callback_data="gen_m_365")
            ]
        ]
        await query.message.reply_text("🌐 **Multi User (Unlimited) Key Validity Chunein:**", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("gen_s_") or query.data.startswith("gen_m_"):
        is_multi = query.data.startswith("gen_m_")
        days = int(query.data.split("_")[2])
        
        prefix = "MULTI-" if is_multi else "AMEER-"
        new_key = generate_random_key(prefix=prefix)
        KEYS_DB[new_key] = {"days": days, "multi": is_multi, "used_by": []}

        type_str = "MULTI-USER (UNLIMITED USERS)" if is_multi else "SINGLE USER (1 PERSON ONLY)"
        note_str = "Yeh key koi bhi kitne bhi log use kar sakte hain." if is_multi else "Yeh key ek hi user ke liye hai. Single use only."

        msg = (
            f"🎉 **VIP ACCESS ACTIVATION KEY** 🎉\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔑 **Your Key:** `{new_key}`\n"
            f"⏳ **Validity:** {days} Days\n"
            f"👥 **Type:** {type_str}\n\n"
            f"📋 **KAISE USE KAREIN (GUIDELINES):**\n"
            f"1. Sabse pehle bot par ja kar `/start` dabayein.\n"
            f"2. Niche di gayi command ko copy karke bot me bhejhein:\n\n"
            f"`/redeem {new_key}`\n\n"
            f"3. Key activate hote hi aap {days} din tak kisi bhi FB, YT, ya Insta video se lyrics extract kar sakte hain.\n\n"
            f"⚠️ **Note:** {note_str}\n\n"
            f"👨‍💻 **Owner:** {BOT_OWNER}"
        )
        await query.message.reply_text(msg, parse_mode="Markdown")

# Single User Key Command
async def genkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Sirf Admin (@AmeerBro786) hi keys generate kar sakta hai.")
        return

    try:
        days = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ **Format:** `/genkey <days>`\nExample: `/genkey 30`")
        return

    new_key = generate_random_key(prefix="AMEER-")
    KEYS_DB[new_key] = {"days": days, "multi": False, "used_by": []}

    msg = (
        f"🎉 **VIP ACCESS ACTIVATION KEY** 🎉\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔑 **Your Key:** `{new_key}`\n"
        f"⏳ **Validity:** {days} Days\n"
        f"👥 **Type:** SINGLE USER\n\n"
        f"📋 **KAISE USE KAREIN:**\n"
        f"Bot me bhejein: `/redeem {new_key}`\n\n"
        f"👨‍💻 **Owner:** {BOT_OWNER}"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

# Multi User / Unlimited Key Command
async def genmultikey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Sirf Admin (@AmeerBro786) hi keys generate kar sakta hai.")
        return

    try:
        days = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ **Format:** `/genmultikey <days>`\nExample: `/genmultikey 30`")
        return

    new_key = generate_random_key(prefix="MULTI-")
    KEYS_DB[new_key] = {"days": days, "multi": True, "used_by": []}

    msg = (
        f"🎉 **GLOBAL UNLIMITED ACTIVATION KEY** 🎉\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔑 **Your Key:** `{new_key}`\n"
        f"⏳ **Validity:** {days} Days (Per User)\n"
        f"🌐 **Type:** MULTI-USER (UNLIMITED)\n\n"
        f"📋 **KAISE USE KAREIN:**\n"
        f"Is command ko sabhi dosto/groups me share karein:\n\n"
        f"`/redeem {new_key}`\n\n"
        f"👨‍💻 **Owner:** {BOT_OWNER}"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    if user_id == ADMIN_ID:
        await update.message.reply_text("👑 Aap Owner hain, aapko key redeem karne ki koi zaroorat nahi hai!")
        return

    try:
        user_key = context.args[0].strip()
    except IndexError:
        await update.message.reply_text("⚠️ Kripya key daalein!\nExample: `/redeem AMEER-XXXXXXXX`")
        return

    if user_key in KEYS_DB:
        key_data = KEYS_DB[user_key]
        
        # Single User Check
        if not key_data["multi"] and len(key_data["used_by"]) > 0:
            await update.message.reply_text("❌ Ye Single-User Key pehle hi koi aur redeem kar chuka hai!")
            return
            
        # Already Redeemed Check
        if user_id in key_data["used_by"]:
            await update.message.reply_text("⚠️ Aap pehle hi is key ko redeem kar chuke hain!")
            return

        days = key_data["days"]
        KEYS_DB[user_key]["used_by"].append(user_id)
        
        current_expiry = USERS_DB.get(user_id, datetime.now())
        if current_expiry < datetime.now():
            current_expiry = datetime.now()
            
        new_expiry = current_expiry + timedelta(days=days)
        USERS_DB[user_id] = new_expiry

        exp_str = new_expiry.strftime("%d-%b-%Y")
        await update.message.reply_text(
            f"🎉 **KEY ACTIVATED SUCCESSFULLY!**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"• **Access Duration:** {days} Days\n"
            f"• **Expiry Date:** {exp_str}\n\n"
            f"🚀 Ab aap koi bhi Facebook, YouTube ya Instagram video link bhej sakte hain!",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("❌ Galat Key! Sahi key lene ke liye Admin @AmeerBro786 se sampark karein.")

async def process_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if not is_user_active(user_id):
        restricted_msg = (
            f"⛔ **ACCESS DENIED!**\n\n"
            f"Aapka access expire ho gaya hai ya aapke paas valid key nahi hai.\n"
            f"Key khareedne ke liye Admin se baat karein: {BOT_OWNER}"
        )
        keyboard = [[InlineKeyboardButton("💬 Contact Admin", url="https://t.me/AmeerBro786")]]
        await update.message.reply_text(restricted_msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    url = update.message.text.strip()
    valid_platforms = ["facebook.com", "fb.watch", "youtube.com", "youtu.be", "instagram.com"]
    if not any(domain in url for domain in valid_platforms):
        await update.message.reply_text("⚠️ **Invalid Link!**\nKripya Facebook, YouTube, ya Instagram ka valid video link bhejein.")
        return

    status_msg = await update.message.reply_text("⚡ **[1/3] Video Processing Started...**\nAudio extract kiya ja raha hai...")
    audio_file = f"audio_{update.message.message_id}.mp3"

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'audio_{update.message.message_id}',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '128',
        }],
        'quiet': True,
        'no_warnings': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        await status_msg.edit_text("🎙️ **[2/3] Audio Extracted!**\nAI Whisper Engine lyrics generate kar raha hai...")

        with open(audio_file, "rb") as file:
            response = requests.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                files={"file": (audio_file, file, "audio/mp3")},
                data={"model": "whisper-large-v3"}
            )

        if os.path.exists(audio_file):
            os.remove(audio_file)

        result = response.json()
        extracted_text = result.get("text", "").strip()

        if extracted_text:
            await status_msg.delete()
            
            header = f"🎬 **EXTRACTED LYRICS / SPEECH**\n"
            header += f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            footer = f"\n\n━━━━━━━━━━━━━━━━━━━━━━\n"
            footer += f"🤖 **Generated by:** {BOT_NAME}\n"
            footer += f"👑 **Owner:** {BOT_OWNER}"

            full_response = header + extracted_text + footer

            keyboard = [[InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/AmeerBro786")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            if len(full_response) > 4000:
                for i in range(0, len(extracted_text), 3500):
                    part = extracted_text[i:i+3500]
                    await update.message.reply_text(f"📝 **Part:**\n\n{part}")
                await update.message.reply_text(footer, reply_markup=reply_markup)
            else:
                await update.message.reply_text(full_response, parse_mode="Markdown", reply_markup=reply_markup)
        else:
            await status_msg.edit_text("❌ **No Speech Found!**\nIs video me koi clear lyrics ya voice over nahi mila.")

    except Exception as e:
        await status_msg.edit_text(f"❌ **Error Occurred:**\n`{str(e)}`")
        if os.path.exists(audio_file):
            os.remove(audio_file)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("genkey", genkey))
    app.add_handler(CommandHandler("genmultikey", genmultikey))
    app.add_handler(CommandHandler("redeem", redeem))
    app.add_handler(CallbackQueryHandler(admin_button_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_video))
    app.run_polling()

if __name__ == "__main__":
    main()
