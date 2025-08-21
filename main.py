import os
import json
import pandas as pd
import datetime
from functools import wraps
from flask import Flask, request, Response # Added Response
import gspread
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio
import logging
import calendar # Added for month names

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- 1. KONFIGURASI ---
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
GSPREAD_CREDENTIALS_JSON = os.environ.get('GSPREAD_CREDENTIALS')
SPREADSHEET_NAME = os.environ.get('SPREADSHEET_NAME', 'Catatan Keuangan')
ALLOWED_USER_ID = None
try:
    allowed_id_str = os.environ.get('ALLOWED_USER_ID')
    if allowed_id_str is not None:
        ALLOWED_USER_ID = int(allowed_id_str)
        if ALLOWED_USER_ID == 0: # Added explicit check for 0 if it's a placeholder
            logger.warning("ALLOWED_USER_ID is set to 0, which might not be a valid user ID. Bot will be restricted to no one.")
            ALLOWED_USER_ID = None
    else:
        logger.warning("ALLOWED_USER_ID environment variable is not set. Bot will be restricted to no one.")
except (TypeError, ValueError):
    logger.warning("ALLOWED_USER_ID environment variable is not a valid integer. Bot will be restricted to no one.", exc_info=True)
    ALLOWED_USER_ID = None

# --- 2. INISIALISASI APLIKASI ---
app = Flask(__name__)
application = Application.builder().token(TELEGRAM_TOKEN).build()

# --- 3. FUNGSI BANTUAN & DECORATOR ---
def restricted(func):
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if ALLOWED_USER_ID is None:
            logger.warning("ALLOWED_USER_ID is not set. Bot will not respond to any user.")
            return # No one allowed if ID is None
        if update.effective_user.id != ALLOWED_USER_ID:
            logger.info(f"Unauthorized access attempt by user ID: {update.effective_user.id}")
            return
        return await func(update, context, *args, **kwargs)
    return wrapped

def get_client() -> gspread.Client:
    if GSPREAD_CREDENTIALS_JSON is None:
        logger.error("GSPREAD_CREDENTIALS environment variable is not set.")
        raise ValueError("GSPREAD_CREDENTIALS environment variable is not set.")
    try:
        creds_dict = json.loads(GSPREAD_CREDENTIALS_JSON)
        return gspread.service_account_from_dict(creds_dict)
    except json.JSONDecodeError:
        logger.error("GSPREAD_CREDENTIALS_JSON is not a valid JSON string.", exc_info=True)
        raise ValueError("GSPREAD_CREDENTIALS_JSON is not a valid JSON string.")
    except Exception as e:
        logger.error("Error initializing gspread client: %s", e, exc_info=True)
        raise RuntimeError(f"Failed to initialize gspread client: {e}")

def parse_message(text: str) -> tuple[int | None, str | None, str | None]:
    parts = text.split()
    try:
        jumlah = abs(int(parts[1]))
    except (ValueError, IndexError):
        logger.warning("Failed to parse amount from message: %s", text)
        return None, None, None
    kategori = "uncategorized"
    deskripsi_parts: list[str] = []
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
            await update.message.reply_text("Format salah. Contoh: `/keluar 50000 #makanan`")
            return
        tanggal = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_row = [tanggal, tipe, jumlah, kategori, deskripsi]
        
        client = get_client()
        spreadsheet = client.open(SPREADSHEET_NAME)
        target_sheet = spreadsheet.worksheet("Transaksi")
        target_sheet.append_row(new_row)
        await update.message.reply_text(f"{emoji} Dicatat: *{tipe}* `Rp {jumlah:,.0f}` untuk kategori `#{kategori}`.", parse_mode='Markdown')
    except gspread.exceptions.SpreadsheetNotFound:
        logger.error("Spreadsheet '%s' not found.", SPREADSHEET_NAME, exc_info=True)
        await update.message.reply_text(
            f"Waduh, spreadsheet '{SPREADSHEET_NAME}' tidak ditemukan. "
            "Pastikan nama spreadsheet di konfigurasi bot (`SPREADSHEET_NAME`) sudah benar "
            "dan bot memiliki akses 'Editor' ke spreadsheet tersebut."
        )
    except gspread.exceptions.APIError as e:
        logger.error("Google Sheets API error during transaction logging: %s", e, exc_info=True)
        await update.message.reply_text(
            "Waduh, ada masalah dengan Google Sheets API saat mencatat. "
            "Ini mungkin karena kredensial tidak valid atau batasan API. "
            "Coba periksa konfigurasi `GSPREAD_CREDENTIALS` Anda."
        )
    except (ValueError, RuntimeError) as e: # Catch errors from get_client specifically
        logger.error("Configuration error in catat_transaksi: %s", e, exc_info=True)
        await update.message.reply_text(
            f"Waduh, ada masalah konfigurasi bot: {e}. "
            "Pastikan `GSPREAD_CREDENTIALS` dan `SPREADSHEET_NAME` sudah diatur dengan benar."
        )
    except Exception as e:
        logger.error("Unexpected error in catat_transaksi: %s", e, exc_info=True)
        await update.message.reply_text(
            "Waduh, ada error tak terduga saat mencatat transaksi. "
            "Silakan coba lagi atau hubungi admin jika masalah berlanjut."
        )

