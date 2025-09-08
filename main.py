# main.py
import os
import json
import pandas as pd
import datetime
import logging
import traceback
import re
from functools import wraps
from flask import Flask, request, jsonify
import gspread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import asyncio
from typing import Optional, Tuple, Dict, Any

# --- 1. KONFIGURASI ---
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
GSPREAD_CREDENTIALS = os.environ.get('GSPREAD_CREDENTIALS')
SPREADSHEET_NAME = os.environ.get('SPREADSHEET_NAME', 'Catatan Keuangan')

try:
    ALLOWED_USER_ID = int(os.environ.get('ALLOWED_USER_ID'))
except (TypeError, ValueError):
    ALLOWED_USER_ID = None

# --- 2. INISIALISASI APLIKASI ---
app = Flask(__name__)

# Inisialisasi Klien Google Sheets dengan connection pooling
gspread_client = None
spreadsheet = None

def initialize_gspread():
    """Initialize Google Sheets client with better error handling."""
    global gspread_client, spreadsheet
    
    try:
        if not GSPREAD_CREDENTIALS:
            logging.error("GSPREAD_CREDENTIALS environment variable is not set")
            return False
            
        creds_dict = json.loads(GSPREAD_CREDENTIALS)
        gspread_client = gspread.service_account_from_dict(creds_dict)
        spreadsheet = gspread_client.open(SPREADSHEET_NAME)
        
        # Verify the required worksheet exists
        try:
            spreadsheet.worksheet("Transaksi")
            logging.info(f"✅ Successfully connected to spreadsheet: {SPREADSHEET_NAME}")
            return True
        except gspread.exceptions.WorksheetNotFound:
            logging.error("❌ Worksheet 'Transaksi' not found. Creating it...")
            # Create the worksheet with headers
            worksheet = spreadsheet.add_worksheet(title="Transaksi", rows="1000", cols="5")
            worksheet.append_row(["Tanggal", "Tipe", "Jumlah", "Kategori", "Deskripsi"])
            logging.info("✅ Created 'Transaksi' worksheet with headers")
            return True
            
    except json.JSONDecodeError:
        logging.error("❌ Invalid JSON in GSPREAD_CREDENTIALS environment variable")
        return False
    except Exception as e:
        logging.error(f"❌ Error initializing Google Sheets client: {e}", exc_info=True)
        return False

# Initialize Google Sheets connection
initialize_gspread()

application = Application.builder().token(TELEGRAM_TOKEN).build()

# --- 3. FUNGSI BANTUAN & DECORATOR ---
def restricted(func):
    """Decorator to restrict bot access to authorized users only."""
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        
        if user_id != ALLOWED_USER_ID:
            logging.warning(f"🚫 Unauthorized access denied for user {user_id}")
            await update.message.reply_text(
                "🚫 *Akses Ditolak*\n\n"
                "Maaf, kamu tidak memiliki akses ke bot ini.\n"
                "Bot ini hanya untuk penggunaan pribadi.",
                parse_mode='Markdown'
            )
            return
            
        # Check Google Sheets connection
        if not gspread_client or not spreadsheet:
            logging.error("❌ Google Sheets connection not available")
            await update.message.reply_text(
                "⚠️ *Koneksi Bermasalah*\n\n"
                "Koneksi ke spreadsheet gagal.\n"
                "Silakan coba lagi dalam beberapa saat.",
                parse_mode='Markdown'
            )
            return
            
        # Verify connection is still valid
        try:
            spreadsheet.worksheets()
        except Exception as e:
            logging.error(f"❌ Google Sheets connection error: {e}", exc_info=True)
            # Try to reinitialize connection
            if initialize_gspread():
                logging.info("✅ Successfully reconnected to Google Sheets")
            else:
                await update.message.reply_text(
                    "⚠️ *Koneksi Terputus*\n\n"
                    "Koneksi ke spreadsheet terputus.\n"
                    "Silakan coba lagi dalam beberapa saat.",
                    parse_mode='Markdown'
                )
                return
            
        return await func(update, context, *args, **kwargs)
    return wrapped

def parse_message(text: str) -> Tuple[Optional[int], Optional[str], Optional[str]]:
    """
    Parse message text into amount, category, and description.
    
    Expected format: /command amount #category description
    Returns (None, None, None) if parsing fails.
    """
    parts = text.split()
    
    if len(parts) < 2:
        logging.warning(f"Message too short: {text}")
        return None, None, None
        
    try:
        jumlah = abs(int(parts[1]))
    except (ValueError, IndexError) as e:
        logging.warning(f"Error parsing amount in message: {text}. Error: {e}")
        return None, None, None
        
    # Process category and description
    kategori = "lainnya"
    deskripsi_parts = []
    
    for part in parts[2:]:
        if part.startswith('#'):
            kategori = part[1:].lower().strip()
        else:
            deskripsi_parts.append(part)
            
    deskripsi = " ".join(deskripsi_parts) if deskripsi_parts else "-"
    return jumlah, kategori, deskripsi

def format_currency(amount: float) -> str:
    """Format currency with Indonesian Rupiah formatting."""
    return f"Rp {amount:,.0f}".replace(",", ".")

def get_month_name(month: int) -> str:
    """Dapatkan nama bulan dalam Bahasa Indonesia."""
    months = [
        "", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember"
    ]
    return months[month] if 1 <= month <= 12 else "Tidak Diketahui"

def setup_logging():
    """Configure logging with proper format and level."""
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(os.path.join(log_dir, 'bot.log'))
        ]
    )
    
    # Reduce noise from external libraries
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

