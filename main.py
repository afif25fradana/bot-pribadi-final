# main.py
import os
import json
import pandas as pd
import datetime
import logging
import traceback
import re
from functools import wraps
from flask import Flask, request
import gspread
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio

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

# Inisialisasi Klien Google Sheets sekali saja
gspread_client = None
spreadsheet = None

try:
    if GSPREAD_CREDENTIALS:
        creds_dict = json.loads(GSPREAD_CREDENTIALS)
        gspread_client = gspread.service_account_from_dict(creds_dict)
        spreadsheet = gspread_client.open(SPREADSHEET_NAME)
        logging.info(f"Successfully connected to spreadsheet: {SPREADSHEET_NAME}")
    else:
        logging.error("GSPREAD_CREDENTIALS environment variable is not set")
except json.JSONDecodeError:
    logging.error("Invalid JSON in GSPREAD_CREDENTIALS environment variable")
except Exception as e:
    logging.error(f"Error initializing Google Sheets client: {e}", exc_info=True)

application = Application.builder().token(TELEGRAM_TOKEN).build()

# --- 3. FUNGSI BANTUAN & DECORATOR ---
def restricted(func):
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id != ALLOWED_USER_ID:
            logging.warning(f"Unauthorized access denied for user {user_id}.")
            await update.message.reply_text("Maaf, kamu tidak memiliki akses ke bot ini.")
            return
            
        # Check if Google Sheets connection is available
        if not gspread_client or not spreadsheet:
            logging.error("Google Sheets connection not available")
            await update.message.reply_text("Koneksi ke spreadsheet gagal. Cek konfigurasi atau coba lagi nanti.")
            return
            
        # Check if connection is still valid by performing a simple operation
        try:
            # Try to get worksheets to verify connection is still valid
            spreadsheet.worksheets()
        except Exception as e:
            logging.error(f"Google Sheets connection error: {e}", exc_info=True)
            await update.message.reply_text("Koneksi ke spreadsheet terputus. Coba lagi nanti.")
            return
            
        return await func(update, context, *args, **kwargs)
    return wrapped


def parse_message(text):
    """Parse message text into amount, category, and description.
    
    Expected format: /command amount #category description
    Returns (None, None, None) if parsing fails.
    """
    parts = text.split()
    
    # Check if we have enough parts
    if len(parts) < 2:
        logging.warning(f"Message too short: {text}")
        return None, None, None
        
    try:
        jumlah = abs(int(parts[1]))
    except (ValueError, IndexError) as e:
        logging.warning(f"Error parsing amount in message: {text}. Error: {e}")
        return None, None, None
        
    # Process category and description
    kategori = "uncategorized"
    deskripsi_parts = []
    
    for part in parts[2:]:
        if part.startswith('#'):
            kategori = part[1:].lower()
        else:
            deskripsi_parts.append(part)
            
    deskripsi = " ".join(deskripsi_parts) if deskripsi_parts else "-"
    return jumlah, kategori, deskripsi

def setup_logging():
    """Configure logging with proper format and level."""
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
        handlers=[
            logging.StreamHandler(),  # Console handler
            logging.FileHandler(os.path.join(log_dir, 'bot.log'))  # File handler
        ]
    )
    
    # Set higher log level for some noisy libraries
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.WARNING)

# --- 4. DEFINISI FUNGSI-FUNGSI BOT ---
@restricted
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_name = update.effective_user.first_name
    pesan = (
        f"Halo {user_name}~! 👋 Mau nyatet apa hari ini?\n\n"
        "Ini perintah yang bisa kamu pakai:\n\n"
        "✍️ *Pencatatan*:\n"
        "`/masuk [jumlah] #[kat] [ket]`\n"
        "`/keluar [jumlah] #[kat] [ket]`\n\n"
        "📊 *Laporan Arus Kas*:\n"
        "`/laporan`\n"
        "   (Laporan bulan ini dengan saldo awal)\n\n"
        "📈 *Analisis Perbandingan*:\n"
        "`/compare`\n"
        "   (Bandingkan pengeluaran bulan ini & lalu)"
    )
    await update.message.reply_text(pesan, parse_mode='Markdown')

