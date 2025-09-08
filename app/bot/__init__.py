# app/bot/__init__.py
"""
Modul bot Telegram untuk aplikasi Bot Keuangan Pribadi.

Modul ini menangani inisialisasi bot Telegram, pendaftaran handler,
dan interaksi dengan API Telegram.
"""

import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

from app.bot.handlers import start, catat_transaksi, laporan, compare_report, button_handler

def setup_bot(bot: Application):
    """
    Mengatur bot Telegram dengan handler yang diperlukan.
    
    Args:
        bot (Application): Instance aplikasi bot Telegram.
    """
    try:
        # Daftarkan handler perintah
        bot.add_handler(CommandHandler("start", start))
        bot.add_handler(CommandHandler("masuk", catat_transaksi))
        bot.add_handler(CommandHandler("keluar", catat_transaksi))
        bot.add_handler(CommandHandler("laporan", laporan))
        bot.add_handler(CommandHandler("compare", compare_report))
        
        # Daftarkan handler callback query untuk tombol
        bot.add_handler(CallbackQueryHandler(button_handler))
        
        # Tambahkan error handler
        bot.add_error_handler(error_handler)
        
        logging.info("✅ Handler bot berhasil didaftarkan")
    except Exception as e:
        logging.error(f"❌ Gagal mendaftarkan handler bot: {e}")
        raise

def error_handler(update, context):
    """
    Menangani error yang terjadi saat bot berjalan.
    
    Args:
        update: Update dari Telegram.
        context: Context dari handler.
    """
    logging.error(f"Error saat memproses update: {context.error}")
    
    # Kirim pesan error ke pengguna jika memungkinkan
    if update and update.effective_message:
        update.effective_message.reply_text(
            "❌ Terjadi kesalahan saat memproses perintah Anda. Silakan coba lagi nanti."
        )