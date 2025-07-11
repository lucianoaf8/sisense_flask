"""
Configuration module for Sisense Flask integration.

Handles all configuration settings including Sisense connection details,
authentication credentials, and application settings with environment
variable overrides.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for Sisense Flask application."""
    
    # Sisense connection settings
    SISENSE_URL: str = os.getenv('SISENSE_URL', 'https://localhost:8443')
    SISENSE_API_TOKEN: str = os.getenv('SISENSE_API_TOKEN', '')
    
    # Demo mode (allows app to run without real Sisense credentials)
    DEMO_MODE: bool = os.getenv('DEMO_MODE', 'False').lower() == 'true'
    
    # Authentication settings
    JWT_TOKEN_CACHE_DURATION: int = int(os.getenv('JWT_TOKEN_CACHE_DURATION', '3600'))
    JWT_TOKEN_REFRESH_BUFFER: int = int(os.getenv('JWT_TOKEN_REFRESH_BUFFER', '300'))
    
    # HTTP request settings
    REQUEST_TIMEOUT: int = int(os.getenv('REQUEST_TIMEOUT', '30'))
    REQUEST_RETRIES: int = int(os.getenv('REQUEST_RETRIES', '3'))
    REQUEST_RETRY_DELAY: float = float(os.getenv('REQUEST_RETRY_DELAY', '1.0'))
    REQUEST_RETRY_BACKOFF: float = float(os.getenv('REQUEST_RETRY_BACKOFF', '2.0'))
    
    # Flask settings
    FLASK_ENV: str = os.getenv('FLASK_ENV', 'production')
    FLASK_DEBUG: bool = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    FLASK_PORT: int = int(os.getenv('FLASK_PORT', '5000'))
    
    # Logging settings
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT: str = os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # SSL settings
    SSL_VERIFY: bool = os.getenv('SSL_VERIFY', 'True').lower() == 'true'
    SSL_CERT_PATH: Optional[str] = os.getenv('SSL_CERT_PATH')
    
    @classmethod
    def validate_required_settings(cls) -> None:
        """
        Validate that all required configuration settings are present.
        
        Raises:
            ValueError: If required settings are missing or invalid.
        """
        # In demo mode, skip validation
        if cls.DEMO_MODE:
            print("Running in DEMO MODE - Sisense features will be simulated")
            return
            
        if not cls.SISENSE_URL or cls.SISENSE_URL == 'https://localhost:8443':
            raise ValueError(
                "SISENSE_URL is required and must be configured. "
                "Please create a .env file with your Sisense server URL. "
                "Copy .env.example to .env and update the values. "
                "Or set DEMO_MODE=true to run without real Sisense connection."
            )
        
        if not cls.SISENSE_API_TOKEN or cls.SISENSE_API_TOKEN == '':
            raise ValueError(
                "SISENSE_API_TOKEN is required. "
                "Please get an API token from your Sisense admin panel "
                "(Admin > Settings > API Tokens) and add it to your .env file. "
                "Or set DEMO_MODE=true to run without real Sisense connection."
            )
        
        if not cls.SISENSE_URL.startswith(('http://', 'https://')):
            raise ValueError("SISENSE_URL must start with http:// or https://")
    
    @classmethod
    def get_sisense_base_url(cls) -> str:
        """
        Get the base URL for Sisense API calls.
        
        Returns:
            str: Base URL with trailing slash removed.
        """
        return cls.SISENSE_URL.rstrip('/')
    
    @classmethod
    def get_auth_headers(cls, token: str) -> dict:
        """
        Get authentication headers for API requests.
        
        Args:
            token: JWT token string.
            
        Returns:
            dict: Headers dictionary with authorization.
        """
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    @classmethod
    def get_login_headers(cls) -> dict:
        """
        Get headers for login requests.
        
        Returns:
            dict: Headers dictionary for login.
        """
        return {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }