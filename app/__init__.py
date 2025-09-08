# app/__init__.py
"""
Package utama aplikasi Bot Keuangan Pribadi.

Package ini berisi modul-modul untuk menangani bot Telegram,
interaksi dengan database, dan endpoint web.
"""

import logging
from flask import Flask
from app.config import setup_logging

# Setup logging saat package diimpor
setup_logging()

logging.info("✅ Aplikasi Bot Keuangan Pribadi dimulai")

# Inisialisasi Flask app untuk diakses oleh WSGI server
app = Flask(__name__)

# Setup path for importing main function when needed
import sys
import os

# Add project root to path to import main from app.py
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Define a function to get the main function to avoid circular imports
def get_main():
    """Get the main function from the root app.py"""
    import importlib.util
    import sys
    
    # Import main function from the root app.py file
    spec = importlib.util.spec_from_file_location("app_main", 
                                               os.path.join(os.path.dirname(os.path.dirname(__file__)), "app.py"))
    app_main = importlib.util.module_from_spec(spec)
    sys.modules["app_main"] = app_main
    spec.loader.exec_module(app_main)
    
    # Return the main function
    return app_main.main

# Import routes setelah app dibuat untuk menghindari circular import
from app.web import routes