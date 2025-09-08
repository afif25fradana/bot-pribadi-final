# app.py
"""
File utama untuk menjalankan aplikasi Bot Keuangan Pribadi.

File ini menginisialisasi semua komponen aplikasi dan menjalankan server web.
"""

import logging
from flask import Flask
from telegram.ext import ApplicationBuilder

from app.config import (
    TELEGRAM_TOKEN, PORT, HOST, WEBHOOK_URL, 
    setup_logging, validate_environment
)
from app.database.sheets import initialize_gspread
from app.bot import setup_bot
from app.web.routes import init_web, setup_webhook

# Inisialisasi Flask app di level modul untuk diakses oleh WSGI server
app = Flask(__name__)

def main():
    """Fungsi utama untuk menjalankan aplikasi."""
    # Setup logging
    setup_logging()
    
    # Validasi variabel lingkungan
    if not validate_environment():
        logging.error("❌ Validasi variabel lingkungan gagal. Aplikasi dihentikan.")
        return
    
    # Inisialisasi Google Sheets
    if not initialize_gspread():
        logging.error("❌ Inisialisasi Google Sheets gagal. Aplikasi dihentikan.")
        return
    
    # Inisialisasi bot Telegram
    try:
        bot = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        setup_bot(bot)
        logging.info("✅ Bot Telegram berhasil diinisialisasi")
    except Exception as e:
        logging.error(f"❌ Gagal menginisialisasi bot Telegram: {e}")
        return
    
    # Inisialisasi aplikasi Flask
    try:
        # Gunakan app yang sudah diinisialisasi di level modul
        init_web(app, bot)
        logging.info("✅ Aplikasi web berhasil diinisialisasi")
    except Exception as e:
        logging.error(f"❌ Gagal menginisialisasi aplikasi web: {e}")
        return
    
    # Setup webhook
    if not setup_webhook(bot):
        logging.error("❌ Setup webhook gagal. Aplikasi dihentikan.")
        return
    
    # Jalankan server
    try:
        logging.info(f"✅ Server berjalan di {HOST}:{PORT}")
        app.run(host=HOST, port=PORT)
    except Exception as e:
        logging.error(f"❌ Gagal menjalankan server: {e}")

if __name__ == "__main__":
    main()