# tests/health_check.py
"""
Skrip untuk memeriksa kesehatan aplikasi.

Skrip ini memeriksa konfigurasi lingkungan, koneksi ke Google Sheets,
dan koneksi ke Telegram Bot API.
"""

import os
import json
import logging
import requests
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
import gspread
from telegram import Bot

# Konfigurasi logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Muat variabel lingkungan dari .env
load_dotenv()

def print_header(title):
    """
    Mencetak header untuk bagian pemeriksaan.
    
    Args:
        title (str): Judul bagian.
    """
    print("\n" + "=" * 50)
    print(f" {title} ".center(50, "="))
    print("=" * 50)

def check_environment_variables():
    """
    Memeriksa variabel lingkungan yang diperlukan.
    
    Returns:
        bool: True jika semua variabel wajib ada, False jika tidak.
    """
    print_header("PEMERIKSAAN VARIABEL LINGKUNGAN")
    
    # Variabel wajib
    required_vars = [
        "TELEGRAM_TOKEN",
        "GSPREAD_CREDENTIALS",
        "SPREADSHEET_ID",
        "ALLOWED_USER_IDS",
        "WEBHOOK_URL"
    ]
    
    # Variabel opsional dengan nilai default
    optional_vars = {
        "PORT": "8443",
        "HOST": "0.0.0.0",
        "LOG_LEVEL": "INFO"
    }
    
    all_required_present = True
    
    # Periksa variabel wajib
    print("\n📋 Variabel Wajib:")
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask nilai sensitif
            if var in ["TELEGRAM_TOKEN", "GSPREAD_CREDENTIALS"]:
                masked_value = value[:5] + "*" * (len(value) - 10) + value[-5:] if len(value) > 10 else "*" * len(value)
                print(f"✅ {var}: {masked_value}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: Tidak ditemukan")
            all_required_present = False
    
    # Periksa variabel opsional
    print("\n📋 Variabel Opsional:")
    for var, default in optional_vars.items():
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"ℹ️ {var}: Menggunakan nilai default ({default})")
    
    return all_required_present

def check_google_sheets_connection():
    """
    Memeriksa koneksi ke Google Sheets.
    
    Returns:
        bool: True jika koneksi berhasil, False jika gagal.
    """
    print_header("PEMERIKSAAN KONEKSI GOOGLE SHEETS")
    
    # Ambil kredensial dari variabel lingkungan
    creds_json = os.getenv("GSPREAD_CREDENTIALS")
    spreadsheet_id = os.getenv("SPREADSHEET_ID")
    
    if not creds_json or not spreadsheet_id:
        print("❌ Kredensial atau ID spreadsheet tidak ditemukan")
        return False
    
    try:
        # Parse kredensial JSON
        try:
            credentials_info = json.loads(creds_json)
            print("✅ Format JSON kredensial valid")
        except json.JSONDecodeError as e:
            print(f"❌ Format JSON kredensial tidak valid: {e}")
            return False
        
        # Buat objek kredensial
        try:
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            credentials = Credentials.from_service_account_info(credentials_info, scopes=scopes)
            client = gspread.authorize(credentials)
            print("✅ Otorisasi kredensial berhasil")
        except Exception as e:
            print(f"❌ Gagal mengotorisasi kredensial: {e}")
            return False
        
        # Buka spreadsheet
        try:
            spreadsheet = client.open_by_key(spreadsheet_id)
            print(f"✅ Berhasil membuka spreadsheet: {spreadsheet.title}")
            
            # Periksa worksheet
            try:
                worksheet = spreadsheet.worksheet("Transaksi")
                rows = worksheet.row_count
                cols = worksheet.col_count
                print(f"✅ Worksheet 'Transaksi' ditemukan ({rows} baris x {cols} kolom)")
            except gspread.exceptions.WorksheetNotFound:
                print("❌ Worksheet 'Transaksi' tidak ditemukan")
                return False
                
            return True
            
        except gspread.exceptions.SpreadsheetNotFound:
            print(f"❌ Spreadsheet dengan ID {spreadsheet_id} tidak ditemukan")
            return False
        except gspread.exceptions.APIError as e:
            print(f"❌ API Error: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Kesalahan tidak terduga: {e}")
        return False

def check_telegram_connection():
    """
    Memeriksa koneksi ke Telegram Bot API.
    
    Returns:
        bool: True jika koneksi berhasil, False jika gagal.
    """
    print_header("PEMERIKSAAN KONEKSI TELEGRAM")
    
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        print("❌ Token Telegram tidak ditemukan")
        return False
    
    try:
        # Buat instance bot
        bot = Bot(token=token)
        
        # Dapatkan info bot
        bot_info = bot.get_me()
        print(f"✅ Berhasil terhubung ke bot: @{bot_info.username} (ID: {bot_info.id})")
        
        # Periksa webhook
        webhook_url = os.getenv("WEBHOOK_URL")
        if webhook_url:
            webhook_info = bot.get_webhook_info()
            current_webhook = webhook_info.url
            
            if current_webhook:
                print(f"ℹ️ Webhook saat ini: {current_webhook}")
                if current_webhook != webhook_url:
                    print(f"⚠️ Webhook berbeda dengan konfigurasi: {webhook_url}")
            else:
                print("ℹ️ Webhook belum diatur")
        
        return True
        
    except Exception as e:
        print(f"❌ Gagal terhubung ke Telegram: {e}")
        return False

def check_webhook_endpoint():
    """
    Memeriksa endpoint webhook.
    
    Returns:
        bool: True jika endpoint dapat diakses, False jika tidak.
    """
    print_header("PEMERIKSAAN ENDPOINT WEBHOOK")
    
    webhook_url = os.getenv("WEBHOOK_URL")
    if not webhook_url:
        print("❌ URL webhook tidak ditemukan")
        return False
    
    try:
        # Coba akses endpoint webhook
        response = requests.get(webhook_url.replace("/webhook", "/health"))
        
        if response.status_code == 200:
            print(f"✅ Endpoint health check dapat diakses (status: {response.status_code})")
            try:
                data = response.json()
                print(f"ℹ️ Respons: {data}")
            except:
                print("⚠️ Respons bukan format JSON")
            return True
        else:
            print(f"❌ Endpoint tidak dapat diakses (status: {response.status_code})")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Gagal mengakses endpoint: {e}")
        return False

def main():
    """
    Fungsi utama untuk menjalankan pemeriksaan kesehatan.
    """
    print("\n🔍 PEMERIKSAAN KESEHATAN BOT KEUANGAN PRIBADI\n")
    
    # Jalankan semua pemeriksaan
    env_check = check_environment_variables()
    sheets_check = check_google_sheets_connection() if env_check else False
    telegram_check = check_telegram_connection() if env_check else False
    webhook_check = check_webhook_endpoint() if env_check else False
    
    # Tampilkan ringkasan
    print_header("RINGKASAN PEMERIKSAAN")
    print(f"{'✅' if env_check else '❌'} Variabel Lingkungan: {'Semua variabel wajib tersedia' if env_check else 'Ada variabel wajib yang hilang'}")
    print(f"{'✅' if sheets_check else '❌'} Koneksi Google Sheets: {'Berhasil' if sheets_check else 'Gagal'}")
    print(f"{'✅' if telegram_check else '❌'} Koneksi Telegram: {'Berhasil' if telegram_check else 'Gagal'}")
    print(f"{'✅' if webhook_check else '❌'} Endpoint Webhook: {'Dapat diakses' if webhook_check else 'Tidak dapat diakses'}")
    
    # Tentukan status keseluruhan
    overall_status = env_check and sheets_check and telegram_check
    print("\n" + "=" * 50)
    if overall_status:
        print("✅ SEMUA PEMERIKSAAN BERHASIL! Bot siap digunakan.")
    else:
        print("❌ ADA MASALAH YANG PERLU DIPERBAIKI! Lihat detail di atas.")
    print("=" * 50 + "\n")

if __name__ == "__main__":
    main()