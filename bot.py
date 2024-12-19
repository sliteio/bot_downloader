import asyncio
import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from yt_dlp import YoutubeDL
import re

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

def is_valid_url(url: str, platform: str) -> bool:
    if platform == "tiktok":
        return bool(re.match(r"https://www\.tiktok\.com/", url))
    elif platform == "instagram":
        return bool(re.match(r"https://www\.instagram\.com/", url))
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("TikTok", callback_data="tiktok"), InlineKeyboardButton("Instagram", callback_data="instagram")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Pilih platform untuk mengunduh video:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["platform"] = query.data
    await query.edit_message_text("Kirimkan URL video yang ingin diunduh.")

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    platform = context.user_data.get("platform")
    url = update.message.text

    if platform not in ["tiktok", "instagram"]:
        await update.message.reply_text("Pilih platform terlebih dahulu dengan perintah /start.")
        return

    if not is_valid_url(url, platform):
        await update.message.reply_text(f"URL tidak valid untuk platform {platform.capitalize()}. Pastikan Anda mengirimkan URL yang benar.")
        return

    await update.message.reply_text("Mengunduh video...")

    user_id = update.message.from_user.id
    video_filename = f'{platform}_video_{user_id}.mp4'

    ydl_opts = {
        'outtmpl': video_filename,
        'format': 'bestvideo[height<=1080]+bestaudio/best',
        'noplaylist': True,
        'socket_timeout': 2000,
        'merge_output_format': 'mp4',
        'max_filesize': 50000000,
    }

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: download_video_sync(url, ydl_opts))

        if not os.path.exists(video_filename):
            await update.message.reply_text("Gagal mengunduh video, file tidak ditemukan.")
            return

        with open(video_filename, 'rb') as video_file:
            await update.message.reply_video(video=video_file)

        os.remove(video_filename)

    except Exception as e:
        if "timed out" in str(e).lower():
            await update.message.reply_text("Tunggu sebentar, video memakan waktu yang lama untuk diunduh.")
        else:
            await update.message.reply_text(f"Gagal mengunduh video: {e}")
        if os.path.exists(video_filename):
            os.remove(video_filename)

def download_video_sync(url, ydl_opts):
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))

    print("Bot berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()

