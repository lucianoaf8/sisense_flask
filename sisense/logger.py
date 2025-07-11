"""
Enhanced logging system for Sisense Flask integration.

Provides file-based logging with log rotation, real-time streaming,
and sensitive data sanitization.
"""

import logging
import os
import json
import time
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Dict, Any, List
import re


class SisenseLogger:
    """Enhanced logger with file rotation and real-time capabilities."""
    
    def __init__(self, log_dir: str = "logs"):
        """
        Initialize the enhanced logger.
        
        Args:
            log_dir: Directory to store log files
        """
        self.log_dir = log_dir
        self.log_buffer = []  # Buffer for real-time log streaming
        self.max_buffer_size = 1000
        
        # Create logs directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)
        
        # Generate session-specific log filename
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_log_file = os.path.join(log_dir, f"sisense_session_{session_id}.log")
        
        # Setup logging
        self.setup_logging()
    
    def setup_logging(self):
        """Configure enhanced logging with file rotation."""
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File handler with rotation (10MB max, 5 backup files)
        file_handler = RotatingFileHandler(
            self.current_log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        
        # Get root logger and configure
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Add new handlers
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
        # Add custom handler for real-time buffering
        buffer_handler = BufferHandler(self.log_buffer, self.max_buffer_size)
        buffer_handler.setFormatter(formatter)
        root_logger.addHandler(buffer_handler)
    
    def sanitize_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize payload by removing sensitive data.
        
        Args:
            payload: Original payload dictionary
            
        Returns:
            Dict: Sanitized payload
        """
        if not isinstance(payload, dict):
            return payload
        
        sanitized = payload.copy()
        
        # List of sensitive keys to sanitize
        sensitive_keys = [
            'api_token', 'token', 'password', 'secret', 'key',
            'authorization', 'auth', 'credential', 'sisense_api_token'
        ]
        
        for key, value in sanitized.items():
            # Check if key contains sensitive information
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                if isinstance(value, str) and len(value) > 8:
                    # Show only first 4 and last 4 characters
                    sanitized[key] = f"{value[:4]}...{value[-4:]}"
                else:
                    sanitized[key] = "***REDACTED***"
            
            # Recursively sanitize nested dictionaries
            elif isinstance(value, dict):
                sanitized[key] = self.sanitize_payload(value)
            
            # Handle authorization headers
            elif key.lower() == 'headers' and isinstance(value, dict):
                sanitized_headers = value.copy()
                for header_key, header_value in sanitized_headers.items():
                    if 'authorization' in header_key.lower():
                        if isinstance(header_value, str) and len(header_value) > 8:
                            sanitized_headers[header_key] = f"{header_value[:12]}...{header_value[-4:]}"
                        else:
                            sanitized_headers[header_key] = "***REDACTED***"
                sanitized[key] = sanitized_headers
        
        return sanitized
    
    def log_api_call(self, method: str, endpoint: str, payload: Dict[str, Any] = None, 
                     response_status: int = None, response_time: float = None):
        """
        Log API call with sanitized payload.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            payload: Request payload (will be sanitized)
            response_status: HTTP response status code
            response_time: Response time in seconds
        """
        logger = logging.getLogger(__name__)
        
        log_entry = {
            'type': 'api_call',
            'method': method,
            'endpoint': endpoint,
            'timestamp': datetime.now().isoformat(),
            'response_status': response_status,
            'response_time_ms': round(response_time * 1000, 2) if response_time else None
        }
        
        if payload:
            log_entry['payload'] = self.sanitize_payload(payload)
        
        logger.info(f"API Call: {json.dumps(log_entry, indent=2)}")
    
    def log_user_action(self, action: str, details: Dict[str, Any] = None):
        """
        Log user action.
        
        Args:
            action: Description of user action
            details: Additional details about the action
        """
        logger = logging.getLogger(__name__)
        
        log_entry = {
            'type': 'user_action',
            'action': action,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        
        logger.info(f"User Action: {json.dumps(log_entry, indent=2)}")
    
    def log_system_event(self, event: str, level: str = "INFO", details: Dict[str, Any] = None):
        """
        Log system event.
        
        Args:
            event: Description of system event
            level: Log level (INFO, WARNING, ERROR)
            details: Additional details about the event
        """
        logger = logging.getLogger(__name__)
        
        log_entry = {
            'type': 'system_event',
            'event': event,
            'level': level,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(f"System Event: {json.dumps(log_entry, indent=2)}")
    
    def get_recent_logs(self, limit: int = 100) -> List[str]:
        """
        Get recent logs from buffer.
        
        Args:
            limit: Maximum number of log entries to return
            
        Returns:
            List: Recent log entries
        """
        return self.log_buffer[-limit:] if self.log_buffer else []
    
    def get_log_files(self) -> List[Dict[str, Any]]:
        """
        Get list of available log files.
        
        Returns:
            List: Log file information
        """
        log_files = []
        
        for filename in os.listdir(self.log_dir):
            if filename.endswith('.log'):
                filepath = os.path.join(self.log_dir, filename)
                stat_info = os.stat(filepath)
                
                log_files.append({
                    'filename': filename,
                    'filepath': filepath,
                    'size': stat_info.st_size,
                    'created': datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
                    'modified': datetime.fromtimestamp(stat_info.st_mtime).isoformat()
                })
        
        # Sort by creation time (newest first)
        log_files.sort(key=lambda x: x['created'], reverse=True)
        return log_files


class BufferHandler(logging.Handler):
    """Custom logging handler that maintains a buffer for real-time streaming."""
    
    def __init__(self, buffer: List[str], max_size: int):
        """
        Initialize buffer handler.
        
        Args:
            buffer: List to store log records
            max_size: Maximum buffer size
        """
        super().__init__()
        self.buffer = buffer
        self.max_size = max_size
    
    def emit(self, record):
        """Add log record to buffer."""
        try:
            msg = self.format(record)
            self.buffer.append(msg)
            
            # Trim buffer if it exceeds max size
            if len(self.buffer) > self.max_size:
                self.buffer.pop(0)
        except Exception:
            self.handleError(record)


# Global logger instance
_sisense_logger = None


def get_logger() -> SisenseLogger:
    """Get global logger instance."""
    global _sisense_logger
    if _sisense_logger is None:
        _sisense_logger = SisenseLogger()
    return _sisense_logger


def log_api_call(method: str, endpoint: str, payload: Dict[str, Any] = None, 
                response_status: int = None, response_time: float = None):
    """Convenience function for logging API calls."""
    get_logger().log_api_call(method, endpoint, payload, response_status, response_time)


def log_user_action(action: str, details: Dict[str, Any] = None):
    """Convenience function for logging user actions."""
    get_logger().log_user_action(action, details)


def log_system_event(event: str, level: str = "INFO", details: Dict[str, Any] = None):
    """Convenience function for logging system events."""
    get_logger().log_system_event(event, level, details)
