#!/usr/bin/env python
"""
Enhanced Health Check Script for Bot Keuangan Pribadi v2.0.0
This script verifies that all required environment variables are set
and that connections to external services (Google Sheets, Telegram) are working.
"""

import os
import json
import logging
import requests
import sys
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Setup enhanced logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('health_check.log')
    ]
)

def print_header():
    """Print a nice header for the health check."""
    print("=" * 60)
    print("🏥 Noxara Finance Bot - HEALTH CHECK v2.0.0")
    print("=" * 60)
    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

def check_environment_variables():
    """Check that all required environment variables are set."""
    print("🔍 Checking Environment Variables...")
    
    required_vars = {
        'TELEGRAM_TOKEN': 'Telegram Bot Token',
        'GSPREAD_CREDENTIALS': 'Google Sheets Credentials (JSON)',
        'SPREADSHEET_NAME': 'Google Spreadsheet Name',
        'ALLOWED_USER_ID': 'Authorized Telegram User ID'
    }
    
    optional_vars = {
        'PORT': 'Web Server Port (default: 5000)'
    }
    
    missing_vars = []
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            print(f"  ❌ {var}: Missing")
            missing_vars.append(var)
        else:
            # Mask sensitive values
            if var == 'TELEGRAM_TOKEN':
                masked_value = f"{value[:10]}...{value[-4:]}" if len(value) > 14 else "***"
            elif var == 'GSPREAD_CREDENTIALS':
                masked_value = f"JSON ({len(value)} chars)"
            elif var == 'ALLOWED_USER_ID':
                masked_value = value
            else:
                masked_value = value
            print(f"  ✅ {var}: {masked_value}")
    
    print("\n📋 Optional Variables:")
    for var, description in optional_vars.items():
        value = os.getenv(var, 'Not Set')
        print(f"  ℹ️  {var}: {value}")
    
    if missing_vars:
        print(f"\n❌ Missing required variables: {', '.join(missing_vars)}")
        return False
    
    print("\n✅ All required environment variables are set")
    return True

def check_google_sheets_connection():
    """Check that we can connect to Google Sheets."""
    print("\n🔍 Checking Google Sheets Connection...")
    
    try:
        import gspread
        
        # Get credentials from environment variable
        creds_json = os.getenv('GSPREAD_CREDENTIALS')
        if not creds_json:
            print("  ❌ GSPREAD_CREDENTIALS environment variable not set")
            return False
        
        try:
            creds_dict = json.loads(creds_json)
            print("  ✅ Credentials JSON is valid")
        except json.JSONDecodeError as e:
            print(f"  ❌ Invalid JSON in GSPREAD_CREDENTIALS: {e}")
            return False
        
        # Connect to Google Sheets
        print("  🔄 Connecting to Google Sheets API...")
        client = gspread.service_account_from_dict(creds_dict)
        
        # Open the spreadsheet
        spreadsheet_name = os.getenv('SPREADSHEET_NAME', 'Catatan Keuangan')
        print(f"  🔄 Opening spreadsheet: {spreadsheet_name}")
        spreadsheet = client.open(spreadsheet_name)
        print(f"  ✅ Successfully opened spreadsheet: {spreadsheet.title}")
        
        # Check for required worksheet
        try:
            worksheet = spreadsheet.worksheet("Transaksi")
            print(f"  ✅ Found 'Transaksi' worksheet with {worksheet.row_count} rows")
            
            # Test read access
            headers = worksheet.row_values(1) if worksheet.row_count > 0 else []
            if headers:
                print(f"  ✅ Worksheet headers: {headers}")
            else:
                print("  ⚠️  Worksheet is empty")
                
            return True
            
        except gspread.exceptions.WorksheetNotFound:
            print("  ⚠️  'Transaksi' worksheet not found")
            print("  🔄 Attempting to create worksheet...")
            
            try:
                worksheet = spreadsheet.add_worksheet(title="Transaksi", rows="1000", cols="5")
                worksheet.append_row(["Tanggal", "Tipe", "Jumlah", "Kategori", "Deskripsi"])
                print("  ✅ Created 'Transaksi' worksheet with headers")
                return True
            except Exception as e:
                print(f"  ❌ Failed to create worksheet: {e}")
                return False
        
    except ImportError:
        print("  ❌ gspread library not installed")
        return False
    except Exception as e:
        print(f"  ❌ Error connecting to Google Sheets: {e}")
        return False

def check_telegram_bot():
    """Check that the Telegram bot token is valid."""
    print("\n🔍 Checking Telegram Bot Connection...")
    
    token = os.getenv('TELEGRAM_TOKEN')
    if not token:
        print("  ❌ TELEGRAM_TOKEN environment variable not set")
        return False
    
    try:
        print("  🔄 Validating bot token...")
        response = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
        
        if response.status_code == 200:
            bot_info = response.json()
            if bot_info.get('ok'):
                bot_data = bot_info['result']
                print(f"  ✅ Bot Name: {bot_data.get('first_name', 'Unknown')}")
                print(f"  ✅ Bot Username: @{bot_data.get('username', 'Unknown')}")
                print(f"  ✅ Bot ID: {bot_data.get('id', 'Unknown')}")
                print(f"  ✅ Can Join Groups: {bot_data.get('can_join_groups', False)}")
                print(f"  ✅ Can Read Messages: {bot_data.get('can_read_all_group_messages', False)}")
                return True
        
        print(f"  ❌ Invalid bot token. Response: {response.text}")
        return False
        
    except requests.exceptions.Timeout:
        print("  ❌ Request timeout - check internet connection")
        return False
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Network error: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Error connecting to Telegram: {e}")
        return False

