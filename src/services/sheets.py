import json
import time
import logging
import threading
import gc
import os
from typing import Optional, List, Dict, Any
from pathlib import Path

import gspread # type: ignore
from gspread.exceptions import APIError # type: ignore
from tenacity import retry_if_exception_type, stop_after_attempt, wait_exponential, Retrying, before_sleep_log
from ..config import settings
from ..utils.helpers import SecureLogger

class GoogleSheetsService:
    _instance = None
    _lock = threading.RLock()  # Reentrant lock for thread safety
    _connection_timeout = 3600  # 1 hour timeout for connections
    _last_connection_time = None
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(GoogleSheetsService, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        with self._lock:
            self.client = None
            self.spreadsheet = None
            self._connection_active = False
            self._initialized = True
            self._last_activity = time.time()
            self.connect()
    
    def connect(self):
        """Connect to Google Sheets with retry logic and rate limit handling"""
        with self._lock:
            try:
                # Check if we need to refresh the connection
                self._refresh_connection_if_needed()
                
                if self.client is not None and self._connection_active:
                    return True
                
                SecureLogger.info("Connecting to Google Sheets")
                # Use tenacity for retry with exponential backoff
                for attempt in Retrying(
                    stop=stop_after_attempt(5),
                    wait=wait_exponential(multiplier=1, min=2, max=60),
                    retry=retry_if_exception_type((gspread.exceptions.APIError, ConnectionError)),
                    before_sleep=before_sleep_log(logging.getLogger(), logging.WARNING)
                ):
                    with attempt:
                        # Use service account credentials from environment variables
                        credentials_content = os.getenv('GSPREAD_CREDENTIALS')
                        if credentials_content:
                            # Write credentials to a temporary file
                            temp_creds_file = 'temp_credentials.json'
                            with open(temp_creds_file, 'w') as f:
                                f.write(credentials_content)
                            
                            # Use the temporary file for authentication
                            self.client = gspread.service_account(filename=temp_creds_file)
                            
                            # Remove the temporary file after use
                            if os.path.exists(temp_creds_file):
                                os.remove(temp_creds_file)
                        else:
                            # Fallback to file-based credentials if environment variable not set
                            credentials_file = os.getenv('GOOGLE_SHEETS_CREDENTIALS', 'credentials.json')
                            self.client = gspread.service_account(filename=credentials_file)
                        
                        # Get spreadsheet by name or ID
                        spreadsheet_name = os.getenv('SPREADSHEET_NAME') or os.getenv('GOOGLE_SHEETS_SPREADSHEET_NAME')
                        spreadsheet_id = os.getenv('SPREADSHEET_ID')
                        
                        if spreadsheet_id:
                            self.spreadsheet = self.client.open_by_key(spreadsheet_id)
                        elif spreadsheet_name:
                            self.spreadsheet = self.client.open(spreadsheet_name)
                        else:
                            raise ValueError("No spreadsheet name or ID provided")
                            
                        self._connection_active = True
                        self._last_connection_time = time.time()
                        self._last_activity = time.time()
                        SecureLogger.info("Successfully connected to Google Sheets")
                        return True
            except Exception as e:
                self._connection_active = False
                SecureLogger.error(f"Failed to connect to Google Sheets: {e}")
                return False
    
    def _refresh_connection_if_needed(self):
        """Check if connection needs to be refreshed and do so if necessary"""
        current_time = time.time()
        
        # If connection is too old or inactive for too long, reset it
        if (self._last_connection_time and 
                (current_time - self._last_connection_time > self._connection_timeout or
                 current_time - self._last_activity > 1800)):  # 30 minutes of inactivity
            SecureLogger.info("Refreshing Google Sheets connection due to timeout or inactivity")
            self._close_connection()
    
    def _close_connection(self):
        """Close the connection and clean up resources"""
        with self._lock:
            try:
                # Clear references to allow garbage collection
                if self.client:
                    # Close any open sessions
                    if hasattr(self.client, 'session') and self.client.session:
                        self.client.session.close()
                    
                self.client = None
                self.spreadsheet = None
                self._connection_active = False
                gc.collect()  # Explicitly trigger garbage collection
                SecureLogger.info("Closed Google Sheets connection and cleaned up resources")
            except Exception as e:
                SecureLogger.error(f"Error closing Google Sheets connection: {e}")
    
    def get_worksheet(self, worksheet_name):
        """Get a worksheet by name with retry logic"""
        self._last_activity = time.time()  # Update last activity time
        
        if not self.is_connected():
            if not self.connect():
                return None
        
        try:
            # Use tenacity for retry with exponential backoff
            for attempt in Retrying(
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=1, min=1, max=10),
                retry=retry_if_exception_type(gspread.exceptions.APIError),
                before_sleep=before_sleep_log(logging.getLogger(), logging.WARNING)
            ):
                with attempt:
                    return self.spreadsheet.worksheet(worksheet_name)
        except Exception as e:
            SecureLogger.error(f"Error getting worksheet {worksheet_name}: {e}")
            return None
    
    def is_connected(self):
        """Check if the service is connected"""
        # For backward compatibility with health_check.py
        self.connected = self.client is not None and self.spreadsheet is not None and self._connection_active
        return self.connected
    
    def append_row(self, worksheet_name, row_data):
        """Append a row to the specified worksheet with retry logic"""
        self._last_activity = time.time()  # Update last activity time
        
        worksheet = self.get_worksheet(worksheet_name)
        if not worksheet:
            return False
        
        try:
            # Use tenacity for retry with exponential backoff
            for attempt in Retrying(
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=1, min=1, max=10),
                retry=retry_if_exception_type(gspread.exceptions.APIError),
                before_sleep=before_sleep_log(logging.getLogger(), logging.WARNING)
            ):
                with attempt:
                    worksheet.append_row(row_data)
                    return True
        except Exception as e:
            SecureLogger.error(f"Error appending row to {worksheet_name}: {e}")
            return False
    
    def get_all_records(self, worksheet_name):
        """Get all records from the specified worksheet with retry logic"""
        self._last_activity = time.time()  # Update last activity time
        
        worksheet = self.get_worksheet(worksheet_name)
        if not worksheet:
            return []
        
        try:
            # Use tenacity for retry with exponential backoff
            for attempt in Retrying(
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=1, min=1, max=10),
                retry=retry_if_exception_type(gspread.exceptions.APIError),
                before_sleep=before_sleep_log(logging.getLogger(), logging.WARNING)
            ):
                with attempt:
                    return worksheet.get_all_records()
        except Exception as e:
            SecureLogger.error(f"Error getting records from {worksheet_name}: {e}")
            return []
    
    def __del__(self):
        """Destructor to ensure resources are cleaned up"""
        self._close_connection()

    def get_worksheet(self, name: str):
        """Get a worksheet by name with rate limit handling."""
        if not self.connected:
            if not self.connect():
                return None
                
        try:
            return self.spreadsheet.worksheet(name)
        except APIError as e:
            if e.response.status_code == 429:  # Rate limit exceeded
                if self.retry_count < self.max_retries:
                    self.retry_count += 1
                    retry_delay = self.retry_delay * (2 ** (self.retry_count - 1))  # Exponential backoff
                    SecureLogger.warning(f"Rate limit exceeded. Retrying in {retry_delay} seconds. Attempt {self.retry_count}/{self.max_retries}")
                    time.sleep(retry_delay)
                    return self.get_worksheet(name)  # Recursive retry
                else:
                    SecureLogger.error(f"Failed to get worksheet after {self.max_retries} retries")
                    return None
            else:
                SecureLogger.error(f"Google Sheets API error: {e}")
                return None
        except Exception as e:
            SecureLogger.error(f"Error getting worksheet: {e}")
            return None
            
    def is_connected(self) -> bool:
        """Check if connected to Google Sheets."""
        if not self.connected:
            return self.connect()
        return self.connected
        
    def append_row(self, worksheet_name: str, row_data: List[Any]) -> bool:
        """Append a row to a worksheet with rate limit handling."""
        worksheet = self.get_worksheet(worksheet_name)
        if not worksheet:
            return False
            
        try:
            worksheet.append_row(row_data)
            self.retry_count = 0  # Reset retry count on successful operation
            return True
        except APIError as e:
            if e.response.status_code == 429:  # Rate limit exceeded
                if self.retry_count < self.max_retries:
                    self.retry_count += 1
                    retry_delay = self.retry_delay * (2 ** (self.retry_count - 1))  # Exponential backoff
                    SecureLogger.warning(f"Rate limit exceeded. Retrying in {retry_delay} seconds. Attempt {self.retry_count}/{self.max_retries}")
                    time.sleep(retry_delay)
                    return self.append_row(worksheet_name, row_data)  # Recursive retry
                else:
                    SecureLogger.error(f"Failed to append row after {self.max_retries} retries")
                    return False
            else:
                SecureLogger.error(f"Google Sheets API error: {e}")
                return False
        except Exception as e:
            SecureLogger.error(f"Error appending row: {e}")
            return False
            
    def get_all_records(self, worksheet_name: str) -> Optional[List[Dict[str, Any]]]:
        """Get all records from a worksheet with rate limit handling."""
        worksheet = self.get_worksheet(worksheet_name)
        if not worksheet:
            return None
            
        try:
            records = worksheet.get_all_records()
            self.retry_count = 0  # Reset retry count on successful operation
            return records
        except APIError as e:
            if e.response.status_code == 429:  # Rate limit exceeded
                if self.retry_count < self.max_retries:
                    self.retry_count += 1
                    retry_delay = self.retry_delay * (2 ** (self.retry_count - 1))  # Exponential backoff
                    SecureLogger.warning(f"Rate limit exceeded. Retrying in {retry_delay} seconds. Attempt {self.retry_count}/{self.max_retries}")
                    time.sleep(retry_delay)
                    return self.get_all_records(worksheet_name)  # Recursive retry
                else:
                    SecureLogger.error(f"Failed to get records after {self.max_retries} retries")
                    return None
            else:
                SecureLogger.error(f"Google Sheets API error: {e}")
                return None
        except Exception as e:
            SecureLogger.error(f"Error getting records: {e}")
            return None

# Create a singleton instance
sheets_service = GoogleSheetsService()
