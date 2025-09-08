# app/database/sheets.py
"""
Modul untuk menangani interaksi dengan Google Sheets.

Modul ini berisi fungsi-fungsi untuk menginisialisasi koneksi ke Google Sheets,
mengakses worksheet, dan melakukan operasi CRUD pada data.
"""

import os
import json
import logging
import gspread
from google.oauth2.service_account import Credentials
from app.config import GSPREAD_CREDENTIALS

# Get SPREADSHEET_ID from environment variable
import os
SPREADSHEET_ID = os.environ.get('SPREADSHEET_ID')

# Variabel global untuk menyimpan koneksi
_client = None
_spreadsheet = None

def get_spreadsheet():
    """
    Mendapatkan objek spreadsheet yang sudah diinisialisasi.
    
    Returns:
        gspread.Spreadsheet: Objek spreadsheet jika berhasil, None jika gagal.
    """
    global _spreadsheet
    
    # Periksa apakah spreadsheet sudah diinisialisasi
    if _spreadsheet is None:
        if not initialize_gspread():
            return None
    
    return _spreadsheet

def initialize_gspread():
    """
    Menginisialisasi koneksi ke Google Sheets dengan penanganan error yang lebih baik.
    
    Returns:
        bool: True jika berhasil, False jika gagal.
    """
    global _client, _spreadsheet
    
    try:
        # Periksa apakah kredensial sudah ada
        if not GSPREAD_CREDENTIALS:
            logging.error("❌ Kredensial Google Sheets tidak ditemukan")
            return False
            
        if not SPREADSHEET_ID:
            logging.error("❌ ID Spreadsheet tidak ditemukan")
            return False
        
        # Coba parse kredensial JSON
        try:
            credentials_info = json.loads(GSPREAD_CREDENTIALS)
        except json.JSONDecodeError as e:
            logging.error(f"❌ Format kredensial JSON tidak valid: {e}")
            return False
        
        # Buat objek kredensial
        try:
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            credentials = Credentials.from_service_account_info(credentials_info, scopes=scopes)
            _client = gspread.authorize(credentials)
        except Exception as e:
            logging.error(f"❌ Gagal mengotorisasi kredensial: {e}")
            return False
        
        # Buka spreadsheet
        try:
            _spreadsheet = _client.open_by_key(SPREADSHEET_ID)
            logging.info("✅ Berhasil terhubung ke Google Sheets")
            return True
        except gspread.exceptions.SpreadsheetNotFound:
            logging.error(f"❌ Spreadsheet dengan ID {SPREADSHEET_ID} tidak ditemukan")
            return False
        except gspread.exceptions.APIError as e:
            logging.error(f"❌ API Error: {e}")
            return False
            
    except Exception as e:
        logging.error(f"❌ Kesalahan tidak terduga saat menginisialisasi gspread: {e}")
        return False

def get_worksheet(worksheet_name):
    """
    Mendapatkan worksheet berdasarkan nama.
    
    Args:
        worksheet_name (str): Nama worksheet yang akan diakses.
        
    Returns:
        gspread.Worksheet: Objek worksheet jika berhasil, None jika gagal.
    """
    global _spreadsheet
    
    try:
        # Periksa apakah spreadsheet sudah diinisialisasi
        if _spreadsheet is None:
            if not initialize_gspread():
                return None
        
        # Coba dapatkan worksheet
        try:
            worksheet = _spreadsheet.worksheet(worksheet_name)
            return worksheet
        except gspread.exceptions.WorksheetNotFound:
            logging.error(f"❌ Worksheet '{worksheet_name}' tidak ditemukan")
            return None
        except gspread.exceptions.APIError as e:
            logging.error(f"❌ API Error saat mengakses worksheet: {e}")
            return None
            
    except Exception as e:
        logging.error(f"❌ Kesalahan tidak terduga saat mengakses worksheet: {e}")
        return None

def append_row(worksheet, row_data):
    """
    Menambahkan baris baru ke worksheet.
    
    Args:
        worksheet (gspread.Worksheet): Objek worksheet yang akan ditambahkan data.
        row_data (list): Data baris yang akan ditambahkan.
        
    Returns:
        bool: True jika berhasil, False jika gagal.
    """
    try:
        worksheet.append_row(row_data)
        return True
    except gspread.exceptions.APIError as e:
        logging.error(f"❌ API Error saat menambahkan baris: {e}")
        return False
    except Exception as e:
        logging.error(f"❌ Kesalahan tidak terduga saat menambahkan baris: {e}")
        return False