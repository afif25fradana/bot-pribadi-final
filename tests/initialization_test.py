#!/usr/bin/env python
# tests/initialization_test.py
"""
Test script to verify application initialization.

This script tests the initialization process without actually starting the server.
"""

import sys
import logging
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path to import app modules
sys.path.append('..')

class InitializationTest(unittest.TestCase):
    """Test case for application initialization."""
    
    @patch('app.app.run')
    @patch('app.web.routes.setup_webhook')
    @patch('app.bot.setup_bot')
    @patch('app.database.sheets.initialize_gspread')
    @patch('app.config.validate_environment')
    def test_initialization(self, mock_validate, mock_gspread, mock_setup_bot, 
                           mock_setup_webhook, mock_app_run):
        """Test that the application initializes correctly."""
        # Configure mocks to return success
        mock_validate.return_value = True
        mock_gspread.return_value = True
        mock_setup_webhook.return_value = True
        
        # Import main function after mocks are set up
        import sys
        import os
        # Add project root to path
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        # Import the main function directly from app.py
        from app import main
        
        # Run the main function
        result = main()
        
        # Assert that initialization was successful
        self.assertTrue(result, "Initialization should return True on success")
        
        # Verify that all expected functions were called
        mock_validate.assert_called_once()
        mock_gspread.assert_called_once()
        mock_setup_bot.assert_called_once()
        mock_setup_webhook.assert_called_once()
        mock_app_run.assert_called_once()
    
    @patch('app.config.validate_environment')
    def test_initialization_fails_on_invalid_env(self, mock_validate):
        """Test that initialization fails when environment validation fails."""
        # Configure mock to return failure
        mock_validate.return_value = False
        
        # Import main function after mock is set up
        import sys
        import os
        # Add project root to path
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        # Import the main function directly from app.py
        from app import main
        
        # Run the main function
        result = main()
        
        # Assert that initialization failed
        self.assertFalse(result, "Initialization should return False when environment validation fails")
        
        # Verify that validate_environment was called
        mock_validate.assert_called_once()

if __name__ == '__main__':
    # Configure logging to suppress output during tests
    logging.basicConfig(level=logging.CRITICAL)
    
    # Run the tests
    unittest.main()