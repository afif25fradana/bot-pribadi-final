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
    setup_logging()
    logging.info("🚀 Menjalankan bot dalam mode polling (development)")
    
    # Validasi variabel lingkungan
    if not validate_environment():
        logging.error("❌ Validasi variabel lingkungan gagal. Aplikasi dihentikan.")
        return
    
    # Inisialisasi Google Sheets
    if not initialize_gspread():
        logging.error("❌ Inisialisasi Google Sheets gagal. Aplikasi dihentikan.")
        return
    
    # Inisialisasi dan jalankan bot dalam mode polling
    try:
        bot = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        setup_bot(bot)
        logging.info("✅ Bot Telegram berhasil diinisialisasi")
        logging.info("🔄 Memulai polling... Tekan Ctrl+C untuk berhenti")
        bot.run_polling()
    except Exception as e:
        logging.error(f"❌ Gagal menjalankan bot: {e}")

if __name__ == "__main__":
    run_local()