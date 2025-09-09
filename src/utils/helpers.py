import re
import logging
from typing import Optional, Tuple, Any, Dict

def parse_message(text: str) -> Tuple[Optional[int], Optional[str], Optional[str]]:
    """
    Parse message text into amount, category, and description.
    
    Expected format: /command amount #category description
    Returns (None, None, None) if parsing fails.
    """
    parts = text.split()
    
    if len(parts) < 2:
        return None, None, None
        
    try:
        jumlah = abs(int(parts[1]))
    except (ValueError, IndexError):
        return None, None, None
        
    # Process category and description
    kategori = "lainnya"
    deskripsi_parts = []
    
    for part in parts[2:]:
        if part.startswith('#'):
            kategori = part[1:].lower().strip()
        else:
            deskripsi_parts.append(part)
            
    deskripsi = " ".join(deskripsi_parts) if deskripsi_parts else "-"
    return jumlah, kategori, deskripsi

def format_currency(amount: float) -> str:
    """Format currency with Indonesian Rupiah formatting."""
    return f"Rp {amount:,.0f}".replace(",", ".")

def get_month_name(month: int) -> str:
    """Get month name in Indonesian."""
    months = [
        "", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember"
    ]
    return months[month] if 1 <= month <= 12 else "Tidak Diketahui"

def sanitize_log_data(data: Any) -> Any:
    """
    Sanitize sensitive data for logging.
    
    Masks or removes sensitive information like user IDs, transaction amounts,
    and personal financial details before they are logged.
    """
    if isinstance(data, str):
        # Mask user IDs
        data = re.sub(r'user\s+(\d+)', r'user ***', data)
        data = re.sub(r'user_id[=:]\s*(\d+)', r'user_id=***', data)
        
        # Mask transaction amounts
        data = re.sub(r'(Rp\s*[\d.,]+)', r'Rp ***', data)
        data = re.sub(r'([\d.,]+\s*Rp)', r'*** Rp', data)
        data = re.sub(r'jumlah[=:]\s*([\d.,]+)', r'jumlah=***', data)
        
        # Mask financial details
        data = re.sub(r'saldo[=:]\s*([\d.,]+)', r'saldo=***', data)
        data = re.sub(r'pemasukan[=:]\s*([\d.,]+)', r'pemasukan=***', data)
        data = re.sub(r'pengeluaran[=:]\s*([\d.,]+)', r'pengeluaran=***', data)
        
    elif isinstance(data, dict):
        # Create a new dict with sanitized values
        sanitized = {}
        sensitive_keys = ['user_id', 'jumlah', 'saldo', 'pemasukan', 'pengeluaran']
        
        for key, value in data.items():
            if key.lower() in sensitive_keys:
                sanitized[key] = '***'
            else:
                sanitized[key] = sanitize_log_data(value)
        return sanitized
    
    return data

class SecureLogger:
    """
    A secure logging wrapper that sanitizes sensitive data before logging.
    
    This class wraps the standard Python logging module to ensure all logs
    are sanitized of sensitive information before being written.
    """
    
    @staticmethod
    def debug(msg: Any, *args, **kwargs):
        """Log a debug message with sanitized data."""
        logging.debug(sanitize_log_data(msg), *args, **kwargs)
    
    @staticmethod
    def info(msg: Any, *args, **kwargs):
        """Log an info message with sanitized data."""
        logging.info(sanitize_log_data(msg), *args, **kwargs)
    
    @staticmethod
    def warning(msg: Any, *args, **kwargs):
        """Log a warning message with sanitized data."""
        logging.warning(sanitize_log_data(msg), *args, **kwargs)
    
    @staticmethod
    def error(msg: Any, *args, **kwargs):
        """Log an error message with sanitized data."""
        logging.error(sanitize_log_data(msg), *args, **kwargs)
    
    @staticmethod
    def critical(msg: Any, *args, **kwargs):
        """Log a critical message with sanitized data."""
        logging.critical(sanitize_log_data(msg), *args, **kwargs)
    
    @staticmethod
    def exception(msg: Any, *args, **kwargs):
        """Log an exception message with sanitized data."""
        logging.exception(sanitize_log_data(msg), *args, **kwargs)
