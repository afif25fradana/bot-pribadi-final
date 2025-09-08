# wsgi.py
"""
WSGI entry point for the application.

This file exposes the Flask application for WSGI servers like Gunicorn.
"""

import sys
import os

# Ensure the current directory is in the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the Flask app from the app package
from app import app

# For production deployment, the bot initialization will be handled by the main application
# This file only needs to expose the Flask app for the WSGI server

# Export the Flask app for WSGI servers
# No need to initialize as it's already done in app.py