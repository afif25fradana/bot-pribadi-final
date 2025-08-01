# main.py (Versi Final dengan Saldo Awal)
import gspread
import os
import json
import pandas as pd
import datetime
import traceback
from functools import wraps
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio

# --- KONFIGURASI ---
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
GSPREAD_CREDENTIALS_JSON = os.environ.get('GSPREAD_CREDENTIALS')
SPREADSHEET_NAME = os.environ.get('SPREADSHEET_NAME', 'Catatan Keuangan')
try:
    ALLOWED_USER_ID = int(os.environ.get('ALLOWED_USER_ID'))
except (TypeError, ValueError):
    ALLOWED_USER_ID = None

app = Flask(__name__)
application = Application.builder().token(TELEGRAM_TOKEN).build()

# --- DECORATOR & FUNGSI BANTUAN ---
def restricted(func):
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if update.effective_user.id != ALLOWED_USER_ID: return
        return await func(update, context, *args, **kwargs)
    return wrapped

def get_client():
    creds_dict = json.loads(GSPREAD_CREDENTIALS_JSON)
    return gspread.service_account_from_dict(creds_dict)

def parse_message(text):
    parts = text.split()
    try:
        jumlah = abs(int(parts[1]))
    except (ValueError, IndexError):
        return None, None, None
    kategori = "uncategorized"
    deskripsi_parts = []
    for part in parts[2:]:
        if part.startswith('#'):
            kategori = part[1:].lower()
        else:
            deskripsi_parts.append(part)
    deskripsi = " ".join(deskripsi_parts) if deskripsi_parts else "-"
    return jumlah, kategori, deskripsi

# --- FUNGSI-FUNGSI BOT ---
@restricted
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pesan = (
        "Bot Keuangan v5.0 (Final) Siap!\n\n"
        "Laporan sekarang menyertakan Saldo Awal dari bulan sebelumnya."
    )
    await update.message.reply_text(pesan, parse_mode='Markdown')

@restricted
async def catat_transaksi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Fungsi ini tidak berubah
    try:
        command = update.message.text.split()[0].lower()
        tipe = "Pemasukan" if command == "/masuk" else "Pengeluaran"
        jumlah, kategori, deskripsi = parse_message(update.message.text)
        if jumlah is None:
            await update.message.reply_text("Format salah.")
            return
        tanggal = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_row = [tanggal, tipe, jumlah, kategori, deskripsi]
        client = get_client()
        spreadsheet = client.open(SPREADSHEET_NAME)
        target_sheet = spreadsheet.worksheet("Transaksi")
        target_sheet.append_row(new_row)
        await update.message.reply_text(f"✅ Dicatat: {tipe} {jumlah} untuk #{kategori}")
    except Exception:
        print("--- ERROR DI FUNGSI catat_transaksi ---")
        traceback.print_exc()
        await update.message.reply_text("Waduh, ada error saat mencatat.")

@restricted
async def laporan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Membuat laporan arus kas lengkap dengan saldo awal."""
    try:
        await update.message.reply_text("⏳ Sedang menyusun laporan arus kas...")
        
        # Logika untuk menentukan bulan & tahun target (bisa ditambahkan lagi jika perlu)
        sekarang = datetime.datetime.now()
        bulan_target, tahun_target = sekarang.month, sekarang.year

        client = get_client()
        spreadsheet = client.open(SPREADSHEET_NAME)
        sheet = spreadsheet.worksheet("Transaksi")
        data = sheet.get_all_records()

        if not data:
            await update.message.reply_text("Belum ada data transaksi.")
            return

        df = pd.DataFrame(data)
        df['Jumlah'] = pd.to_numeric(df['Jumlah'], errors='coerce').fillna(0)
        df['Tanggal'] = pd.to_datetime(df['Tanggal'], errors='coerce')
        df.dropna(subset=['Tanggal'], inplace=True) # Hapus baris dengan tanggal tidak valid

        # --- LOGIKA BARU: HITUNG SALDO AWAL ---
        # Tentukan bulan dan tahun sebelumnya
        tanggal_awal_bulan_ini = datetime.date(tahun_target, bulan_target, 1)
        
        # Filter semua transaksi SEBELUM bulan ini
        df_sebelumnya = df[df['Tanggal'].dt.date < tanggal_awal_bulan_ini]
        
        pemasukan_sebelumnya = df_sebelumnya[df_sebelumnya['Tipe'] == 'Pemasukan']['Jumlah'].sum()
        pengeluaran_sebelumnya = df_sebelumnya[df_sebelumnya['Tipe'] == 'Pengeluaran']['Jumlah'].sum()
        saldo_awal = pemasukan_sebelumnya - pengeluaran_sebelumnya
        # --- AKHIR LOGIKA BARU ---

        # Filter transaksi HANYA untuk bulan ini
        df_bulan_ini = df[(df['Tanggal'].dt.month == bulan_target) & (df['Tanggal'].dt.year == tahun_target)]

        pemasukan_bulan_ini = df_bulan_ini[df_bulan_ini['Tipe'] == 'Pemasukan']['Jumlah'].sum()
        pengeluaran_bulan_ini = df_bulan_ini[df_bulan_ini['Tipe'] == 'Pengeluaran']['Jumlah'].sum()
        
        saldo_akhir = saldo_awal + pemasukan_bulan_ini - pengeluaran_bulan_ini

        # Rincian pengeluaran per kategori
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

    except Exception:
        print("--- ERROR DI FUNGSI laporan ---")
        traceback.print_exc()
        await update.message.reply_text("Waduh, ada error saat membuat laporan.")

    # ... (sisa kode webhook dan main program tidak berubah) ...
    
    # --- BAGIAN WEBHOOK ---
@app.route('/webhook', methods=['POST'])
def webhook() -> str:
    """Menangani update dari Telegram dengan lifecycle yang benar."""
    async def process():
        update = Update.de_json(request.get_json(force=True), application.bot)
        await application.initialize()
        await application.process_update(update)
        await application.shutdown()

    asyncio.run(process())
    return "OK"

@app.route('/')
def index():
    return 'Bot Keuangan Pribadi is running!'

# --- MAIN PROGRAM ---
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("masuk", catat_transaksi))
application.add_handler(CommandHandler("keluar", catat_transaksi))
application.add_handler(CommandHandler("laporan", laporan))
application.add_handler(CommandHandler("compare", compare_report))