def check_webhook_info():
    """Check webhook configuration."""
    print("\n🔍 Checking Webhook Configuration...")
    
    token = os.getenv('TELEGRAM_TOKEN')
    if not token:
        return False
    
    try:
        response = requests.get(f"https://api.telegram.org/bot{token}/getWebhookInfo", timeout=10)
        if response.status_code == 200:
            webhook_info = response.json()
            if webhook_info.get('ok'):
                result = webhook_info['result']
                webhook_url = result.get('url', '')
                
                if webhook_url:
                    print(f"  ✅ Webhook URL: {webhook_url}")
                    print(f"  ✅ Has Custom Certificate: {result.get('has_custom_certificate', False)}")
                    print(f"  ✅ Pending Updates: {result.get('pending_update_count', 0)}")
                    
                    last_error = result.get('last_error_message')
                    if last_error:
                        print(f"  ⚠️  Last Error: {last_error}")
                        print(f"  ⚠️  Error Date: {result.get('last_error_date', 'Unknown')}")
                else:
                    print("  ℹ️  No webhook URL configured (polling mode)")
                
                return True
        return False
    except Exception as e:
        print(f"  ❌ Error checking webhook: {e}")
        return False

def check_system_resources():
    """Check system resources and dependencies."""
    print("\n🔍 Checking System Resources...")
    
    try:
        import psutil
        
        # Memory usage
        memory = psutil.virtual_memory()
        print(f"  💾 Memory Usage: {memory.percent}% ({memory.used // (1024**2)} MB / {memory.total // (1024**2)} MB)")
        
        # Disk usage
        disk = psutil.disk_usage('/')
        print(f"  💿 Disk Usage: {disk.percent}% ({disk.used // (1024**3)} GB / {disk.total // (1024**3)} GB)")
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        print(f"  🖥️  CPU Usage: {cpu_percent}%")
        
    except ImportError:
        print("  ℹ️  psutil not available - skipping system resource check")
    except Exception as e:
        print(f"  ⚠️  Error checking system resources: {e}")
    
    # Check Python version
    print(f"  🐍 Python Version: {sys.version.split()[0]}")
    
    # Check required modules
    required_modules = ['flask', 'pandas', 'gspread', 'telegram', 'requests']
    print("  📦 Required Modules:")
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"    ✅ {module}")
        except ImportError:
            print(f"    ❌ {module} - Not installed")
    
    return True

def run_performance_test():
    """Run a simple performance test."""
    print("\n🔍 Running Performance Test...")
    
    try:
        # Test JSON parsing performance
        start_time = time.time()
        test_data = {"test": "data", "numbers": list(range(1000))}
        for _ in range(100):
            json.dumps(test_data)
            json.loads(json.dumps(test_data))
        json_time = time.time() - start_time
        print(f"  ⚡ JSON Processing: {json_time:.3f}s (100 iterations)")
        
        # Test pandas performance if available
        try:
            import pandas as pd
            start_time = time.time()
            df = pd.DataFrame({'A': range(1000), 'B': range(1000, 2000)})
            df['C'] = df['A'] + df['B']
            result = df.groupby('C').sum()
            pandas_time = time.time() - start_time
            print(f"  ⚡ Pandas Processing: {pandas_time:.3f}s (1000 rows)")
        except ImportError:
            print("  ℹ️  Pandas not available - skipping pandas test")
        
        return True
    except Exception as e:
        print(f"  ❌ Performance test error: {e}")
        return False

def generate_summary_report(results):
    """Generate a summary report of all checks."""
    print("\n" + "=" * 60)
    print("📋 HEALTH CHECK SUMMARY REPORT")
    print("=" * 60)
    
    total_checks = len(results)
    passed_checks = sum(1 for result in results.values() if result)
    failed_checks = total_checks - passed_checks
    
    print(f"📊 Total Checks: {total_checks}")
    print(f"✅ Passed: {passed_checks}")
    print(f"❌ Failed: {failed_checks}")
    print(f"📈 Success Rate: {(passed_checks/total_checks)*100:.1f}%")
    
    print("\n📋 Detailed Results:")
    for check_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {check_name}")
    
    if failed_checks == 0:
        print("\n🎉 All checks passed! Bot is ready to run.")
        return True
    else:
        print(f"\n⚠️  {failed_checks} check(s) failed. Please fix the issues before running the bot.")
        return False

def main():
    """Run all health checks."""
    print_header()
    
    checks = {
        "Environment Variables": check_environment_variables,
        "Google Sheets Connection": check_google_sheets_connection,
        "Telegram Bot": check_telegram_bot,
        "Webhook Configuration": check_webhook_info,
        "System Resources": check_system_resources,
        "Performance Test": run_performance_test
    }
    
    results = {}
    
    for name, check_func in checks.items():
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"\n❌ Error running {name}: {e}")
            results[name] = False
    
    # Generate summary report
    all_passed = generate_summary_report(results)
    
    # Save results to log file
    try:
        with open('health_check_results.json', 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'results': results,
                'summary': {
                    'total_checks': len(results),
                    'passed_checks': sum(1 for r in results.values() if r),
                    'failed_checks': sum(1 for r in results.values() if not r),
                    'success_rate': (sum(1 for r in results.values() if r) / len(results)) * 100
                }
            }, f, indent=2)
        print(f"\n💾 Results saved to health_check_results.json")
    except Exception as e:
        print(f"\n⚠️  Could not save results: {e}")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
