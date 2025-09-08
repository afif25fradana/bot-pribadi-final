#!/usr/bin/env python
# tests/webhook_test.py
"""
Test script to verify webhook functionality.

This script tests the webhook endpoint by sending a mock Telegram update.
"""

import sys
import json
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path to import app modules
sys.path.append('..')

class WebhookTest(unittest.TestCase):
    """Test case for webhook functionality."""
    
    def setUp(self):
        """Set up the test environment."""
        # Import Flask app
        import sys
        import os
        # Add project root to path
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        # Import the Flask app directly
        from app import app
        
        # Create a test client
        self.app = app.test_client()
        
        # Mock the bot
        self.mock_bot = MagicMock()
        
        # Set up a mock Telegram update
        self.update_data = {
            "update_id": 123456789,
            "message": {
                "message_id": 1,
                "from": {
                    "id": 123456789,
                    "first_name": "Test",
                    "username": "test_user"
                },
                "chat": {
                    "id": 123456789,
                    "first_name": "Test",
                    "username": "test_user",
                    "type": "private"
                },
                "date": 1631234567,
                "text": "/start"
            }
        }
    
    @patch('app.web.routes._bot')
    def test_webhook_endpoint(self, mock_bot):
        """Test that the webhook endpoint processes updates correctly."""
        # Configure the mock bot
        mock_bot_instance = MagicMock()
        mock_bot_instance.process_update = MagicMock()
        mock_bot.__bool__.return_value = True  # Make the bot truthy
        mock_bot.bot = mock_bot_instance
        
        # Send a POST request to the webhook endpoint
        response = self.app.post(
            '/webhook',
            data=json.dumps(self.update_data),
            content_type='application/json'
        )
        
        # Assert that the response is successful
        self.assertEqual(response.status_code, 200)
        
        # Verify that process_update was called
        mock_bot.process_update.assert_called_once()
    
    def test_health_endpoint(self):
        """Test that the health endpoint returns OK."""
        # Send a GET request to the health endpoint
        response = self.app.get('/health')
        
        # Assert that the response is successful and contains 'OK'
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.decode('utf-8'), 'OK')
    
    def test_index_endpoint(self):
        """Test that the index endpoint returns a valid response."""
        # Send a GET request to the index endpoint
        response = self.app.get('/')
        
        # Assert that the response is successful
        self.assertEqual(response.status_code, 200)
        
        # Parse the JSON response
        data = json.loads(response.data.decode('utf-8'))
        
        # Assert that the response contains the expected fields
        self.assertIn('status', data)
        self.assertIn('message', data)
        self.assertEqual(data['status'], 'online')

if __name__ == '__main__':
    # Run the tests
    unittest.main()