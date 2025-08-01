# main.py (Versi Final - Laporan Saldo Awal + Analisis)
import os
import json
import pandas as pd
import datetime
import traceback
from functools import wraps
from flask import Flask, request
import gspread
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio

# --- 1. KONFIGURASI ---
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
GSPREAD_CREDENTIALS_JSON = os.environ.get('GSPREAD_CREDENTIALS')
SPREADSHEET_NAME = os.environ.get('SPREADSHEET_NAME', 'Catatan Keuangan')
try:
    ALLOWED_USER_ID = int(os.environ.get('ALLOWED_USER_ID'))
except (TypeError, ValueError):
    ALLOWED_USER_ID = None

# --- 2. INISIALISASI APLIKASI ---
app = Flask(__name__)
application = Application.builder().token(TELEGRAM_TOKEN).build()

# --- 3. FUNGSI BANTUAN & DECORATOR ---
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
    except (ValueError, IndexError): return None, None, None
    kategori = "uncategorized"
    deskripsi_parts = []
    for part in parts[2:]:
        if part.startswith('#'):
            kategori = part[1:].lower()
        else:
            deskripsi_parts.append(part)
    deskripsi = " ".join(deskripsi_parts) if deskripsi_parts else "-"
    return jumlah, kategori, deskripsi

# --- 4. DEFINISI FUNGSI-FUNGSI BOT ---
@restricted
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pesan = (
        "Bot Keuangan v5.2 (Lengkap) Siap!\n\n"
        "Fitur Utama:\n"
        "✅ `/masuk` & `/keluar`\n"
        "📊 `/laporan` - Laporan arus kas bulan ini (dengan saldo awal)\n"
        "📈 `/compare` - Bandingkan pengeluaran dengan bulan lalu"
    )
    await update.message.reply_text(pesan, parse_mode='Markdown')

@restricted
async def catat_transaksi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        command = update.message.text.split()[0].lower()
        tipe = "Pemasukan" if command == "/masuk" else "Pengeluaran"
        jumlah, kategori, deskripsi = parse_message(update.message.text)
        if jumlah is None:
            await update.message.reply_text("Format salah. Contoh: `/keluar 50000 #makanan`")
            return
        tanggal = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_row = [tanggal, tipe, jumlah, kategori, deskripsi]
        client = get_client()
        spreadsheet = client.open(SPREADSHEET_NAME)
        target_sheet = spreadsheet.worksheet("Transaksi")
        target_sheet.append_row(new_row)
        await update.message.reply_text(f"✅ Dicatat: {tipe} {jumlah} untuk kategori #{kategori}")
    except Exception:
        traceback.print_exc()
        await update.message.reply_text("Waduh, ada error saat mencatat.")

@restricted
async def laporan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Membuat laporan arus kas lengkap dengan saldo awal."""
    try:
        await update.message.reply_text("⏳ Sedang menyusun laporan arus kas...")
        
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
        df.dropna(subset=['Tanggal'], inplace=True)

        # Hitung Saldo Awal
        tanggal_awal_bulan_ini = datetime.date(tahun_target, bulan_target, 1)
        df_sebelumnya = df[df['Tanggal'].dt.date < tanggal_awal_bulan_ini]
        pemasukan_sebelumnya = df_sebelumnya[df_sebelumnya['Tipe'] == 'Pemasukan']['Jumlah'].sum()
        pengeluaran_sebelumnya = df_sebelumnya[df_sebelumnya['Tipe'] == 'Pengeluaran']['Jumlah'].sum()
        saldo_awal = pemasukan_sebelumnya - pengeluaran_sebelumnya

        # Transaksi Bulan Ini
        df_bulan_ini = df[(df['Tanggal'].dt.month == bulan_target) & (df['Tanggal'].dt.year == tahun_target)]
        pemasukan_bulan_ini = df_bulan_ini[df_bulan_ini['Tipe'] == 'Pemasukan']['Jumlah'].sum()
        pengeluaran_bulan_ini = df_bulan_ini[df_bulan_ini['Tipe'] == 'Pengeluaran']['Jumlah'].sum()
        saldo_akhir = saldo_awal + pemasukan_bulan_ini - pengeluaran_bulan_ini

        # Rincian Pengeluaran Bulan Ini
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
        traceback.print_exc()
        await update.message.reply_text("Waduh, ada error saat membuat laporan.")

@restricted
async def compare_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        await update.message.reply_text("⏳ Sedang menyusun analisis perbandingan...")
        client = get_client()
        spreadsheet = client.open(SPREADSHEET_NAME)
        sheet = spreadsheet.worksheet("Transaksi")
        data = sheet.get_all_records()
        if not data:
            await update.message.reply_text("Belum ada data untuk dibandingkan.")
            return

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
            emoji = "🔺" if selisih > 0 else ("🔻" if selisih < 0 else "")
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

# --- 6. PENDAFTARAN PERINTAH (HANDLER) ---
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("masuk", catat_transaksi))
application.add_handler(CommandHandler("keluar", catat_transaksi))
application.add_handler(CommandHandler("laporan", laporan))
application.add_handler(CommandHandler("compare", compare_report))

