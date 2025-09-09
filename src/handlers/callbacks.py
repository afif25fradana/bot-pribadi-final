import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup # type: ignore
from telegram.ext import ContextTypes # type: ignore
from . import commands
from ..utils.helpers import SecureLogger

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button presses from inline keyboards."""
    query = update.callback_query
    
    if not query:
        SecureLogger.warning("Received callback without query data")
        return
        
    await query.answer()
    callback_data = query.data
    
    try:
        if callback_data == "laporan":
            # Call the laporan function
            await commands.laporan(update, context)
            
        elif callback_data == "compare":
            # Call the compare_report function
            await commands.compare_report(update, context)
            
        elif callback_data == "tips":
            # Send usage tips
            keyboard = [
                [
                    InlineKeyboardButton("📊 Laporan", callback_data="laporan"),
                    InlineKeyboardButton("📈 Compare", callback_data="compare")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "💡 *Tips Penggunaan Bot*\n\n"
                "*Format Transaksi:*\n"
                "• `/masuk [jumlah] #[kategori] [deskripsi]`\n"
                "• `/keluar [jumlah] #[kategori] [deskripsi]`\n\n"
                "*Contoh:*\n"
                "• `/masuk 500000 #gaji Gaji bulan ini`\n"
                "• `/keluar 15000 #makan Beli nasi padang`\n\n"
                "*Kategori Populer:*\n"
                "`#gaji #bonus #makanan #transportasi #belanja #hiburan #tagihan #kesehatan`",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            SecureLogger.info("Tips message sent")
            
        elif callback_data == "info":
            # Send bot information
            keyboard = [
                [
                    InlineKeyboardButton("📊 Laporan", callback_data="laporan"),
                    InlineKeyboardButton("📈 Compare", callback_data="compare")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "ℹ️ *Tentang Bot Keuangan Pribadi*\n\n"
                "Bot ini membantu Anda mencatat dan menganalisis keuangan pribadi dengan mudah.\n\n"
                "*Fitur Utama:*\n"
                "• Pencatatan pemasukan dan pengeluaran\n"
                "• Laporan keuangan bulanan\n"
                "• Perbandingan dengan bulan sebelumnya\n"
                "• Analisis kategori pengeluaran\n\n"
                "*Versi:* 1.0.0\n"
                "*Dibuat oleh:* Noxara",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            SecureLogger.info("Info message sent")
            
    except Exception as e:
        SecureLogger.error(f"Error handling callback: {e}")
        await query.edit_message_text(
            "⚠️ *Error*\n\n"
            "Terjadi kesalahan saat memproses permintaan.",
            parse_mode='Markdown'
        )
