# app.py
"""
File utama untuk menjalankan aplikasi Bot Keuangan Pribadi.

File ini menginisialisasi semua komponen aplikasi dan menjalankan server web.
"""

import logging
import asyncio
from telegram.ext import ApplicationBuilder

from app import app
from app.config import (
    TELEGRAM_TOKEN, PORT, HOST, WEBHOOK_URL,
    setup_logging, validate_environment,
    APP_NAME, APP_VERSION  # Import the constants
)
from app.database.sheets import initialize_gspread
from app.bot import setup_bot
from app.web.routes import set_bot, setup_webhook


async def initialize_bot():
    """Initialize the bot application asynchronously"""
    bot = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    await bot.initialize()
    setup_bot(bot)
    return bot

def main():
    """Fungsi utama untuk menjalankan aplikasi."""
    # Setup logging
    try:
        setup_logging()
        logging.info(f"✅ Memulai {APP_NAME} v{APP_VERSION}")
    except Exception as e:
        print(f"FATAL ERROR: Gagal mengatur logging: {e}")
        return False

    # Validasi variabel lingkungan
    try:
        if not validate_environment():
            logging.error("❌ Validasi variabel lingkungan gagal. Aplikasi dihentikan.")
            return False
        logging.info("✅ Validasi variabel lingkungan berhasil")
    except Exception as e:
        logging.error(f"❌ Error tak terduga saat validasi lingkungan: {e}")
        return False

    # Inisialisasi Google Sheets
    try:
        if not initialize_gspread():
            logging.error("❌ Inisialisasi Google Sheets gagal. Aplikasi dihentikan.")
            return False
        logging.info("✅ Koneksi Google Sheets berhasil")
    except Exception as e:
        logging.error(f"❌ Error tak terduga saat inisialisasi Google Sheets: {e}")
        return False

    # Inisialisasi bot Telegram
    bot = None
    try:
        # Use asyncio to run the async initialization function
        bot = asyncio.run(initialize_bot())
        logging.info("✅ Bot Telegram berhasil diinisialisasi")
    except Exception as e:
        logging.error(f"❌ Gagal menginisialisasi bot Telegram: {e}")
        return False

    # Inisialisasi aplikasi Flask
    try:
        # Gunakan app yang sudah diinisialisasi di level modul
        set_bot(bot)
        logging.info("✅ Aplikasi web berhasil diinisialisasi")
    except Exception as e:
        logging.error(f"❌ Gagal menginisialisasi aplikasi web: {e}")
        return False
    
    # Setup webhook
    try:
        if not setup_webhook(bot):
            logging.error("❌ Setup webhook gagal. Aplikasi dihentikan.")
            return False
        logging.info("✅ Webhook berhasil dikonfigurasi")
    except Exception as e:
        logging.error(f"❌ Error tak terduga saat setup webhook: {e}")
        return False
    
    # Jalankan server
    try:
        logging.info(f"✅ Server berjalan di {HOST}:{PORT}")
        app.run(host=HOST, port=PORT)
        return True
    except KeyboardInterrupt:
        logging.info("⚠️ Aplikasi dihentikan oleh pengguna")
        return True
    except Exception as e:
        logging.error(f"❌ Gagal menjalankan server: {e}")
        return False

if __name__ == "__main__":
    main()