@restricted
async def laporan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
        # Validate columns before accessing
        required_cols = ['Jumlah', 'Tanggal', 'Tipe', 'Kategori']
        if not all(col in df.columns for col in required_cols):
            missing_cols = [col for col in required_cols if col not in df.columns]
            logger.error("Missing required columns in spreadsheet data: %s", missing_cols)
            await update.message.reply_text(f"Waduh, data spreadsheet tidak lengkap. Kolom yang hilang: {', '.join(missing_cols)}.")
            return

        # Ensure 'Jumlah' column is numeric and handle NaNs
        df['Jumlah'] = pd.to_numeric(df['Jumlah'], errors='coerce').fillna(0).astype(float)
        # Ensure 'Tanggal' column is datetime and handle NaNs
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

        nama_bulan_laporan = calendar.month_name[bulan_target]
        
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
    except gspread.exceptions.SpreadsheetNotFound:
        logger.error("Spreadsheet '%s' not found.", SPREADSHEET_NAME, exc_info=True)
        await update.message.reply_text(
            f"Waduh, spreadsheet '{SPREADSHEET_NAME}' tidak ditemukan. "
            "Pastikan nama spreadsheet di konfigurasi bot (`SPREADSHEET_NAME`) sudah benar "
            "dan bot memiliki akses 'Editor' ke spreadsheet tersebut."
        )
    except gspread.exceptions.APIError as e:
        logger.error("Google Sheets API error during report generation: %s", e, exc_info=True)
        await update.message.reply_text(
            "Waduh, ada masalah dengan Google Sheets API saat membuat laporan. "
            "Ini mungkin karena kredensial tidak valid atau batasan API. "
            "Coba periksa konfigurasi `GSPREAD_CREDENTIALS` Anda."
        )
    except (ValueError, RuntimeError) as e: # Catch errors from get_client specifically
        logger.error("Configuration error in laporan: %s", e, exc_info=True)
        await update.message.reply_text(
            f"Waduh, ada masalah konfigurasi bot: {e}. "
            "Pastikan `GSPREAD_CREDENTIALS` dan `SPREADSHEET_NAME` sudah diatur dengan benar."
        )
    except Exception as e:
        logger.error("Unexpected error in laporan: %s", e, exc_info=True)
        await update.message.reply_text(
            "Waduh, ada error tak terduga saat membuat laporan. "
            "Silakan coba lagi atau hubungi admin jika masalah berlanjut."
        )

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
        # Validate columns before accessing
        required_cols = ['Jumlah', 'Tanggal', 'Tipe', 'Kategori']
        if not all(col in df.columns for col in required_cols):
            missing_cols = [col for col in required_cols if col not in df.columns]
            logger.error("Missing required columns in spreadsheet data: %s", missing_cols)
            await update.message.reply_text(f"Waduh, data spreadsheet tidak lengkap. Kolom yang hilang: {', '.join(missing_cols)}.")
            return

        # Ensure 'Jumlah' column is numeric and handle NaNs
        df['Jumlah'] = pd.to_numeric(df['Jumlah'], errors='coerce').fillna(0).astype(float)
        # Ensure 'Tanggal' column is datetime and handle NaNs
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

        kat_ini = df_bulan_ini[df_bulan_ini['Tipe'] == 'Pengeluaran']['Jumlah'].groupby(df_bulan_ini['Kategori']).sum().rename('Bulan Ini').astype(float)
        kat_lalu = df_bulan_lalu[df_bulan_lalu['Tipe'] == 'Pengeluaran']['Jumlah'].groupby(df_bulan_lalu['Kategori']).sum().rename('Bulan Lalu').astype(float)
        
        df_compare = pd.concat([kat_ini, kat_lalu], axis=1).fillna(0).sort_values(by='Bulan Ini', ascending=False)
        
        rincian_teks = "\n\n*Perbandingan per Kategori:*\n`Kategori      Bulan Ini vs Bulan Lalu`\n"
        for kategori, row in df_compare.iterrows():
            total_ini: float = float(row['Bulan Ini']) # type: ignore
            total_lalu: float = float(row['Bulan Lalu']) # type: ignore
            selisih: float = total_ini - total_lalu
            emoji = "🔺" if selisih > 0 else ("🔻" if selisih < 0 else "➖")
            rincian_teks += f"`#{kategori:<12} Rp{int(total_ini):<8,} vs Rp{int(total_lalu):<8,}` {emoji}\n"
        
        nama_bulan_ini = calendar.month_name[bulan_ini]
        nama_bulan_lalu = calendar.month_name[bulan_lalu]

        pesan = (
            f"📈 *Analisis Pengeluaran*\n_{nama_bulan_ini} vs. {nama_bulan_lalu}_\n\n"
            f"*{nama_bulan_ini}:* `Rp {pengeluaran_bulan_ini:,.0f}`\n"
            f"*{nama_bulan_lalu}:* `Rp {pengeluaran_bulan_lalu:,.0f}`\n"
            f"{rincian_teks}"
        )
        await update.message.reply_text(pesan, parse_mode='Markdown')
    except gspread.exceptions.SpreadsheetNotFound:
        logger.error("Spreadsheet '%s' not found.", SPREADSHEET_NAME, exc_info=True)
        await update.message.reply_text(
            f"Waduh, spreadsheet '{SPREADSHEET_NAME}' tidak ditemukan. "
            "Pastikan nama spreadsheet di konfigurasi bot (`SPREADSHEET_NAME`) sudah benar "
            "dan bot memiliki akses 'Editor' ke spreadsheet tersebut."
        )
    except gspread.exceptions.APIError as e:
        logger.error("Google Sheets API error during comparison report generation: %s", e, exc_info=True)
        await update.message.reply_text(
            "Waduh, ada masalah dengan Google Sheets API saat membuat perbandingan. "
            "Ini mungkin karena kredensial tidak valid atau batasan API. "
            "Coba periksa konfigurasi `GSPREAD_CREDENTIALS` Anda."
        )
    except (ValueError, RuntimeError) as e: # Catch errors from get_client specifically
        logger.error("Configuration error in compare_report: %s", e, exc_info=True)
        await update.message.reply_text(
            f"Waduh, ada masalah konfigurasi bot: {e}. "
            "Pastikan `GSPREAD_CREDENTIALS` dan `SPREADSHEET_NAME` sudah diatur dengan benar."
        )
    except Exception as e:
        logger.error("Unexpected error in compare_report: %s", e, exc_info=True)
        await update.message.reply_text(
            "Waduh, ada error tak terduga saat membuat perbandingan. "
            "Silakan coba lagi atau hubungi admin jika masalah berlanjut."
        )

