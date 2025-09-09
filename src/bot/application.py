import logging
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler # type: ignore
from ..config import settings
from ..handlers import commands, callbacks
from ..utils.helpers import SecureLogger

def create_application():
    """Create and configure the Telegram bot application."""
    try:
        # Initialize the application with the token from settings
        application = ApplicationBuilder().token(settings.TELEGRAM_TOKEN).build()
        
        # Register command handlers
        application.add_handler(CommandHandler("start", commands.start))
        application.add_handler(CommandHandler("masuk", lambda update, context: commands.catat_transaksi(update, context, "masuk")))
        application.add_handler(CommandHandler("keluar", lambda update, context: commands.catat_transaksi(update, context, "keluar")))
        application.add_handler(CommandHandler("laporan", commands.laporan))
        application.add_handler(CommandHandler("compare", commands.compare_report))
        
        # Register callback query handler for button interactions
        application.add_handler(CallbackQueryHandler(callbacks.button_handler))
        
        SecureLogger.info("Application created and handlers registered successfully")
        return application
    except Exception as e:
        SecureLogger.error(f"Error creating application: {e}")
        raise