@restricted
async def catat_transaksi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        command = update.message.text.split()[0].lower()
        tipe = "Pemasukan" if command == "/masuk" else "Pengeluaran"
        emoji = "🟢" if tipe == "Pemasukan" else "🔴"
        
        jumlah, kategori, deskripsi = parse_message(update.message.text)
        if jumlah is None:
            await update.message.reply_text("Format salah. Contoh: `/keluar 50000 #makanan Makan siang`", parse_mode='Markdown')
            return
            
        tanggal = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_row = [tanggal, tipe, jumlah, kategori, deskripsi]
        
        # Get worksheet with error handling
        try:
            target_sheet = spreadsheet.worksheet("Transaksi")
            target_sheet.append_row(new_row)
            await update.message.reply_text(f"{emoji} Dicatat: *{tipe}* `Rp {jumlah:,.0f}` untuk kategori `#{kategori}`.\n\nDeskripsi: _{deskripsi}_", parse_mode='Markdown')
            logging.info(f"Transaction recorded: {tipe} {jumlah} for {kategori}")
        except gspread.exceptions.WorksheetNotFound:
            logging.error("Worksheet 'Transaksi' not found")
            await update.message.reply_text("Worksheet 'Transaksi' tidak ditemukan. Pastikan spreadsheet memiliki sheet dengan nama 'Transaksi'.")
        except gspread.exceptions.APIError as e:
            logging.error(f"Google Sheets API error: {e}")
            await update.message.reply_text("Terjadi kesalahan saat mengakses Google Sheets. Coba lagi nanti.")
    except Exception as e:
        logging.error(f"Error in catat_transaksi: {e}", exc_info=True)
        await update.message.reply_text("Waduh, ada error saat mencatat. Coba lagi nanti.")

