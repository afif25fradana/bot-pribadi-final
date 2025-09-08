# app/config.py
"""
Konfigurasi untuk aplikasi Noxara Finance Bot.

Modul ini berisi semua konfigurasi dan variabel lingkungan yang diperlukan
untuk menjalankan aplikasi.
"""

import os
import logging
from dotenv import load_dotenv

# Muat variabel lingkungan dari file .env jika ada
load_dotenv()

# Konfigurasi Telegram
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')

# Konfigurasi Google Sheets
GSPREAD_CREDENTIALS = os.environ.get('GSPREAD_CREDENTIALS')
SPREADSHEET_NAME = os.environ.get('SPREADSHEET_NAME', 'Catatan Keuangan')

# Konfigurasi Keamanan
try:
    # Mendukung baik ALLOWED_USER_ID maupun ALLOWED_USER_IDS untuk kompatibilitas
    user_id_str = os.environ.get('ALLOWED_USER_ID') or os.environ.get('ALLOWED_USER_IDS', '').split(',')[0]
    ALLOWED_USER_ID = int(user_id_str) if user_id_str else None
except (TypeError, ValueError):
    ALLOWED_USER_ID = None

# Konfigurasi Server
PORT = int(os.environ.get("PORT", 5000))
HOST = os.environ.get("HOST", "0.0.0.0")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

# Konfigurasi Aplikasi
APP_NAME = "Noxara Finance Bot"
APP_VERSION = "2.0.0"

def setup_logging():
    """Mengkonfigurasi logging dengan format dan level yang tepat."""
    import os
    import sys
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Konfigurasi handler untuk konsol dengan encoding yang tepat
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Konfigurasi handler untuk file
    file_handler = logging.FileHandler(os.path.join(log_dir, 'bot.log'), encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # Format yang sama untuk kedua handler
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # Konfigurasi root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = []  # Hapus handler yang ada
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Kurangi kebisingan dari library eksternal
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

def validate_environment():
    """Validasi variabel lingkungan yang diperlukan."""
    missing_vars = []
    if not TELEGRAM_TOKEN:
        missing_vars.append("TELEGRAM_TOKEN")
    if not ALLOWED_USER_ID:
        missing_vars.append("ALLOWED_USER_ID/ALLOWED_USER_IDS")
    if not GSPREAD_CREDENTIALS:
        missing_vars.append("GSPREAD_CREDENTIALS")
    
    # Periksa WEBHOOK_URL jika bukan dalam mode development
    import sys
    is_development = 'run.py' in sys.argv[0]
    if not is_development and not WEBHOOK_URL:
        missing_vars.append("WEBHOOK_URL")
        logging.warning("⚠️ WEBHOOK_URL tidak ditemukan. Ini diperlukan untuk deployment.")
    
    if missing_vars:
        logging.error(f"❌ Variabel lingkungan yang diperlukan berikut tidak ada: {', '.join(missing_vars)}")
        logging.error("❌ Harap atur semua variabel lingkungan yang diperlukan sebelum memulai bot")
        return False
    
    return True