# --- 4. DEFINISI FUNGSI-FUNGSI BOT ---
@restricted
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Pesan selamat datang dengan tombol interaktif."""
    user_name = update.effective_user.first_name
    
    keyboard = [
        [
            InlineKeyboardButton("📊 Laporan Bulan Ini", callback_data="laporan"),
            InlineKeyboardButton("📈 Perbandingan", callback_data="compare")
        ],
        [
            InlineKeyboardButton("💡 Tips Penggunaan", callback_data="tips"),
            InlineKeyboardButton("ℹ️ Info Bot", callback_data="info")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    pesan = (
        f"👋 *Halo {user_name}!*\n\n"
        "🎯 *Bot Keuangan Pribadi* siap membantu!\n\n"
        "📝 *Perintah Utama:*\n"
        "• `/masuk [jumlah] #[kategori] [keterangan]`\n"
        "  _Contoh: /masuk 500000 #gaji Gaji bulan ini_\n\n"
        "• `/keluar [jumlah] #[kategori] [keterangan]`\n"
        "  _Contoh: /keluar 50000 #makanan Makan siang_\n\n"
        "📊 *Laporan & Analisis:*\n"
        "• `/laporan` - Ringkasan keuangan bulan ini\n"
        "• `/compare` - Perbandingan dengan bulan lalu\n\n"
        "💡 *Kategori Populer:*\n"
        "`#makanan #transportasi #belanja #tagihan #hiburan #kesehatan #gaji #bonus`\n\n"
        "Pilih menu di bawah untuk aksi cepat! 👇"
    )
    
    await update.message.reply_text(pesan, parse_mode='Markdown', reply_markup=reply_markup)

@restricted
async def catat_transaksi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mencatat transaksi pemasukan atau pengeluaran dengan umpan balik yang lebih baik."""
    try:
        command = update.message.text.split()[0].lower()
        tipe = "Pemasukan" if command == "/masuk" else "Pengeluaran"
        emoji = "💰" if tipe == "Pemasukan" else "💸"
        
        jumlah, kategori, deskripsi = parse_message(update.message.text)
        if jumlah is None:
            keyboard = [[
                InlineKeyboardButton("📝 Contoh Format", callback_data="format_help")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "❌ *Format Salah*\n\n"
                "📝 *Format yang benar:*\n"
                f"`{command} [jumlah] #[kategori] [keterangan]`\n\n"
                "💡 *Contoh:*\n"
                f"`{command} 50000 #makanan Makan siang di restoran`\n\n"
                "⚠️ *Pastikan:*\n"
                "• Jumlah berupa angka\n"
                "• Kategori diawali dengan #\n"
                "• Keterangan bersifat opsional",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            return
            
        tanggal = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_row = [tanggal, tipe, jumlah, kategori, deskripsi]
        
        try:
            target_sheet = spreadsheet.worksheet("Transaksi")
            target_sheet.append_row(new_row)
            
            # Buat pesan sukses dengan ringkasan
            keyboard = [[
                InlineKeyboardButton("📊 Lihat Laporan", callback_data="laporan"),
                InlineKeyboardButton("➕ Tambah Lagi", callback_data="add_more")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"{emoji} *Transaksi Berhasil Dicatat!*\n\n"
                f"📋 *Detail:*\n"
                f"• *Tipe:* {tipe}\n"
                f"• *Jumlah:* `{format_currency(jumlah)}`\n"
                f"• *Kategori:* `#{kategori}`\n"
                f"• *Keterangan:* _{deskripsi}_\n"
                f"• *Waktu:* {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
                "✅ Data telah tersimpan di spreadsheet!",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
            logging.info(f"✅ Transaksi dicatat: {tipe} {format_currency(jumlah)} untuk #{kategori}")
            
        except gspread.exceptions.WorksheetNotFound:
            logging.error("❌ Worksheet 'Transaksi' tidak ditemukan")
            await update.message.reply_text(
                "❌ *Worksheet Tidak Ditemukan*\n\n"
                "Worksheet 'Transaksi' tidak ditemukan.\n"
                "Pastikan spreadsheet memiliki sheet dengan nama 'Transaksi'.",
                parse_mode='Markdown'
            )
        except gspread.exceptions.APIError as e:
            logging.error(f"❌ Kesalahan API Google Sheets: {e}")
            await update.message.reply_text(
                "⚠️ *Error API Google Sheets*\n\n"
                "Terjadi kesalahan saat mengakses Google Sheets.\n"
                "Silakan coba lagi dalam beberapa saat.",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logging.error(f"❌ Kesalahan di catat_transaksi: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ *Terjadi Kesalahan*\n\n"
            "Maaf, ada error saat mencatat transaksi.\n"
            "Silakan coba lagi atau hubungi administrator.",
            parse_mode='Markdown'
        )

@restricted
async def laporan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Menghasilkan laporan keuangan bulanan yang komprehensif."""
    try:
        # Tampilkan pesan memuat
        loading_msg = await update.message.reply_text("⏳ *Menyusun laporan keuangan...*", parse_mode='Markdown')
        
        sekarang = datetime.datetime.now()
        bulan_target, tahun_target = sekarang.month, sekarang.year

        try:
            sheet = spreadsheet.worksheet("Transaksi")
            data = sheet.get_all_records()

            if not data:
                await loading_msg.edit_text(
                    "📭 *Belum Ada Data*\n\n"
                    "Belum ada transaksi yang tercatat.\n"
                    "Mulai catat transaksi dengan `/masuk` atau `/keluar`!",
                    parse_mode='Markdown'
                )
                return
                
        except gspread.exceptions.WorksheetNotFound:
            logging.error("❌ Worksheet 'Transaksi' tidak ditemukan di laporan")
            await loading_msg.edit_text(
                "❌ *Worksheet Tidak Ditemukan*\n\n"
                "Worksheet 'Transaksi' tidak ditemukan.\n"
                "Pastikan spreadsheet memiliki sheet dengan nama 'Transaksi'.",
                parse_mode='Markdown'
            )
            return
        except Exception as e:
            logging.error(f"❌ Kesalahan mengakses worksheet di laporan: {e}", exc_info=True)
            await loading_msg.edit_text(
                "⚠️ *Error Mengakses Data*\n\n"
                "Terjadi kesalahan saat mengakses data.\n"
                "Silakan coba lagi dalam beberapa saat.",
                parse_mode='Markdown'
            )
            return

        # Proses data
        df = pd.DataFrame(data)
        df['Jumlah'] = pd.to_numeric(df['Jumlah'], errors='coerce').fillna(0)
        df['Tanggal'] = pd.to_datetime(df['Tanggal'], errors='coerce')
        df.dropna(subset=['Tanggal'], inplace=True)

        # Hitung saldo
        tanggal_awal_bulan_ini = datetime.date(tahun_target, bulan_target, 1)
        df_sebelumnya = df[df['Tanggal'].dt.date < tanggal_awal_bulan_ini]
        pemasukan_sebelumnya = df_sebelumnya[df_sebelumnya['Tipe'] == 'Pemasukan']['Jumlah'].sum()
        pengeluaran_sebelumnya = df_sebelumnya[df_sebelumnya['Tipe'] == 'Pengeluaran']['Jumlah'].sum()
        saldo_awal = pemasukan_sebelumnya - pengeluaran_sebelumnya

        df_bulan_ini = df[(df['Tanggal'].dt.month == bulan_target) & (df['Tanggal'].dt.year == tahun_target)]
        pemasukan_bulan_ini = df_bulan_ini[df_bulan_ini['Tipe'] == 'Pemasukan']['Jumlah'].sum()
        pengeluaran_bulan_ini = df_bulan_ini[df_bulan_ini['Tipe'] == 'Pengeluaran']['Jumlah'].sum()
        saldo_akhir = saldo_awal + pemasukan_bulan_ini - pengeluaran_bulan_ini

        # Rincian kategori
        pengeluaran_per_kategori = df_bulan_ini[df_bulan_ini['Tipe'] == 'Pengeluaran'].groupby('Kategori')['Jumlah'].sum().sort_values(ascending=False)
        pemasukan_per_kategori = df_bulan_ini[df_bulan_ini['Tipe'] == 'Pemasukan'].groupby('Kategori')['Jumlah'].sum().sort_values(ascending=False)
        
        # Buat teks rincian kategori
        rincian_pengeluaran = ""
        if not pengeluaran_per_kategori.empty:
            rincian_pengeluaran = "\n\n💸 *Rincian Pengeluaran:*\n"
            for i, (kategori, total) in enumerate(pengeluaran_per_kategori.head(5).items()):
                percentage = (total / pengeluaran_bulan_ini * 100) if pengeluaran_bulan_ini > 0 else 0
                rincian_pengeluaran += f"`#{kategori:<12} {format_currency(total)} ({percentage:.1f}%)`\n"
            
            if len(pengeluaran_per_kategori) > 5:
                rincian_pengeluaran += f"_...dan {len(pengeluaran_per_kategori) - 5} kategori lainnya_\n"

        rincian_pemasukan = ""
        if not pemasukan_per_kategori.empty:
            rincian_pemasukan = "\n\n💰 *Rincian Pemasukan:*\n"
            for kategori, total in pemasukan_per_kategori.head(3).items():
                rincian_pemasukan += f"`#{kategori:<12} {format_currency(total)}`\n"

        # Tentukan kesehatan keuangan
        if saldo_akhir > saldo_awal:
            health_emoji = "📈"
            health_text = "Keuangan membaik!"
        elif saldo_akhir < saldo_awal:
            health_emoji = "📉"
            health_text = "Perlu lebih hemat."
        else:
            health_emoji = "➖"
            health_text = "Keuangan stabil."

        nama_bulan_laporan = get_month_name(bulan_target)
        
        # Buat tombol interaktif
        keyboard = [
            [
                InlineKeyboardButton("📈 Perbandingan", callback_data="compare"),
                InlineKeyboardButton("🔄 Segarkan", callback_data="laporan")
            ],
            [InlineKeyboardButton("➕ Tambah Transaksi", callback_data="add_transaction")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        pesan = (
            f"📊 *Laporan Keuangan {nama_bulan_laporan} {tahun_target}*\n\n"
            f"💼 *Saldo Awal:* `{format_currency(saldo_awal)}`\n\n"
            f"💰 *Pemasukan:* `{format_currency(pemasukan_bulan_ini)}`\n"
            f"💸 *Pengeluaran:* `{format_currency(pengeluaran_bulan_ini)}`\n"
            f"{'─' * 30}\n"
            f"🏦 *SALDO AKHIR:* `{format_currency(saldo_akhir)}`\n\n"
            f"{health_emoji} _{health_text}_"
            f"{rincian_pemasukan}"
            f"{rincian_pengeluaran}"
        )
        
        await loading_msg.edit_text(pesan, parse_mode='Markdown', reply_markup=reply_markup)
        
    except Exception as e:
        logging.error(f"❌ Kesalahan di laporan: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ *Error Membuat Laporan*\n\n"
            "Terjadi kesalahan saat membuat laporan.\n"
            "Silakan coba lagi dalam beberapa saat.",
            parse_mode='Markdown'
        )

@restricted
async def compare_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Menghasilkan laporan perbandingan terperinci antara bulan ini dan sebelumnya."""
    try:
        loading_msg = await update.message.reply_text("⏳ *Menyusun analisis perbandingan...*", parse_mode='Markdown')
        
        try:
            sheet = spreadsheet.worksheet("Transaksi")
            data = sheet.get_all_records()
            if not data:
                await loading_msg.edit_text(
                    "📭 *Belum Ada Data*\n\n"
                    "Belum ada data untuk dibandingkan.\n"
                    "Mulai catat transaksi terlebih dahulu!",
                    parse_mode='Markdown'
                )
                return
        except Exception as e:
            logging.error(f"❌ Kesalahan mengakses worksheet di compare_report: {e}", exc_info=True)
            await loading_msg.edit_text(
                "⚠️ *Error Mengakses Data*\n\n"
                "Terjadi kesalahan saat mengakses data.\n"
                "Silakan coba lagi dalam beberapa saat.",
                parse_mode='Markdown'
            )
            return

        # Proses data
        df = pd.DataFrame(data)
        df['Jumlah'] = pd.to_numeric(df['Jumlah'], errors='coerce').fillna(0)
        df['Tanggal'] = pd.to_datetime(df['Tanggal'], errors='coerce')
        df.dropna(subset=['Tanggal'], inplace=True)

        sekarang = datetime.datetime.now()
        bulan_ini, tahun_ini = sekarang.month, sekarang.year
        
        # Hitung bulan sebelumnya
        if bulan_ini == 1:
            bulan_lalu, tahun_lalu = 12, tahun_ini - 1
        else:
            bulan_lalu, tahun_lalu = bulan_ini - 1, tahun_ini

        df_bulan_ini = df[(df['Tanggal'].dt.month == bulan_ini) & (df['Tanggal'].dt.year == tahun_ini)]
        df_bulan_lalu = df[(df['Tanggal'].dt.month == bulan_lalu) & (df['Tanggal'].dt.year == tahun_lalu)]

        # Hitung total
        pemasukan_ini = df_bulan_ini[df_bulan_ini['Tipe'] == 'Pemasukan']['Jumlah'].sum()
        pengeluaran_ini = df_bulan_ini[df_bulan_ini['Tipe'] == 'Pengeluaran']['Jumlah'].sum()
        pemasukan_lalu = df_bulan_lalu[df_bulan_lalu['Tipe'] == 'Pemasukan']['Jumlah'].sum()
        pengeluaran_lalu = df_bulan_lalu[df_bulan_lalu['Tipe'] == 'Pengeluaran']['Jumlah'].sum()

        # Perbandingan kategori
        kat_pengeluaran_ini = df_bulan_ini[df_bulan_ini['Tipe'] == 'Pengeluaran'].groupby('Kategori')['Jumlah'].sum()
        kat_pengeluaran_lalu = df_bulan_lalu[df_bulan_lalu['Tipe'] == 'Pengeluaran'].groupby('Kategori')['Jumlah'].sum()
        
        df_compare = pd.concat([kat_pengeluaran_ini.rename('Bulan Ini'), kat_pengeluaran_lalu.rename('Bulan Lalu')], axis=1).fillna(0)
        df_compare = df_compare.sort_values(by='Bulan Ini', ascending=False)
        
        # Buat teks perbandingan
        rincian_teks = "\n\n📊 *Perbandingan per Kategori:*\n"
        for kategori, row in df_compare.head(8).iterrows():
            total_ini, total_lalu = row['Bulan Ini'], row['Bulan Lalu']
            selisih = total_ini - total_lalu
            
            if selisih > 0:
                emoji = "🔺"
                trend = f"+{format_currency(selisih)}"
            elif selisih < 0:
                emoji = "🔻"
                trend = f"{format_currency(selisih)}"
            else:
                emoji = "➖"
                trend = "Sama"
            
            rincian_teks += f"`#{kategori:<10}` {format_currency(total_ini)} vs {format_currency(total_lalu)} {emoji}\n"
        
        # Hitung perubahan persentase
        pemasukan_change = ((pemasukan_ini - pemasukan_lalu) / pemasukan_lalu * 100) if pemasukan_lalu > 0 else 0
        pengeluaran_change = ((pengeluaran_ini - pengeluaran_lalu) / pengeluaran_lalu * 100) if pengeluaran_lalu > 0 else 0
        
        # Tentukan tren
        if pengeluaran_change > 10:
            trend_emoji = "⚠️"
            trend_text = "Pengeluaran meningkat signifikan!"
        elif pengeluaran_change < -10:
            trend_emoji = "✅"
            trend_text = "Pengeluaran berkurang signifikan!"
        else:
            trend_emoji = "📊"
            trend_text = "Pengeluaran relatif stabil."

        nama_bulan_ini = get_month_name(bulan_ini)
        nama_bulan_lalu = get_month_name(bulan_lalu)

        # Buat tombol interaktif
        keyboard = [
            [
                InlineKeyboardButton("📊 Laporan Detail", callback_data="laporan"),
                InlineKeyboardButton("🔄 Segarkan", callback_data="compare")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        pesan = (
            f"📈 *Analisis Perbandingan Keuangan*\n"
            f"_{nama_bulan_ini} vs {nama_bulan_lalu}_\n\n"
            f"💰 *Pemasukan:*\n"
            f"• {nama_bulan_ini}: `{format_currency(pemasukan_ini)}`\n"
            f"• {nama_bulan_lalu}: `{format_currency(pemasukan_lalu)}`\n"
            f"• Perubahan: `{pemasukan_change:+.1f}%`\n\n"
            f"💸 *Pengeluaran:*\n"
            f"• {nama_bulan_ini}: `{format_currency(pengeluaran_ini)}`\n"
            f"• {nama_bulan_lalu}: `{format_currency(pengeluaran_lalu)}`\n"
            f"• Perubahan: `{pengeluaran_change:+.1f}%`\n\n"
            f"{trend_emoji} _{trend_text}_"
            f"{rincian_teks}"
        )
        
        await loading_msg.edit_text(pesan, parse_mode='Markdown', reply_markup=reply_markup)
        
    except Exception as e:
        logging.error(f"❌ Kesalahan di compare_report: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ *Error Membuat Perbandingan*\n\n"
            "Terjadi kesalahan saat membuat analisis.\n"
            "Silakan coba lagi dalam beberapa saat.",
            parse_mode='Markdown'
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Menangani penekanan tombol keyboard inline."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "laporan":
        await laporan(update, context)
    elif query.data == "compare":
        await compare_report(update, context)
    elif query.data == "tips":
        tips_text = (
            "💡 *Tips Penggunaan Bot*\n\n"
            "📝 *Format Pesan:*\n"
            "• Gunakan angka tanpa titik/koma\n"
            "• Kategori harus diawali #\n"
            "• Keterangan bersifat opsional\n\n"
            "🏷️ *Kategori yang Disarankan:*\n"
            "`#makanan #transportasi #belanja #tagihan`\n"
            "`#hiburan #kesehatan #pendidikan #gaji`\n\n"
            "⚡ *Tips Cepat:*\n"
            "• Catat transaksi segera setelah terjadi\n"
            "• Gunakan kategori yang konsisten\n"
            "• Periksa laporan secara berkala\n"
            "• Bandingkan pengeluaran antar bulan"
        )
        await query.edit_message_text(tips_text, parse_mode='Markdown')
    elif query.data == "info":
        info_text = (
            "ℹ️ *Informasi Bot Keuangan Pribadi*\n\n"
            "🤖 *Versi:* 2.0.0\n"
            "👨‍💻 *Pengembang:* Asisten Keuangan Pribadi\n"
            "📊 *Database:* Google Sheets\n"
            "🔒 *Keamanan:* Akses Pribadi Saja\n\n"
            "✨ *Fitur Utama:*\n"
            "• Pencatatan transaksi otomatis\n"
            "• Laporan keuangan bulanan\n"
            "• Analisis perbandingan\n"
            "• Kategorisasi pengeluaran\n"
            "• Antarmuka interaktif\n\n"
            "📞 *Dukungan:* Hubungi administrator jika ada masalah"
        )
        await query.edit_message_text(info_text, parse_mode='Markdown')
    elif query.data == "format_help":
        format_text = (
            "📝 *Panduan Format Pesan*\n\n"
            "✅ *Format Benar:*\n"
            "`/masuk 500000 #gaji Gaji bulan ini`\n"
            "`/keluar 75000 #makanan Makan di restoran`\n"
            "`/keluar 20000 #transportasi Ongkos ojek`\n\n"
            "❌ *Format Salah:*\n"
            "`/masuk lima ratus ribu` _(bukan angka)_\n"
            "`/keluar 50.000` _(pakai titik)_\n"
            "`/masuk 100000 makanan` _(tanpa #)_\n\n"
            "💡 *Tips:*\n"
            "• Jumlah harus berupa angka bulat\n"
            "• Kategori wajib diawali dengan #\n"
            "• Keterangan boleh kosong"
        )
        await query.edit_message_text(format_text, parse_mode='Markdown')
    elif query.data == "add_more":
        add_text = (
            "➕ *Tambah Transaksi Baru*\n\n"
            "Gunakan perintah berikut:\n\n"
            "💰 *Untuk Pemasukan:*\n"
            "`/masuk [jumlah] #[kategori] [keterangan]`\n\n"
            "💸 *Untuk Pengeluaran:*\n"
            "`/keluar [jumlah] #[kategori] [keterangan]`\n\n"
            "📝 *Contoh Cepat:*\n"
            "• `/masuk 1000000 #gaji`\n"
            "• `/keluar 50000 #makanan`\n"
            "• `/keluar 100000 #belanja Kebutuhan bulanan`"
        )
        await query.edit_message_text(add_text, parse_mode='Markdown')
    elif query.data == "add_transaction":
        transaction_text = (
            "➕ *Menu Tambah Transaksi*\n\n"
            "Pilih jenis transaksi yang ingin dicatat:\n\n"
            "💰 *Pemasukan:* `/masuk [jumlah] #[kategori] [keterangan]`\n"
            "💸 *Pengeluaran:* `/keluar [jumlah] #[kategori] [keterangan]`\n\n"
            "🏷️ *Kategori Populer:*\n"
            "• Pemasukan: `#gaji #bonus #freelance #investasi`\n"
            "• Pengeluaran: `#makanan #transportasi #belanja #tagihan #hiburan`\n\n"
            "Ketik perintah langsung di chat untuk mencatat transaksi!"
        )
        await query.edit_message_text(transaction_text, parse_mode='Markdown')

# --- 5. BAGIAN WEBHOOK ---
@app.route('/webhook', methods=['POST'])
def webhook() -> str:
    """Handle incoming webhook requests from Telegram."""
    try:
        async def process():
            try:
                update = Update.de_json(request.get_json(force=True), application.bot)
                await application.initialize()
                await application.process_update(update)
                await application.shutdown()
            except Exception as e:
                logging.error(f"❌ Error processing update: {e}", exc_info=True)

        asyncio.run(process())
        return "OK"
    except Exception as e:
        logging.error(f"❌ Webhook error: {e}", exc_info=True)
        return "Error", 500

@app.route('/')
def index():
    """Health check endpoint with enhanced information."""
    try:
        # Check Google Sheets connection
        sheets_status = "✅ Connected" if gspread_client and spreadsheet else "❌ Disconnected"
        
        # Check if worksheet exists
        worksheet_status = "❌ Not Found"
        if spreadsheet:
            try:
                spreadsheet.worksheet("Transaksi")
                worksheet_status = "✅ Available"
            except:
                worksheet_status = "❌ Not Found"
        
        # Bot information
        bot_info = {
            "name": "Noxara Finance Bot",
            "version": "2.0.0",
            "status": "🟢 Running",
            "google_sheets": sheets_status,
            "worksheet": worksheet_status,
            "features": [
                "Transaction Recording",
                "Monthly Reports", 
                "Comparison Analysis",
                "Interactive UI",
                "Auto Reconnection"
            ]
        }
        
        return jsonify(bot_info)
    except Exception as e:
        logging.error(f"❌ Health check error: {e}")
        return jsonify({"status": "❌ Error", "message": str(e)}), 500

@app.route('/health')
def health():
    """Simple health check endpoint."""
    return jsonify({"status": "healthy", "timestamp": datetime.datetime.now().isoformat()})

# --- 6. PENDAFTARAN PERINTAH (HANDLER) ---
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("masuk", catat_transaksi))
application.add_handler(CommandHandler("keluar", catat_transaksi))
application.add_handler(CommandHandler("laporan", laporan))
application.add_handler(CommandHandler("compare", compare_report))
application.add_handler(CallbackQueryHandler(button_handler))

# --- 7. MAIN BLOCK ---
if __name__ == "__main__":
    # Setup logging
    setup_logging()
    logging.info("🚀 Starting Noxara Finance Bot v2.0.0")
    
    # Validate environment variables
    if not TELEGRAM_TOKEN:
        logging.error("❌ TELEGRAM_TOKEN environment variable is required")
        exit(1)
    
    if not ALLOWED_USER_ID:
        logging.error("❌ ALLOWED_USER_ID environment variable is required")
        exit(1)
    
    if not GSPREAD_CREDENTIALS:
        logging.error("❌ GSPREAD_CREDENTIALS environment variable is required")
        exit(1)
    
    # Run the Flask app
    port = int(os.environ.get("PORT", 5000))
    logging.info(f"🌐 Starting web server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