@restricted
async def laporan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        await update.message.reply_text("⏳ Sedang menyusun laporan arus kas...")
        
        sekarang = datetime.datetime.now()
        bulan_target, tahun_target = sekarang.month, sekarang.year

        try:
            sheet = spreadsheet.worksheet("Transaksi")
            data = sheet.get_all_records()

            if not data:
                await update.message.reply_text("Belum ada data transaksi.")
                return
        except gspread.exceptions.WorksheetNotFound:
            logging.error("Worksheet 'Transaksi' not found in laporan")
            await update.message.reply_text("Worksheet 'Transaksi' tidak ditemukan. Pastikan spreadsheet memiliki sheet dengan nama 'Transaksi'.")
            return
        except gspread.exceptions.APIError as e:
            logging.error(f"Google Sheets API error in laporan: {e}", exc_info=True)
            await update.message.reply_text("Terjadi kesalahan pada API Google Sheets. Coba lagi nanti.")
            return
        except Exception as e:
            logging.error(f"Error accessing worksheet in laporan: {e}", exc_info=True)
            await update.message.reply_text("Terjadi kesalahan saat mengakses data. Coba lagi nanti.")
            return

        df = pd.DataFrame(data)
        df['Jumlah'] = pd.to_numeric(df['Jumlah'], errors='coerce').fillna(0)
        df['Tanggal'] = pd.to_datetime(df['Tanggal'], errors='coerce')
        df.dropna(subset=['Tanggal'], inplace=True)

        tanggal_awal_bulan_ini = datetime.date(tahun_target, bulan_target, 1)
        df_sebelumnya = df[df['Tanggal'].dt.date < tanggal_awal_bulan_ini]
        pemasukan_sebelumnya = df_sebelumnya[df_sebelumnya['Tipe'] == 'Pemasukan']['Jumlah'].sum()
        pengeluaran_sebelumnya = df_sebelumnya[df_sebelumnya['Tipe'] == 'Pengeluaran']['Jumlah'].sum()
        saldo_awal = pemasukan_sebelumnya - pengeluaran_sebelumnya

        df_bulan_ini = df[(df['Tanggal'].dt.month == bulan_target) & (df['Tanggal'].dt.year == tahun_target)]
        pemasukan_bulan_ini = df_bulan_ini[df_bulan_ini['Tipe'] == 'Pemasukan']['Jumlah'].sum()
        pengeluaran_bulan_ini = df_bulan_ini[df_bulan_ini['Tipe'] == 'Pengeluaran']['Jumlah'].sum()
        saldo_akhir = saldo_awal + pemasukan_bulan_ini - pengeluaran_bulan_ini

        pengeluaran_per_kategori = df_bulan_ini[df_bulan_ini['Tipe'] == 'Pengeluaran'].groupby('Kategori')['Jumlah'].sum().sort_values(ascending=False)
        rincian_teks = ""
        if not pengeluaran_per_kategori.empty:
            rincian_teks = "\n\n*Rincian Pengeluaran Bulan Ini:*\n"
            for kategori, total in pengeluaran_per_kategori.items():
                rincian_teks += f"`#{kategori:<15} Rp {total:,.0f}`\n"

        nama_bulan_laporan = datetime.date(1900, bulan_target, 1).strftime('%B')
        pesan = (
            f"📊 *Laporan Arus Kas {nama_bulan_laporan} {tahun_target}*\n\n"
            f"💰 *Saldo Awal Bulan:*\n`Rp {saldo_awal:,.0f}`\n\n"
            f"➕ *Pemasukan Bulan Ini:*\n`Rp {pemasukan_bulan_ini:,.0f}`\n\n"
            f"➖ *Pengeluaran Bulan Ini:*\n`Rp {pengeluaran_bulan_ini:,.0f}`\n"
            f"----------------------------------\n"
            f"🏦 *SALDO AKHIR:*\n`Rp {saldo_akhir:,.0f}`"
            f"{rincian_teks}"
        )
        await update.message.reply_text(pesan, parse_mode='Markdown')
    except Exception as e:
        logging.error(f"Error in laporan: {e}", exc_info=True)
        await update.message.reply_text("Waduh, ada error saat membuat laporan. Coba lagi nanti.")

