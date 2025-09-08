# app/bot/utils.py
"""
Fungsi utilitas untuk bot Telegram.

Modul ini berisi fungsi-fungsi pembantu yang digunakan oleh handler bot.
"""

import logging
import datetime
from functools import wraps
from typing import Optional, Tuple
from telegram import Update
from telegram.ext import ContextTypes
from app.config import ALLOWED_USER_ID
from app.database.sheets import get_spreadsheet

def restricted(func):
    """Decorator untuk membatasi akses bot hanya untuk pengguna yang berwenang."""
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        
        if user_id != ALLOWED_USER_ID:
            logging.warning(f"🚫 Akses tidak sah ditolak untuk pengguna {user_id}")
            await update.message.reply_text(
                "🚫 *Akses Ditolak*\n\n"
                "Maaf, kamu tidak memiliki akses ke bot ini.\n"
                "Bot ini hanya untuk penggunaan pribadi.",
                parse_mode='Markdown'
            )
            return
            
        # Periksa koneksi Google Sheets
        spreadsheet = get_spreadsheet()
        if not spreadsheet:
            logging.error("❌ Koneksi Google Sheets tidak tersedia")
            await update.message.reply_text(
                "⚠️ *Koneksi Bermasalah*\n\n"
                "Koneksi ke spreadsheet gagal.\n"
                "Silakan coba lagi dalam beberapa saat.",
                parse_mode='Markdown'
            )
            return
            
        return await func(update, context, *args, **kwargs)
    return wrapped

def parse_message(text: str) -> Tuple[Optional[int], Optional[str], Optional[str]]:
    """
    Mengurai teks pesan menjadi jumlah, kategori, dan deskripsi dengan validasi yang ditingkatkan.
    
    Format yang diharapkan: /perintah jumlah #kategori deskripsi
    Mengembalikan (None, None, None) jika penguraian gagal.
    """
    parts = text.split()
    
    # Validasi pesan memiliki setidaknya perintah dan jumlah
    if len(parts) < 2:
        logging.warning(f"Pesan terlalu pendek: {text}")
        return None, None, None
        
    # Mengurai jumlah dengan penanganan error yang lebih baik
    try:
        # Pastikan kita mendapatkan nilai integer positif
        jumlah = abs(int(parts[1]))
        if jumlah <= 0:
            logging.warning(f"Jumlah harus lebih besar dari 0: {text}")
            return None, None, None
    except (ValueError, IndexError) as e:
        logging.warning(f"Error mengurai jumlah dalam pesan: {text}. Error: {e}")
        return None, None, None
    
    # Nilai default
    kategori = "lainnya"
    deskripsi_parts = []
    has_category = False
    
    # Memproses kategori dan deskripsi lebih efisien
    for part in parts[2:]:
        if part.startswith('#'):
            # Ekstrak kategori tanpa simbol # dan normalisasi
            extracted_category = part[1:].lower().strip()
            if extracted_category:  # Pastikan kategori tidak kosong
                kategori = extracted_category
                has_category = True
        else:
            deskripsi_parts.append(part)
    
    # Gabungkan bagian deskripsi atau gunakan default
    deskripsi = " ".join(deskripsi_parts) if deskripsi_parts else "Tidak ada keterangan"
    
    # Batasi panjang deskripsi untuk mencegah masalah
    if len(deskripsi) > 100:
        deskripsi = deskripsi[:97] + '...'
    
    return jumlah, kategori, deskripsi

def format_currency(amount: float) -> str:
    """Memformat mata uang dengan format Rupiah Indonesia."""
    return f"Rp {amount:,.0f}".replace(",", ".")

def get_month_name(month: int) -> str:
    """Dapatkan nama bulan dalam Bahasa Indonesia."""
    months = [
        "", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember"
    ]
    return months[month] if 1 <= month <= 12 else "Tidak Diketahui"