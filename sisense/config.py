"""
Configuration module for Sisense Flask integration.

Handles all configuration settings including Sisense connection details,
authentication credentials, and application settings with environment
variable overrides.
"""

import os
import sys
from pathlib import Path
from typing import Optional, List
from dotenv import load_dotenv

# Load environment variables from .env file with error handling
def _load_environment() -> None:
    """Load environment variables with comprehensive error handling."""
    env_files = ['.env.local', '.env']
    loaded_files = []
    
    for env_file in env_files:
        if Path(env_file).exists():
            try:
                load_dotenv(env_file, override=True)
                loaded_files.append(env_file)
            except Exception as e:
                print(f"WARNING: Failed to load {env_file}: {e}")
    
    if loaded_files:
        print(f"Environment loaded from: {', '.join(loaded_files)}")
    else:
        print("No .env files found - using system environment variables only")

_load_environment()


class Config:
    """Configuration class for Sisense Flask application."""
    
    # Sisense connection settings
    SISENSE_URL: str = os.getenv('SISENSE_URL', 'https://localhost:8443')
    SISENSE_API_TOKEN: str = os.getenv('SISENSE_API_TOKEN', '')
    
    # Dual authentication support (matching React patterns)
    SISENSE_USERNAME: str = os.getenv('SISENSE_USERNAME', '')
    SISENSE_PASSWORD: str = os.getenv('SISENSE_PASSWORD', '')
    
    # Environment-specific overrides (matching React patterns)
    SISENSE_PLATFORM_OVERRIDE: str = os.getenv('SISENSE_PLATFORM_OVERRIDE', 'auto')
    SISENSE_API_VERSION_OVERRIDE: str = os.getenv('SISENSE_API_VERSION_OVERRIDE', 'auto')
    SISENSE_BASE_PATH_OVERRIDE: str = os.getenv('SISENSE_BASE_PATH_OVERRIDE', '')
    SISENSE_DISABLE_LIVE_FEATURES: bool = os.getenv('SISENSE_DISABLE_LIVE_FEATURES', 'False').lower() == 'true'
    SISENSE_DEBUG_MODE: bool = os.getenv('SISENSE_DEBUG_MODE', 'False').lower() == 'true'
    
    # Smart API detection and routing settings
    ENABLE_SMART_API_DETECTION: bool = os.getenv('ENABLE_SMART_API_DETECTION', 'True').lower() == 'true'
    API_CAPABILITY_CACHE_DURATION: int = int(os.getenv('API_CAPABILITY_CACHE_DURATION', '3600'))
    FORCE_API_VERSION: str = os.getenv('FORCE_API_VERSION', '')  # v0, v1, v2, or empty for auto-detect
    DISABLE_API_FALLBACK: bool = os.getenv('DISABLE_API_FALLBACK', 'False').lower() == 'true'
    
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
        Supports dual authentication: API token OR username/password.
        
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
        
        # Validate authentication - API token OR username/password (matching React)
        has_api_token = bool(cls.SISENSE_API_TOKEN and cls.SISENSE_API_TOKEN.strip())
        has_credentials = bool(
            cls.SISENSE_USERNAME and cls.SISENSE_USERNAME.strip() and
            cls.SISENSE_PASSWORD and cls.SISENSE_PASSWORD.strip()
        )
        
        if not has_api_token and not has_credentials:
            raise ValueError(
                "Authentication is required. Please provide either:\n"
                "1. SISENSE_API_TOKEN (get from Admin > Settings > API Tokens), OR\n"
                "2. SISENSE_USERNAME and SISENSE_PASSWORD\n"
                "Add these to your .env file or set DEMO_MODE=true to run without real Sisense connection."
            )
        
        if not cls.SISENSE_URL.startswith(('http://', 'https://')):
            raise ValueError("SISENSE_URL must start with http:// or https://")
        
        # Security validation
        cls._validate_security_settings()
    
    @classmethod
    def _validate_security_settings(cls) -> None:
        """
        Validate security-related configuration settings.
        
        Raises:
            ValueError: If security settings are invalid.
        """
        # Check for obviously insecure patterns
        if cls.SISENSE_API_TOKEN:
            if len(cls.SISENSE_API_TOKEN) < 10:
                raise ValueError("SISENSE_API_TOKEN appears too short to be valid")
            
            if cls.SISENSE_API_TOKEN in ('your_token_here', 'placeholder', 'example'):
                raise ValueError("SISENSE_API_TOKEN appears to be a placeholder value")
        
        # Validate SSL settings for production
        if cls.FLASK_ENV == 'production' and not cls.SSL_VERIFY:
            print("WARNING: SSL verification is disabled in production environment")
        
        # Check for secure connection in production
        if cls.FLASK_ENV == 'production' and not cls.SISENSE_URL.startswith('https://'):
            print("WARNING: Using non-HTTPS connection in production environment")
    
    @classmethod
    def get_authentication_type(cls) -> str:
        """
        Determine which authentication method to use (matching React priority).
        
        Returns:
            str: 'api_token', 'username_password', or 'none'
        """
        if cls.SISENSE_API_TOKEN and cls.SISENSE_API_TOKEN.strip():
            return 'api_token'
        elif (cls.SISENSE_USERNAME and cls.SISENSE_USERNAME.strip() and 
              cls.SISENSE_PASSWORD and cls.SISENSE_PASSWORD.strip()):
            return 'username_password'
        else:
            return 'none'
    
    @classmethod
    def has_valid_authentication(cls) -> bool:
        """
        Check if valid authentication credentials are available.
        
        Returns:
            bool: True if valid authentication is configured.
        """
        return cls.get_authentication_type() in ('api_token', 'username_password')
    
    @classmethod
    def validate_environment_configuration(cls) -> List[str]:
        """
        Comprehensive validation of environment configuration.
        
        Returns:
            List[str]: List of validation warnings/errors.
        """
        issues = []
        
        # Check for .env file existence
        if not Path('.env').exists() and not Path('.env.local').exists():
            issues.append(
                "No .env file found. Copy .env.example to .env and configure your settings."
            )
        
        # Check for placeholder values
        placeholder_patterns = [
            ('SISENSE_URL', ['your-sisense-server.com', 'localhost:8443', 'https://localhost:8443']),
            ('SISENSE_API_TOKEN', ['your_api_token_here', 'your_token_here']),
            ('SISENSE_USERNAME', ['your_username']),
            ('SISENSE_PASSWORD', ['your_password'])
        ]
        
        for var_name, placeholders in placeholder_patterns:
            value = getattr(cls, var_name, '')
            if value in placeholders:
                issues.append(f"{var_name} contains placeholder value: {value}")
        
        # Check for common configuration issues
        if cls.SISENSE_URL:
            if 'localhost' in cls.SISENSE_URL and cls.FLASK_ENV == 'production':
                issues.append("Using localhost URL in production environment")
            
            if cls.SISENSE_URL.endswith('/'):
                issues.append("SISENSE_URL should not end with trailing slash")
        
        # Check authentication configuration
        auth_type = cls.get_authentication_type()
        if auth_type == 'none':
            issues.append("No valid authentication configured (API token or username/password)")
        elif auth_type == 'api_token' and len(cls.SISENSE_API_TOKEN) < 20:
            issues.append("SISENSE_API_TOKEN appears too short to be a valid JWT token")
        
        # Check for potentially insecure configurations
        if cls.FLASK_ENV == 'production':
            if cls.FLASK_DEBUG:
                issues.append("Flask debug mode is enabled in production")
            if not cls.SSL_VERIFY:
                issues.append("SSL verification is disabled in production")
        
        return issues
    
    @classmethod
    def print_configuration_summary(cls) -> None:
        """Print a summary of current configuration for debugging."""
        print("\n=== Sisense Flask Configuration Summary ===")
        print(f"Sisense URL: {cls.SISENSE_URL}")
        print(f"Authentication: {cls.get_authentication_type()}")
        print(f"Demo Mode: {cls.DEMO_MODE}")
        print(f"Flask Environment: {cls.FLASK_ENV}")
        print(f"Debug Mode: {cls.FLASK_DEBUG}")
        print(f"SSL Verification: {cls.SSL_VERIFY}")
        
        # Check for issues
        issues = cls.validate_environment_configuration()
        if issues:
            print("\n⚠️  Configuration Issues:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("\n✅ Configuration looks good!")
        print("=" * 47)
    
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
        Get authentication headers for API requests (matching React pattern).
        
        Args:
            token: JWT token string.
            
        Returns:
            dict: Headers dictionary with authorization.
        """
        # Match React's exact header format
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