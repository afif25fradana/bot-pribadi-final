import logging
from functools import wraps
from telegram import Update # type: ignore
from telegram.ext import ContextTypes # type: ignore
from ..config import settings
from ..services.sheets import sheets_service
from ..utils.helpers import SecureLogger

def restricted(func):
    """Decorator to restrict bot access to authorized users only."""
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if not update.effective_user:
            SecureLogger.warning("Received an update without an effective user.")
            return

        user_id = update.effective_user.id
        
        if user_id != settings.ALLOWED_USER_ID:
            SecureLogger.warning(f"Unauthorized access denied for user {user_id}")
            if update.message: # Check if message exists before replying
                await update.message.reply_text(
                    "🚫 *Akses Ditolak*\n\n"
                    "Maaf, kamu tidak memiliki akses ke bot ini.",
                    parse_mode='Markdown'
                )
            return
            
        if not sheets_service.is_connected():
            SecureLogger.error("Google Sheets connection not available")
            if update.message: # Check if message exists before replying
                await update.message.reply_text(
                    "⚠️ *Koneksi Bermasalah*\n\n"
                    "Koneksi ke spreadsheet gagal.",
                    parse_mode='Markdown'
                )
            return
            
        return await func(update, context, *args, **kwargs)
    return wrapped
