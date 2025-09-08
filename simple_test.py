#!/usr/bin/env python
# simple_test.py
"""
Simple test script to verify application functionality.

This script tests the application initialization and WSGI setup
without using the unittest framework.
"""

import sys
import os
import logging
from unittest.mock import MagicMock, patch
from google.oauth2.service_account import Credentials

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_app_initialization():
    """Test that the application initializes correctly."""
    logging.info("Testing application initialization...")
    
    # Add project root to path
    sys.path.insert(0, os.path.dirname(__file__))
    
    # Set mock environment variables
    os.environ['TELEGRAM_TOKEN'] = 'test_token'
    os.environ['ALLOWED_USER_ID'] = '123456789'
    os.environ['GSPREAD_CREDENTIALS'] = '{"type": "service_account", "project_id": "test-project", "private_key_id": "test-key-id", "private_key": "test-key", "client_email": "test@example.com", "token_uri": "https://oauth2.googleapis.com/token"}'
    os.environ['WEBHOOK_URL'] = 'https://test.example.com/webhook'
    os.environ['SPREADSHEET_ID'] = 'test_spreadsheet_id'
    
    try:
        # Import get_main function
        from app import get_main
        from app.config import APP_NAME, APP_VERSION
        
        # Get main function
        main_func = get_main()
        
        # Create mock objects
        mock_client = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_client.open_by_key.return_value = mock_spreadsheet
        
        # Mock dependencies with simpler approach
        with patch('app.config.validate_environment', return_value=True), \
             patch('google.oauth2.service_account.Credentials.from_service_account_info', return_value=MagicMock()), \
             patch('gspread.authorize', return_value=mock_client), \
             patch('app.database.sheets.initialize_gspread', side_effect=lambda: True), \
             patch('app.database.sheets.get_spreadsheet', return_value=mock_spreadsheet), \
             patch('telegram.ext.ApplicationBuilder'), \
             patch('app.web.routes.setup_webhook', return_value=True), \
             patch('app.app.run'):
            # Run main function
            result = main_func()
        
        if result:
            logging.info("✅ Application initialization test passed!")
            return True
        else:
            logging.error("❌ Application initialization test failed!")
            return False
    except Exception as e:
        logging.error(f"❌ Error during app initialization test: {e}")
        return False

def test_wsgi_initialization():
    """Test that the WSGI application initializes correctly."""
    logging.info("Testing WSGI initialization...")
    
    # Add project root to path
    sys.path.insert(0, os.path.dirname(__file__))
    
    # Set mock environment variables
    os.environ['TELEGRAM_TOKEN'] = 'test_token'
    os.environ['ALLOWED_USER_ID'] = '123456789'
    os.environ['GSPREAD_CREDENTIALS'] = '{"type": "service_account", "project_id": "test-project", "private_key_id": "test-key-id", "private_key": "test-key", "client_email": "test@example.com", "token_uri": "https://oauth2.googleapis.com/token"}'
    os.environ['WEBHOOK_URL'] = 'https://test.example.com/webhook'
    os.environ['SPREADSHEET_ID'] = 'test_spreadsheet_id'
    
    try:
        # Create mock objects
        mock_client = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_client.open_by_key.return_value = mock_spreadsheet
        
        # Mock dependencies with simpler approach
        with patch('google.oauth2.service_account.Credentials.from_service_account_info', return_value=MagicMock()), \
             patch('gspread.authorize', return_value=mock_client), \
             patch('app.database.sheets.initialize_gspread', side_effect=lambda: True), \
             patch('app.database.sheets.get_spreadsheet', return_value=mock_spreadsheet), \
             patch('telegram.ext.ApplicationBuilder'), \
             patch('app.web.routes.setup_webhook', return_value=True), \
             patch('app.app.run'):
            # Import wsgi module
            import wsgi
            flask_app = wsgi.app
        
        # Check that the app exists
        if flask_app:
            logging.info("✅ WSGI initialization test passed!")
            return True
        else:
            logging.error("❌ WSGI initialization test failed!")
            return False
    except Exception as e:
        logging.error(f"❌ Error during WSGI initialization test: {e}")
        return False

if __name__ == "__main__":
    print("Running simple tests to verify application functionality...")
    
    # Run tests
    app_init_result = test_app_initialization()
    wsgi_init_result = test_wsgi_initialization()
    
    # Count passed and failed tests
    passed = 0
    failed = 0
    
    if app_init_result:
        passed += 1
    else:
        failed += 1
        
    if wsgi_init_result:
        passed += 1
    else:
        failed += 1
    
    # Print summary
    logging.info(f"Tests passed: {passed}")
    logging.info(f"Tests failed: {failed}")
    
    if failed > 0:
        print("\n❌ Some tests failed. Please check the output above for details.")
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")
        sys.exit(0)