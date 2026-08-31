import os
import requests
import yt_dlp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Namaste! Mujhe koi bhi Facebook video link bhejein, main uska text/lyrics nikaal kar dunga.")

async def process_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if "facebook.com" not in url and "fb.watch" not in url:
        await update.message.reply_text("Kripya sahi Facebook video link bhejein.")
        return

    status_msg = await update.message.reply_text("Video se lyrics/text nikaala ja raha hai... Kripya intezar karein.")
    audio_file = f"audio_{update.message.message_id}.mp3"

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'audio_{update.message.message_id}',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '128',
        }],
        'quiet': True
    }

    try:
        # Video se audio download
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        await status_msg.edit_text("Audio mil gaya hai! AI ab text/lyrics likh raha hai...")

        # Groq Whisper API Call
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
            if len(extracted_text) > 4000:
                for i in range(0, len(extracted_text), 4000):
                    await update.message.reply_text(extracted_text[i:i+4000])
            else:
                await update.message.reply_text(f"📝 **Video me bola gaya Text / Lyrics:**\n\n{extracted_text}")
        else:
            await update.message.reply_text("Video me koi clear aawaz ya lyrics nahi mili.")

    except Exception as e:
        await update.message.reply_text(f"Galti aayi: {str(e)}")
        if os.path.exists(audio_file):
            os.remove(audio_file)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_video))
    app.run_polling()

if __name__ == "__main__":
    main()