import asyncio
import logging
from flask import Flask, request, jsonify # type: ignore
from telegram import Update # type: ignore
from src.config import settings
from src.bot.application import create_application

# Initialize Flask app
app = Flask(__name__)

# Setup logging
settings.setup_logging()

# Create Telegram application
application = create_application()

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming webhook requests from Telegram."""
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

@app.route('/')
def index():
    """Health check endpoint with enhanced information."""
    from src.services.sheets import sheets_service
    
    sheets_status = "✅ Connected" if sheets_service.is_connected() else "❌ Disconnected"
    
    bot_info = {
        "name": "Noxara Finance Bot",
        "version": "2.1.0",
        "creator": "@Afif_Fradana",
        "status": "🟢 Running",
        "google_sheets": sheets_status
    }
    return jsonify(bot_info)

@app.route('/health')
def health():
    """Simple health check endpoint."""
    return jsonify({"status": "healthy"})

if __name__ == "__main__":
    try:
        settings.validate_config()
        logging.info("🚀 Starting Noxara Finance Bot v2.1.0 in production mode")
        # Force debug to False for production
        app.run(host=settings.HOST, port=settings.PORT, debug=False)
    except ValueError as e:
        logging.critical(f"❌ Bot failed to start: {e}")
        exit(1)
