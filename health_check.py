#!/usr/bin/env python
"""
Enhanced Health Check Script for Bot Keuangan Pribadi v2.1.0
"""

import os
import json
import logging
import requests
import sys
import time
from datetime import datetime
from src.config import settings

# Setup enhanced logging
settings.setup_logging()

def print_header():
    """Print a nice header for the health check."""
    print("=" * 60)
    print("🏥 Noxara Finance Bot - HEALTH CHECK v2.1.0")
    print("=" * 60)
    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

def check_environment_variables():
    """Check that all required environment variables are set."""
    print("🔍 Checking Environment Variables...")
    try:
        settings.validate_config()
        print("  ✅ All required environment variables are set")
        return True
    except ValueError as e:
        print(f"  ❌ {e}")
        return False

def check_google_sheets_connection():
    """Check that we can connect to Google Sheets."""
    print("\n🔍 Checking Google Sheets Connection...")
    try:
        from src.services.sheets import sheets_service
        # Check if the service has connected successfully
        if sheets_service.client is not None and sheets_service.spreadsheet is not None:
            print("  ✅ Successfully connected to Google Sheets")
            return True
        else:
            print("  ❌ Failed to connect to Google Sheets")
            return False
    except Exception as e:
        print(f"  ❌ Error connecting to Google Sheets: {e}")
        return False

def check_telegram_bot():
    """Check that the Telegram bot token is valid."""
    print("\n🔍 Checking Telegram Bot Connection...")
    token = settings.TELEGRAM_TOKEN
    if not token:
        print("  ❌ TELEGRAM_TOKEN environment variable not set")
        return False
    
    try:
        response = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
        if response.status_code == 200 and response.json().get('ok'):
            bot_info = response.json()['result']
            print(f"  ✅ Bot Name: {bot_info.get('first_name', 'Unknown')}")
            return True
        else:
            print(f"  ❌ Invalid bot token. Response: {response.text}")
            return False
    except Exception as e:
        print(f"  ❌ Error connecting to Telegram: {e}")
        return False

def main():
    """Run all health checks."""
    print_header()
    
    checks = {
        "Environment Variables": check_environment_variables,
        "Google Sheets Connection": check_google_sheets_connection,
        "Telegram Bot": check_telegram_bot,
    }
    
    results = {name: func() for name, func in checks.items()}
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    print("📋 HEALTH CHECK SUMMARY REPORT")
    print("=" * 60)
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {name}")
    
    if all_passed:
        print("\n🎉 All checks passed! Bot is ready to run.")
    else:
        print("\n⚠️ Some checks failed. Please fix the issues.")
        
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