# --- 5. BAGIAN WEBHOOK ---
@app.route('/webhook', methods=['POST'])
async def webhook() -> Response:
    """Handle incoming Telegram webhook updates."""
    try:
        update = Update.de_json(request.get_json(force=True), application.bot)
        await application.process_update(update)
        return Response("OK", status=200)
    except Exception as e:
        logger.error("Error processing webhook update: %s", e, exc_info=True)
        return Response("Error", status=500)

@app.route('/')
def index():
    return 'Bot Keuangan Pribadi is running!'

# --- 6. PENDAFTARAN PERINTAS (HANDLER) ---
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("masuk", catat_transaksi))
application.add_handler(CommandHandler("keluar", catat_transaksi))
application.add_handler(CommandHandler("laporan", laporan))
application.add_handler(CommandHandler("compare", compare_report))

# --- 7. INITIALIZE BOT APPLICATION (for Gunicorn/production) ---
# This block ensures the bot application is initialized when the Flask app starts.
# For Gunicorn, this code runs once per worker process.
# The `application.initialize()` is an async function, so it needs to be awaited.
# If Gunicorn is running with a synchronous worker, this will cause issues.
# It's recommended to use an async worker for Gunicorn (e.g., `gunicorn --worker-class uvicorn.workers.UvicornWorker main:app`).
# Alternatively, for a more robust setup, consider using `python-telegram-bot`'s `run_webhook`
# which handles the Flask integration more seamlessly, or a separate thread for the bot's event loop.
# For this fix, we assume an async-compatible Gunicorn worker.
async def init_application():
    await application.initialize()
    logger.info("Telegram bot application initialized.")

# Run the initialization when the module is loaded.
# This is a common pattern for global async setup in Flask apps with async workers.
# It relies on the event loop being available when the worker starts.
# If not, a more explicit startup hook (e.g., with `flask-executor` or a custom WSGI server hook)
# might be needed.
try:
    asyncio.get_event_loop().run_until_complete(init_application())
except RuntimeError:
    # If an event loop is already running (e.g., in some Gunicorn configurations),
    # we can try to create a task. This is a common workaround but can be fragile.
    # The ideal solution is a proper async worker setup for Gunicorn.
    asyncio.create_task(init_application())
except Exception as e:
    logger.critical("Failed to initialize Telegram bot application: %s", e, exc_info=True)
