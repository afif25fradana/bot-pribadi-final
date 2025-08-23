import os
import json
import pandas as pd
import datetime
import traceback
from functools import wraps
from flask import Flask, request, Response
import gspread
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio
from typing import Union, Tuple, cast

# --- 1. KONFIGURASI ---
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
GSPREAD_CREDENTIALS_JSON = os.environ.get('GSPREAD_CREDENTIALS')
SPREADSHEET_NAME = os.environ.get('SPREADSHEET_NAME', 'Catatan Keuangan')

_allowed_user_id_str = os.environ.get('ALLOWED_USER_ID')
ALLOWED_USER_ID: int | None = None # Initialize with explicit type hint
if isinstance(_allowed_user_id_str, str): # Use isinstance for clearer type narrowing
    try:
        ALLOWED_USER_ID = int(cast(str, _allowed_user_id_str)) # type: ignore[arg-type] # Use cast for explicit type assertion
    except ValueError: # TypeError is not expected if it's already a string
        ALLOWED_USER_ID = None

# --- 2. INISIALISASI APLIKASI ---
app = Flask(__name__)
if TELEGRAM_TOKEN is None:
    raise ValueError("TELEGRAM_TOKEN environment variable is not set.")
telegram_token_str: str = cast(str, TELEGRAM_TOKEN) # type: ignore[assignment] # Use cast for explicit type assertion
application = Application.builder().token(telegram_token_str).build()
# The Application should not be explicitly started/stopped here when Flask is handling webhooks.
# Its process_update method will be called directly by the webhook route.

# --- 3. FUNGSI BANTUAN & DECORATOR ---
def restricted(func):
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if update.effective_user is None:
            return # Cannot proceed without effective_user
        if update.message is None:
            return # Cannot proceed without message

        # Now update.effective_user and update.message are guaranteed not to be None
        if ALLOWED_USER_ID is None or update.effective_user.id != ALLOWED_USER_ID: # type: ignore[union-attr]
            await update.message.reply_text("Maaf, Anda tidak diizinkan menggunakan bot ini.") # type: ignore[union-attr]
            return
        return await func(update, context, *args, **kwargs)
    return wrapped

def get_client():
    if GSPREAD_CREDENTIALS_JSON is None:
        raise ValueError("GSPREAD_CREDENTIALS environment variable is not set.")
    creds_dict = json.loads(GSPREAD_CREDENTIALS_JSON) # Pylance should now infer GSPREAD_CREDENTIALS_JSON as str
    return gspread.service_account_from_dict(creds_dict)

def parse_message(text: str | None):
    if text is None:
        return None, None, None
    assert text is not None # Ensure text is not None for split()
    parts = text.split() # type: ignore[union-attr]
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

# --- 4. DEFINISI FUNGSI-FUNGSI BOT ---
@restricted
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_user is not None
    assert update.message is not None
    user_name = update.effective_user.first_name # type: ignore[union-attr]
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
    await update.message.reply_text(pesan, parse_mode='Markdown') # type: ignore[union-attr]

@restricted
async def catat_transaksi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.message is not None
    assert update.message.text is not None
    try:
        command = update.message.text.split()[0].lower() # type: ignore[union-attr]
        tipe = "Pemasukan" if command == "/masuk" else "Pengeluaran"
        emoji = "🟢" if tipe == "Pemasukan" else "🔴"
        jumlah, kategori, deskripsi = parse_message(update.message.text)
        if jumlah is None:
            await update.message.reply_text("Format salah. Contoh: `/keluar 50000 #makanan`") # type: ignore[union-attr]
            return
        tanggal = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_row = [tanggal, tipe, jumlah, kategori, deskripsi]
        client = get_client()
        spreadsheet = client.open(SPREADSHEET_NAME)
        target_sheet = spreadsheet.worksheet("Transaksi")
        target_sheet.append_row(new_row)
        await update.message.reply_text(f"{emoji} Dicatat: *{tipe}* `Rp {jumlah:,.0f}` untuk kategori `#{kategori}`.", parse_mode='Markdown') # type: ignore[union-attr]
    except Exception:
        traceback.print_exc()
        await update.message.reply_text("Waduh, ada error saat mencatat.") # type: ignore[union-attr]

