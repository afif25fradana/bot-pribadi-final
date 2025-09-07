#!/usr/bin/env python
"""
Health check script for Bot Keuangan Pribadi
This script verifies that all required environment variables are set
and that connections to external services (Google Sheets) are working.
"""

import os
import json
import logging
import requests
import sys
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def check_environment_variables():
    """Check that all required environment variables are set."""
    required_vars = [
        'TELEGRAM_TOKEN',
        'GSPREAD_CREDENTIALS',
        'SPREADSHEET_NAME',
        'ALLOWED_USER_ID'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logging.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    logging.info("All required environment variables are set")
    return True

def check_google_sheets_connection():
    """Check that we can connect to Google Sheets."""
    try:
        import gspread
        from oauth2client.service_account import ServiceAccountCredentials
        
        # Get credentials from environment variable
        creds_json = os.getenv('GSPREAD_CREDENTIALS')
        if not creds_json:
            logging.error("GSPREAD_CREDENTIALS environment variable not set")
            return False
        
        try:
            creds_dict = json.loads(creds_json)
        except json.JSONDecodeError:
            logging.error("GSPREAD_CREDENTIALS_JSON is not valid JSON")
            return False
        
        # Connect to Google Sheets
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # Open the spreadsheet
        spreadsheet_id = os.getenv('SPREADSHEET_ID')
        if not spreadsheet_id:
            logging.error("SPREADSHEET_ID environment variable not set")
            return False
        
        spreadsheet = client.open_by_key(spreadsheet_id)
        
        # Try to access the Transaksi worksheet
        try:
            worksheet = spreadsheet.worksheet("Transaksi")
            logging.info(f"Successfully connected to Google Sheets and accessed 'Transaksi' worksheet")
            return True
        except gspread.exceptions.WorksheetNotFound:
            logging.error("'Transaksi' worksheet not found in the spreadsheet")
            return False
        
    except Exception as e:
        logging.error(f"Error connecting to Google Sheets: {e}")
        return False

def check_telegram_bot():
    """Check that the Telegram bot token is valid."""
    token = os.getenv('TELEGRAM_TOKEN')
    if not token:
        logging.error("TELEGRAM_TOKEN environment variable not set")
        return False
    
    try:
        response = requests.get(f"https://api.telegram.org/bot{token}/getMe")
        if response.status_code == 200:
            bot_info = response.json()
            if bot_info.get('ok'):
                logging.info(f"Successfully connected to Telegram bot: @{bot_info['result']['username']}")
                return True
        
        logging.error(f"Invalid Telegram bot token: {response.text}")
        return False
    except Exception as e:
        logging.error(f"Error connecting to Telegram: {e}")
        return False

def check_webhook_url():
    """Check if a webhook URL is set for the bot."""
    token = os.getenv('TELEGRAM_TOKEN')
    if not token:
        return False
    
    try:
        response = requests.get(f"https://api.telegram.org/bot{token}/getWebhookInfo")
        if response.status_code == 200:
            webhook_info = response.json()
            if webhook_info.get('ok'):
                webhook_url = webhook_info['result'].get('url')
                if webhook_url:
                    logging.info(f"Webhook URL is set to: {webhook_url}")
                    return True
                else:
                    logging.warning("No webhook URL is set for the bot")
        return False
    except Exception as e:
        logging.error(f"Error checking webhook URL: {e}")
        return False

def main():
    """Run all health checks."""
    logging.info("Starting health check for Bot Keuangan Pribadi")
    
    checks = [
        ("Environment Variables", check_environment_variables),
        ("Google Sheets Connection", check_google_sheets_connection),
        ("Telegram Bot", check_telegram_bot),
        ("Webhook URL", check_webhook_url)
    ]
    
    all_passed = True
    
    for name, check_func in checks:
        logging.info(f"Checking {name}...")
        if check_func():
            logging.info(f"✅ {name} check passed")
        else:
            logging.error(f"❌ {name} check failed")
            all_passed = False
    
    if all_passed:
        logging.info("All health checks passed!")
        return 0
    else:
        logging.error("Some health checks failed. See logs for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())