# app/web/routes.py
"""
Modul untuk menangani endpoint web dan webhook.

Modul ini berisi fungsi-fungsi untuk menangani endpoint web dan webhook Telegram.
"""

import logging
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import Application
from app.config import WEBHOOK_URL, PORT, HOST

# Variabel global untuk menyimpan aplikasi Flask dan bot
_app = None
_bot = None

def init_web(app: Flask, bot: Application):
    """
    Menginisialisasi aplikasi web dengan bot Telegram.
    
    Args:
        app (Flask): Aplikasi Flask.
        bot (Application): Aplikasi bot Telegram.
    """
    global _app, _bot
    _app = app
    _bot = bot
    
    # Daftarkan endpoint
    app.route('/', methods=['GET'])(index)
    app.route('/webhook', methods=['POST'])(webhook)
    app.route('/health', methods=['GET'])(health)

def index():
    """
    Endpoint untuk halaman utama.
    
    Returns:
        dict: Respons JSON.
    """
    return jsonify({
        'status': 'online',
        'message': 'Bot Keuangan Pribadi aktif dan berjalan.'
    })

def webhook():
    """
    Endpoint untuk webhook Telegram.
    
    Returns:
        str: Respons kosong dengan status 200.
    """
    global _bot
    
    if request.method == 'POST':
        try:
            update = Update.de_json(request.get_json(force=True), _bot.bot)
            _bot.process_update(update)
        except Exception as e:
            logging.error(f"❌ Error saat memproses webhook: {e}")
    
    return ''

def health():
    """
    Endpoint untuk health check.
    
    Returns:
        dict: Respons JSON dengan status kesehatan.
    """
    return jsonify({
        'status': 'healthy',
        'webhook_url': WEBHOOK_URL,
        'port': PORT,
        'host': HOST
    })

def setup_webhook(bot: Application):
    """
    Mengatur webhook untuk bot Telegram.
    
    Args:
        bot (Application): Aplikasi bot Telegram.
        
    Returns:
        bool: True jika berhasil, False jika gagal.
    """
    # Periksa apakah WEBHOOK_URL tersedia
    if not WEBHOOK_URL:
        # Jika tidak ada WEBHOOK_URL, mungkin sedang dalam mode development
        # Jadi kita tidak perlu mengatur webhook
        logging.warning("⚠️ WEBHOOK_URL tidak tersedia. Webhook tidak diatur.")
        logging.info("ℹ️ Jika Anda menjalankan dalam mode development, gunakan run.py untuk mode polling.")
        # Kembalikan True agar aplikasi tetap berjalan
        return True
        
    try:
        bot.bot.set_webhook(WEBHOOK_URL)
        logging.info(f"✅ Webhook berhasil diatur ke {WEBHOOK_URL}")
        return True
    except Exception as e:
        logging.error(f"❌ Gagal mengatur webhook: {e}")
        return False