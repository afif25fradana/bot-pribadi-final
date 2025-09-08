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

# Import routes setelah app dibuat untuk menghindari circular import
from app.web.routes import init_web