@restricted
async def compare_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        await update.message.reply_text("⏳ Sedang menyusun analisis perbandingan...")
        
        try:
            sheet = spreadsheet.worksheet("Transaksi")
            data = sheet.get_all_records()
            if not data:
                await update.message.reply_text("Belum ada data untuk dibandingkan.")
                return
        except gspread.exceptions.WorksheetNotFound:
            logging.error("Worksheet 'Transaksi' not found in compare_report")
            await update.message.reply_text("Worksheet 'Transaksi' tidak ditemukan. Pastikan spreadsheet memiliki sheet dengan nama 'Transaksi'.")
            return
        except Exception as e:
            logging.error(f"Error accessing worksheet in compare_report: {e}", exc_info=True)
            await update.message.reply_text("Terjadi kesalahan saat mengakses data. Coba lagi nanti.")
            return

        # Process data with pandas
        df = pd.DataFrame(data)
        df['Jumlah'] = pd.to_numeric(df['Jumlah'], errors='coerce').fillna(0)
        df['Tanggal'] = pd.to_datetime(df['Tanggal'], errors='coerce')
        df.dropna(subset=['Tanggal'], inplace=True)

        sekarang = datetime.datetime.now()
        bulan_ini, tahun_ini = sekarang.month, sekarang.year
        tanggal_awal_bulan_ini = datetime.date(tahun_ini, bulan_ini, 1)
        tanggal_akhir_bulan_lalu = tanggal_awal_bulan_ini - datetime.timedelta(days=1)
        bulan_lalu, tahun_lalu = tanggal_akhir_bulan_lalu.month, tanggal_akhir_bulan_lalu.year

        df_bulan_ini = df[(df['Tanggal'].dt.month == bulan_ini) & (df['Tanggal'].dt.year == tahun_ini)]
        df_bulan_lalu = df[(df['Tanggal'].dt.month == bulan_lalu) & (df['Tanggal'].dt.year == tahun_lalu)]

        pengeluaran_bulan_ini = df_bulan_ini[df_bulan_ini['Tipe'] == 'Pengeluaran']['Jumlah'].sum()
        pengeluaran_bulan_lalu = df_bulan_lalu[df_bulan_lalu['Tipe'] == 'Pengeluaran']['Jumlah'].sum()

        kat_ini = df_bulan_ini[df_bulan_ini['Tipe'] == 'Pengeluaran'].groupby('Kategori')['Jumlah'].sum().rename('Bulan Ini')
        kat_lalu = df_bulan_lalu[df_bulan_lalu['Tipe'] == 'Pengeluaran'].groupby('Kategori')['Jumlah'].sum().rename('Bulan Lalu')
        
        df_compare = pd.concat([kat_ini, kat_lalu], axis=1).fillna(0).sort_values(by='Bulan Ini', ascending=False)
        
        rincian_teks = "\n\n*Perbandingan per Kategori:*\n`Kategori      Bulan Ini vs Bulan Lalu`\n"
        for kategori, row in df_compare.iterrows():
            total_ini, total_lalu = row['Bulan Ini'], row['Bulan Lalu']
            selisih = total_ini - total_lalu
            emoji = "🔺" if selisih > 0 else ("🔻" if selisih < 0 else "➖")
            rincian_teks += f"`#{kategori:<12} Rp{int(total_ini):<8,} vs Rp{int(total_lalu):<8,}` {emoji}\n"
        
        nama_bulan_ini = datetime.date(1900, bulan_ini, 1).strftime('%B')
        nama_bulan_lalu = datetime.date(1900, bulan_lalu, 1).strftime('%B')

        pesan = (
            f"📈 *Analisis Pengeluaran*\n_{nama_bulan_ini} vs. {nama_bulan_lalu}_\n\n"
            f"*{nama_bulan_ini}:* `Rp {pengeluaran_bulan_ini:,.0f}`\n"
            f"*{nama_bulan_lalu}:* `Rp {pengeluaran_bulan_lalu:,.0f}`\n"
            f"{rincian_teks}"
        )
        await update.message.reply_text(pesan, parse_mode='Markdown')
    except Exception:
        traceback.print_exc()
        await update.message.reply_text("Waduh, ada error saat membuat perbandingan.")

# --- 5. BAGIAN WEBHOOK ---
@app.route('/webhook', methods=['POST'])
def webhook() -> str:
    try:
        async def process():
            try:
                update = Update.de_json(request.get_json(force=True), application.bot)
                await application.initialize()
                await application.process_update(update)
                await application.shutdown()
            except Exception as e:
                logging.error(f"Error processing update: {e}", exc_info=True)

        asyncio.run(process())
        return "OK"
    except Exception as e:
        logging.error(f"Webhook error: {e}", exc_info=True)
        return "Error", 500

@app.route('/')
def index():
    # Add health check information
    status = "OK" if gspread_client and spreadsheet else "ERROR: Google Sheets connection failed"
    version = "1.0.1"
    return f'Bot Keuangan Pribadi v{version} is running! Status: {status}'

# --- 6. PENDAFTARAN PERINTAH (HANDLER) ---
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("masuk", catat_transaksi))
application.add_handler(CommandHandler("keluar", catat_transaksi))
application.add_handler(CommandHandler("laporan", laporan))
application.add_handler(CommandHandler("compare", compare_report))

# --- 7. MAIN BLOCK ---
if __name__ == "__main__":
    # Setup logging
    setup_logging()
    logging.info("Starting Bot Keuangan Pribadi")
    
    # Run the Flask app
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
