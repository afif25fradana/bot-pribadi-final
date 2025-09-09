import logging
import datetime
import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup # type: ignore
from telegram.ext import ContextTypes # type: ignore
from ..bot.decorators import restricted
from ..services.sheets import sheets_service
from ..utils.helpers import parse_message, format_currency, get_month_name, SecureLogger

@restricted
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message when the command /start is issued."""
    user_first_name = update.effective_user.first_name if update.effective_user else "User"
    
    # Create inline keyboard with buttons
    keyboard = [
        [
            InlineKeyboardButton("📊 Laporan", callback_data="laporan"),
            InlineKeyboardButton("📈 Compare", callback_data="compare")
        ],
        [
            InlineKeyboardButton("💡 Tips", callback_data="tips"),
            InlineKeyboardButton("ℹ️ Info", callback_data="info")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send welcome message with buttons
    await update.message.reply_text(
        f"Halo, {user_first_name}! 👋\n\n"
        "Selamat datang di *Bot Keuangan Pribadi*!\n\n"
        "*Contoh Perintah:*\n"
        "• /masuk 50000 #gaji Gajian bulan ini\n"
        "• /keluar 15000 #makan Beli nasi padang\n"
        "• /laporan\n"
        "• /compare\n\n"
        "Silakan pilih opsi di bawah:",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
    SecureLogger.info(f"User {user_first_name} started the bot")

@restricted
async def catat_transaksi(update: Update, context: ContextTypes.DEFAULT_TYPE, tipe: str):
    """Record a financial transaction."""
    if not update.message or not update.message.text:
        SecureLogger.warning("Received transaction command without message text")
        return
        
    # Parse the message
    jumlah, kategori, deskripsi = parse_message(update.message.text)
    
    if not jumlah:
        await update.message.reply_text(
            "❌ *Format Salah*\n\n"
            f"Format yang benar: /{tipe} [jumlah] #[kategori] [deskripsi]\n"
            f"Contoh: /{tipe} 50000 #gaji Gajian bulan ini",
            parse_mode='Markdown'
        )
        return
    
    # Get current date
    tanggal = datetime.datetime.now().strftime("%Y-%m-%d")
    
    try:
        # Get the worksheet
        worksheet = sheets_service.get_worksheet("Transaksi")
        if not worksheet:
            await update.message.reply_text(
                "⚠️ *Error*\n\n"
                "Worksheet 'Transaksi' tidak ditemukan.",
                parse_mode='Markdown'
            )
            return
            
        # Append the transaction
        row = [tanggal, jumlah, kategori, deskripsi, tipe]
        success = sheets_service.append_row("Transaksi", row)
        
        if not success:
            await update.message.reply_text(
                "⚠️ *Error*\n\n"
                "Gagal mencatat transaksi. Silakan coba lagi.",
                parse_mode='Markdown'
            )
            return
        
        # Create inline keyboard with buttons
        keyboard = [
            [
                InlineKeyboardButton("📊 Laporan", callback_data="laporan"),
                InlineKeyboardButton("📈 Compare", callback_data="compare")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send success message
        tipe_emoji = "💰" if tipe == "masuk" else "💸"
        await update.message.reply_text(
            f"{tipe_emoji} *Transaksi {tipe.capitalize()} Berhasil Dicatat*\n\n"
            f"*Jumlah:* {format_currency(jumlah)}\n"
            f"*Kategori:* {kategori}\n"
            f"*Deskripsi:* {deskripsi}\n"
            f"*Tanggal:* {tanggal}",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        SecureLogger.info(f"Transaction recorded: type={tipe}, category={kategori}")
        
    except Exception as e:
        SecureLogger.error(f"Error recording transaction: {e}")
        await update.message.reply_text(
            "⚠️ *Error*\n\n"
            "Terjadi kesalahan saat mencatat transaksi.",
            parse_mode='Markdown'
        )

@restricted
# Add this function to standardize date handling
def get_standardized_date(date_str=None):
    """
    Standardizes date handling with proper timezone support.
    If date_str is provided, parses it. Otherwise uses current date.
    Returns a datetime object with Asia/Jakarta timezone.
    """
    jakarta_tz = timezone(timedelta(hours=7))  # UTC+7 for Jakarta/Indonesia
    
    if date_str:
        try:
            # Try to parse the date string in various formats
            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d %B %Y"]:
                try:
                    parsed_date = datetime.strptime(date_str, fmt)
                    # Set time to beginning of day and apply timezone
                    return datetime(parsed_date.year, parsed_date.month, parsed_date.day, 
                                   tzinfo=jakarta_tz)
                except ValueError:
                    continue
            # If all formats fail, raise exception
            raise ValueError(f"Cannot parse date: {date_str}")
        except Exception as e:
            SecureLogger.error(f"Error parsing date: {e}")
            # Default to current date if parsing fails
            now = datetime.now(jakarta_tz)
            return datetime(now.year, now.month, now.day, tzinfo=jakarta_tz)
    else:
        # Use current date with Jakarta timezone
        now = datetime.now(jakarta_tz)
        return datetime(now.year, now.month, now.day, tzinfo=jakarta_tz)

@restricted
async def laporan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate a monthly financial report."""
    try:
        # Get user information for logging
        user = update.effective_user
        chat_id = update.effective_chat.id
        SecureLogger.info(f"User requested financial report")
        
        # Send loading message
        loading_message = await context.bot.send_message(
            chat_id=chat_id,
            text="⏳ Sedang menyiapkan laporan keuangan..."
        )
        
        # Get current date using standardized function
        current_date = get_standardized_date()
        current_month = current_date.month
        current_year = current_date.year
        
        # Format month name in Indonesian
        month_name = get_month_name(current_month)
        
        # Get the Google Sheets service
        sheets_service = GoogleSheetsService()
        if not sheets_service.is_connected():
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=loading_message.message_id,
                text="❌ Gagal terhubung ke Google Sheets. Coba lagi nanti."
            )
            return

        # Rest of the function remains the same
        # Get all transactions
        records = sheets_service.get_all_records("Transaksi")
        if not records:
            await loading_message.edit_text(
                "⚠️ *Data Tidak Ditemukan*\n\n"
                "Belum ada transaksi yang tercatat.",
                parse_mode='Markdown'
            )
            return
            
        # Convert to DataFrame
        df = pd.DataFrame(records)
        
        # Ensure date column is in correct format
        df['Tanggal'] = pd.to_datetime(df['Tanggal'], errors='coerce', format='%Y-%m-%d')
        
        # Filter for current month
        df_bulan_ini = df[
            (df['Tanggal'].dt.month == current_month) & 
            (df['Tanggal'].dt.year == current_year)
        ]
        
        if df_bulan_ini.empty:
            await loading_message.edit_text(
                f"⚠️ *Data Bulan {get_month_name(current_month)} {current_year} Tidak Ditemukan*\n\n"
                "Belum ada transaksi yang tercatat untuk bulan ini.",
                parse_mode='Markdown'
            )
            return
            
        # Calculate total income and expenses
        pemasukan = df_bulan_ini[df_bulan_ini['Tipe'] == 'masuk']['Jumlah'].sum()
        pengeluaran = df_bulan_ini[df_bulan_ini['Tipe'] == 'keluar']['Jumlah'].sum()
        
        # Calculate balance
        saldo_awal = 0  # This would ideally come from previous month's data
        saldo_akhir = saldo_awal + pemasukan - pengeluaran
        
        # Get expense breakdown by category
        if pengeluaran > 0:
            pengeluaran_by_kategori = df_bulan_ini[df_bulan_ini['Tipe'] == 'keluar'].groupby('Kategori')['Jumlah'].sum()
            pengeluaran_by_kategori = pengeluaran_by_kategori.sort_values(ascending=False)
            
            # Calculate percentages
            kategori_details = []
            for kategori, jumlah in pengeluaran_by_kategori.items():
                # Avoid division by zero
                percentage = (jumlah / pengeluaran * 100) if pengeluaran > 0 else 0
                kategori_details.append(f"• {kategori}: {format_currency(jumlah)} ({percentage:.1f}%)")
                
            kategori_text = "\n".join(kategori_details)
        else:
            kategori_text = "• Tidak ada pengeluaran bulan ini"
        
        # Create inline keyboard with buttons
        keyboard = [
            [
                InlineKeyboardButton("📈 Compare", callback_data="compare"),
                InlineKeyboardButton("💡 Tips", callback_data="tips")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send report
        await loading_message.edit_text(
            f"📊 *Laporan Keuangan {get_month_name(current_month)} {current_year}*\n\n"
            f"💰 *Pemasukan:* {format_currency(pemasukan)}\n"
            f"💸 *Pengeluaran:* {format_currency(pengeluaran)}\n"
            f"💼 *Saldo Akhir:* {format_currency(saldo_akhir)}\n\n"
            f"*Breakdown Pengeluaran:*\n{kategori_text}",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        SecureLogger.info(f"Financial report generated for {get_month_name(current_month)} {current_year}")
        
    except Exception as e:
        SecureLogger.error(f"Error generating report: {e}")
        await loading_message.edit_text(
            "⚠️ *Error*\n\n"
            "Terjadi kesalahan saat membuat laporan.",
            parse_mode='Markdown'
        )

@restricted
async def compare_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Compare financial reports between current and previous month."""
    try:
        # Get user information for logging
        user = update.effective_user
        chat_id = update.effective_chat.id
        SecureLogger.info(f"User requested comparison report")
        
        # Send loading message
        loading_message = await context.bot.send_message(
            chat_id=chat_id,
            text="⏳ Sedang menyiapkan laporan perbandingan..."
        )
        
        # Get current date using standardized function
        current_date = get_standardized_date()
        current_month = current_date.month
        current_year = current_date.year
        
        # Calculate previous month with proper year handling
        if current_month == 1:  # January
            prev_month = 12  # December
            prev_year = current_year - 1
        else:
            prev_month = current_month - 1
            prev_year = current_year
        
        # Format month names in Indonesian
        current_month_name = get_month_name(current_month)
        prev_month_name = get_month_name(prev_month)
        
        # Rest of the function remains the same
        # Get all transactions
        records = sheets_service.get_all_records("Transaksi")
        if not records:
            await loading_message.edit_text(
                "⚠️ *Data Tidak Ditemukan*\n\n"
                "Belum ada transaksi yang tercatat.",
                parse_mode='Markdown'
            )
            return
            
        # Convert to DataFrame
        df = pd.DataFrame(records)
        
        # Ensure date column is in correct format
        df['Tanggal'] = pd.to_datetime(df['Tanggal'], errors='coerce', format='%Y-%m-%d')
        
        # Filter for current and previous month
        df_bulan_ini = df[
            (df['Tanggal'].dt.month == current_month) & 
            (df['Tanggal'].dt.year == current_year)
        ]
        
        df_bulan_lalu = df[
            (df['Tanggal'].dt.month == prev_month) & 
            (df['Tanggal'].dt.year == prev_year)
        ]
        
        if df_bulan_ini.empty and df_bulan_lalu.empty:
            await loading_message.edit_text(
                "⚠️ *Data Tidak Ditemukan*\n\n"
                "Belum ada transaksi yang tercatat untuk bulan ini dan bulan lalu.",
                parse_mode='Markdown'
            )
            return
            
        # Calculate totals for current month
        pemasukan_bulan_ini = df_bulan_ini[df_bulan_ini['Tipe'] == 'masuk']['Jumlah'].sum() if not df_bulan_ini.empty else 0
        pengeluaran_bulan_ini = df_bulan_ini[df_bulan_ini['Tipe'] == 'keluar']['Jumlah'].sum() if not df_bulan_ini.empty else 0
        
        # Calculate totals for previous month
        pemasukan_bulan_lalu = df_bulan_lalu[df_bulan_lalu['Tipe'] == 'masuk']['Jumlah'].sum() if not df_bulan_lalu.empty else 0
        pengeluaran_bulan_lalu = df_bulan_lalu[df_bulan_lalu['Tipe'] == 'keluar']['Jumlah'].sum() if not df_bulan_lalu.empty else 0
        
        # Calculate percentage changes
        if pemasukan_bulan_lalu > 0:
            pemasukan_change = ((pemasukan_bulan_ini - pemasukan_bulan_lalu) / pemasukan_bulan_lalu) * 100
            pemasukan_change_text = f"{pemasukan_change:+.1f}%"
        else:
            pemasukan_change_text = "N/A"
            
        if pengeluaran_bulan_lalu > 0:
            pengeluaran_change = ((pengeluaran_bulan_ini - pengeluaran_bulan_lalu) / pengeluaran_bulan_lalu) * 100
            pengeluaran_change_text = f"{pengeluaran_change:+.1f}%"
        else:
            pengeluaran_change_text = "N/A"
            
        # Compare top expense categories
        kategori_bulan_ini = df_bulan_ini[df_bulan_ini['Tipe'] == 'keluar'].groupby('Kategori')['Jumlah'].sum().sort_values(ascending=False)
        kategori_bulan_lalu = df_bulan_lalu[df_bulan_lalu['Tipe'] == 'keluar'].groupby('Kategori')['Jumlah'].sum().sort_values(ascending=False)
        
        # Get top 3 categories from current month
        top_categories = kategori_bulan_ini.head(3).index.tolist()
        
        # Create comparison text
        comparison_details = []
        for kategori in top_categories:
            jumlah_bulan_ini = kategori_bulan_ini.get(kategori, 0)
            jumlah_bulan_lalu = kategori_bulan_lalu.get(kategori, 0)
            
            if jumlah_bulan_lalu > 0:
                change = ((jumlah_bulan_ini - jumlah_bulan_lalu) / jumlah_bulan_lalu) * 100
                change_text = f"{change:+.1f}%"
            else:
                change_text = "N/A"
                
            comparison_details.append(
                f"• {kategori}: {format_currency(jumlah_bulan_ini)} vs {format_currency(jumlah_bulan_lalu)} ({change_text})"
            )
            
        comparison_text = "\n".join(comparison_details) if comparison_details else "• Tidak ada data perbandingan"
        
        # Create inline keyboard with buttons
        keyboard = [
            [
                InlineKeyboardButton("📊 Laporan", callback_data="laporan"),
                InlineKeyboardButton("💡 Tips", callback_data="tips")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send comparison report
        await loading_message.edit_text(
            f"📈 *Perbandingan {get_month_name(current_month)} vs {get_month_name(prev_month)}*\n\n"
            f"💰 *Pemasukan:*\n{format_currency(pemasukan_bulan_ini)} vs {format_currency(pemasukan_bulan_lalu)} ({pemasukan_change_text})\n\n"
            f"💸 *Pengeluaran:*\n{format_currency(pengeluaran_bulan_ini)} vs {format_currency(pengeluaran_bulan_lalu)} ({pengeluaran_change_text})\n\n"
            f"*Top Kategori Pengeluaran:*\n{comparison_text}",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        SecureLogger.info(f"Comparison report generated for {get_month_name(current_month)} vs {get_month_name(prev_month)}")
        
    except Exception as e:
        SecureLogger.error(f"Error generating comparison report: {e}")
        await loading_message.edit_text(
            "⚠️ *Error*\n\n"
            "Terjadi kesalahan saat membuat perbandingan.",
            parse_mode='Markdown'
        )
