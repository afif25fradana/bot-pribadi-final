# app/web/routes.py
"""
Modul untuk menangani endpoint web dan webhook.

Modul ini berisi fungsi-fungsi untuk menangani endpoint web dan webhook Telegram.
"""

import logging
from flask import request, jsonify
from telegram import Update
from telegram.ext import Application
from app.config import WEBHOOK_URL, PORT, HOST
from app import app

# Variabel global untuk menyimpan bot Telegram
_bot = None

def set_bot(bot: Application):
    global _bot
    _bot = bot

@app.route('/', methods=['GET'])
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

@app.route('/health', methods=['GET'])
def health():
    return 'OK', 200



@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Endpoint untuk webhook Telegram.
    
    Returns:
        str: Respons kosong dengan status 200.
    """
    global _bot
    
    if request.method == 'POST':
        if _bot is None:
            logging.error("❌ Bot belum diinisialisasi saat menerima webhook")
            return 'Bot not initialized', 500
            
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                logging.error("❌ Webhook menerima data kosong atau tidak valid")
                return 'Invalid data', 400
                
            update = Update.de_json(json_data, _bot.bot)
            if update is None:
                logging.error("❌ Gagal mem-parsing update dari Telegram")
                return 'Invalid update format', 400
                
            # Create a task for the coroutine instead of calling it directly
            import asyncio
            asyncio.create_task(_bot.process_update(update))
            logging.debug("✅ Webhook berhasil diproses")
        except ValueError as e:
            logging.error(f"❌ Error format JSON saat memproses webhook: {e}")
            return 'Invalid JSON', 400
        except Exception as e:
            logging.error(f"❌ Error saat memproses webhook: {e}")
            return 'Internal error', 500
    
    return ''



def setup_webhook(bot: Application):
    """
    Mengatur webhook untuk bot Telegram.
    
    Args:
        bot (Application): Aplikasi bot Telegram.
        
    Returns:
        bool: True jika berhasil, False jika gagal.
    """
    # Validasi parameter bot
    if bot is None:
        logging.error("❌ Parameter bot tidak valid untuk setup_webhook")
        return False
        
    # Periksa apakah WEBHOOK_URL tersedia
    if not WEBHOOK_URL:
        # Jika tidak ada WEBHOOK_URL, mungkin sedang dalam mode development
        # Jadi kita tidak perlu mengatur webhook
        logging.warning("⚠️ WEBHOOK_URL tidak tersedia. Webhook tidak diatur.")
        logging.info("ℹ️ Jika Anda menjalankan dalam mode development, gunakan run.py untuk mode polling.")
        # Kembalikan True agar aplikasi tetap berjalan
        return True
    
    # Validasi format webhook URL
    if not WEBHOOK_URL.startswith('https://'):
        logging.error(f"❌ WEBHOOK_URL harus menggunakan HTTPS: {WEBHOOK_URL}")
        return False
        
    try:
        # Hapus webhook yang ada terlebih dahulu untuk menghindari konflik
        bot.bot.delete_webhook()
        logging.info("✅ Webhook lama dihapus")
        
        # Atur webhook baru
        webhook_info = bot.bot.set_webhook(WEBHOOK_URL)
        
        # Verifikasi bahwa webhook berhasil diatur
        if webhook_info:
            logging.info(f"✅ Webhook berhasil diatur ke {WEBHOOK_URL}")
            return True
        else:
            logging.error("❌ Telegram API mengembalikan respons kosong saat mengatur webhook")
            return False
    except Exception as e:
        logging.error(f"❌ Gagal mengatur webhook: {e}")
        return False