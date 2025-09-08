#!/usr/bin/env python
# run.py
"""
File untuk menjalankan aplikasi secara lokal dengan mode polling.

File ini menjalankan bot dalam mode polling tanpa memerlukan webhook,
cocok untuk pengembangan dan pengujian lokal.
"""

import logging
from telegram.ext import ApplicationBuilder

from app.config import (
    TELEGRAM_TOKEN, setup_logging, validate_environment
)
from app.database.sheets import initialize_gspread
from app.bot import setup_bot

def run_local():
    """Menjalankan bot dalam mode polling untuk pengembangan lokal."""
    # Setup logging
    try:
        setup_logging()
        logging.info("🚀 Menjalankan bot dalam mode polling (development)")
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
    
    # Inisialisasi dan jalankan bot dalam mode polling
    try:
        bot = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        setup_bot(bot)
        logging.info("✅ Bot Telegram berhasil diinisialisasi")
        logging.info("🔄 Memulai polling... Tekan Ctrl+C untuk berhenti")
        bot.run_polling()
        return True
    except KeyboardInterrupt:
        logging.info("⚠️ Bot dihentikan oleh pengguna")
        return True
    except Exception as e:
        logging.error(f"❌ Gagal menjalankan bot: {e}")
        return False

if __name__ == "__main__":
    import sys
    success = run_local()
    if not success:
        logging.error("❌ Aplikasi dihentikan karena terjadi kesalahan")
        sys.exit(1)
    sys.exit(0)