@restricted
async def laporan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.message is not None
    try:
        await update.message.reply_text("⏳ Sedang menyusun laporan arus kas...") # type: ignore[union-attr]
        
        sekarang = datetime.datetime.now()
        bulan_target, tahun_target = sekarang.month, sekarang.year

        client = get_client()
        spreadsheet = client.open(SPREADSHEET_NAME)
        sheet = spreadsheet.worksheet("Transaksi")
        data = sheet.get_all_records()

        if not data:
            await update.message.reply_text("Belum ada data transaksi.") # type: ignore[union-attr]
            return

        df = pd.DataFrame(data)
        df['Jumlah'] = pd.to_numeric(df['Jumlah'], errors='coerce')
        df['Jumlah'] = df['Jumlah'].fillna(0) # Ensure fillna is called on a Series
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
        await update.message.reply_text(pesan, parse_mode='Markdown') # type: ignore[union-attr]
    except Exception:
        traceback.print_exc()
        await update.message.reply_text("Waduh, ada error saat membuat laporan.") # type: ignore[union-attr]

@restricted
async def compare_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.message is not None
    try:
        await update.message.reply_text("⏳ Sedang menyusun analisis perbandingan...") # type: ignore[union-attr]
        client = get_client()
        spreadsheet = client.open(SPREADSHEET_NAME)
        sheet = spreadsheet.worksheet("Transaksi")
        data = sheet.get_all_records()
        if not data:
            await update.message.reply_text("Belum ada data untuk dibandingkan.") # type: ignore[union-attr]
            return

        df = pd.DataFrame(data)
        df['Jumlah'] = pd.to_numeric(df['Jumlah'], errors='coerce')
        df['Jumlah'] = df['Jumlah'].fillna(0) # Ensure fillna is called on a Series
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
        
        df_compare = pd.concat([kat_ini, kat_lalu], axis=1).fillna(0)
        df_compare['Bulan Ini'] = df_compare['Bulan Ini'].astype(int)
        df_compare['Bulan Lalu'] = df_compare['Bulan Lalu'].astype(int)
        df_compare = df_compare.sort_values(by='Bulan Ini', ascending=False)
        
        rincian_teks = "\n\n*Perbandingan per Kategori:*\n`Kategori      Bulan Ini vs Bulan Lalu`\n"
        for kategori, row in df_compare.iterrows():
            total_ini = int(row['Bulan Ini']) # type: ignore
            total_lalu = int(row['Bulan Lalu']) # type: ignore
            selisih = total_ini - total_lalu
            emoji = "🔺" if selisih > 0 else ("🔻" if selisih < 0 else "➖")
            rincian_teks += f"`#{kategori:<12} Rp{total_ini:<8,} vs Rp{total_lalu:<8,}` {emoji}\n"
        
        nama_bulan_ini = datetime.date(1900, bulan_ini, 1).strftime('%B')
        nama_bulan_lalu = datetime.date(1900, bulan_lalu, 1).strftime('%B')

        pesan = (
            f"📈 *Analisis Pengeluaran*\n_{nama_bulan_ini} vs. {nama_bulan_lalu}_\n\n"
            f"*{nama_bulan_ini}:* `Rp {pengeluaran_bulan_ini:,.0f}`\n"
            f"*{nama_bulan_lalu}:* `Rp {pengeluaran_bulan_lalu:,.0f}`\n"
            f"{rincian_teks}"
        )
        await update.message.reply_text(pesan, parse_mode='Markdown') # type: ignore[union-attr]
    except Exception:
        traceback.print_exc()
        await update.message.reply_text("Waduh, ada error saat membuat perbandingan.") # type: ignore[union-attr]

# --- 5. BAGIAN WEBHOOK ---
@app.route('/webhook', methods=['POST'])
async def webhook() -> Union[str, Response, Tuple[str, int]]:
    try:
        update = Update.de_json(request.get_json(force=True), application.bot)
        await application.process_update(update)
        return "OK"
    except Exception:
        traceback.print_exc()
        return "Error", 500

@app.route('/')
def index():
    return 'Bot Keuangan Pribadi is running!'

# --- 6. PENDAFTARAN PERINTAH (HANDLER) ---
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("masuk", catat_transaksi))
application.add_handler(CommandHandler("keluar", catat_transaksi))
application.add_handler(CommandHandler("laporan", laporan))
application.add_handler(CommandHandler("compare", compare_report))

# --- 7. SHUTDOWN HOOK (Optional, for graceful shutdown) ---
# Removed as it conflicts with Flask/Gunicorn lifecycle
