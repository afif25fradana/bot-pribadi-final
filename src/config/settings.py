import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from ..utils.helpers import SecureLogger

# Load environment variables
load_dotenv()

# Telegram settings
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID", 0))

# Google Sheets settings
GOOGLE_SHEETS_CREDENTIALS = os.getenv("GOOGLE_SHEETS_CREDENTIALS") or os.getenv("GSPREAD_CREDENTIALS")
GOOGLE_SHEETS_SPREADSHEET_NAME = os.getenv("GOOGLE_SHEETS_SPREADSHEET_NAME") or os.getenv("SPREADSHEET_NAME")

# Web server settings
PORT = int(os.getenv("PORT", 8000))
HOST = os.getenv("HOST", "0.0.0.0")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Logging settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR = os.getenv("LOG_DIR", "logs")

def setup_logging():
    """Set up logging configuration."""
    # Create logs directory if it doesn't exist
    log_dir = Path(LOG_DIR)
    log_dir.mkdir(exist_ok=True)
    
    # Set up logging
    log_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "bot.log"),
            logging.StreamHandler()
        ]
    )
    
    # Reduce noise from external libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)
    logging.getLogger("gspread").setLevel(logging.WARNING)
    
    SecureLogger.info("Logging configured successfully")

def validate_config():
    """Validate required configuration variables."""
    required_vars = {
        "TELEGRAM_TOKEN": TELEGRAM_TOKEN,
        "ALLOWED_USER_ID": ALLOWED_USER_ID,
        "GOOGLE_SHEETS_CREDENTIALS": GOOGLE_SHEETS_CREDENTIALS,
        "GOOGLE_SHEETS_SPREADSHEET_NAME": GOOGLE_SHEETS_SPREADSHEET_NAME
    }
    
    missing_vars = [var for var, value in required_vars.items() if not value]
    
    if missing_vars:
        SecureLogger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False
        
    return True
