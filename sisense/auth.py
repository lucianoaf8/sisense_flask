"""
Authentication module for Sisense API.

Handles API token-based authentication for Sisense API calls.
With API tokens, we don't need login/logout or token refresh logic.
"""

import logging
from typing import Dict, Optional, Tuple
import time
import requests

from config import Config
from sisense.utils import SisenseAPIError


logger = logging.getLogger(__name__)


def get_auth_headers() -> Dict[str, str]:
    """
    Get authentication headers with API token or session token.
    
    Returns:
        Dict[str, str]: Headers with authorization token.
        
    Raises:
        SisenseAPIError: If authentication is not available.
    """
    if Config.DEMO_MODE:
        return {"Authorization": "Bearer demo-token", "Content-Type": "application/json"}
    
    # Validate configuration first
    if not Config.has_valid_authentication():
        raise SisenseAPIError(
            "No valid authentication configured. "
            "Please provide SISENSE_API_TOKEN or SISENSE_USERNAME/SISENSE_PASSWORD in your .env file."
        )
    
    # Get authentication client and token
    auth_client = get_auth_client()
    token = auth_client.get_valid_token()
    
    return Config.get_auth_headers(token)


def validate_authentication() -> bool:
    """
    Validate current authentication using React-style validation.
    
    Returns:
        bool: True if authentication is valid.
    """
    try:
        auth_client = get_auth_client()
        token = auth_client.get_valid_token()
        return bool(token)
    except Exception as e:
        logger.error(f"Authentication validation failed: {e}")
        return False


def login() -> str:
    """
    Get API token for authentication.
    
    With API token authentication, this simply returns the configured token.
    No login request is needed.
    
    Returns:
        str: API token.
        
    Raises:
        SisenseAPIError: If API token is not configured.
    """
    if not Config.SISENSE_API_TOKEN:
        raise SisenseAPIError("SISENSE_API_TOKEN is not configured")
    
    logger.debug("Using configured API token for authentication")
    return Config.SISENSE_API_TOKEN


def invalidate_token() -> None:
    """
    Invalidate cached authentication tokens.
    
    Clears both API token cache and session token cache.
    """
    logger.debug("Invalidating authentication tokens")
    global _auth_client
    if _auth_client:
        _auth_client.invalidate_tokens()
    _auth_client = None


class ReactStyleAuthClient:
    """
    Authentication client matching React's dual authentication strategy.
    Supports both API token and username/password authentication.
    """
    
    def __init__(self):
        """Initialize authentication client."""
        self.logger = logging.getLogger(__name__)
        self.api_token = Config.SISENSE_API_TOKEN.strip() if Config.SISENSE_API_TOKEN else None
        self.use_api_token = bool(self.api_token)
        self.session_token = None
        self.token_expiry = None
        
        # Get authentication type from Config
        auth_type = Config.get_authentication_type()
        
        # Log configuration info (matching React pattern)
        self.logger.info('Initializing authentication client', extra={
            'auth_type': auth_type,
            'has_api_token': bool(self.api_token),
            'use_api_token': self.use_api_token
        })
    
    def authenticate(self) -> str:
        """
        Authenticate using React's priority system.
        
        Returns:
            str: Authentication token.
            
        Raises:
            SisenseAPIError: If authentication fails.
        """
        try:
            # Priority 1: API Token (if available) - matching React pattern
            if self.use_api_token and self.api_token:
                self.logger.info('Using API token for authentication')
                self.session_token = self.api_token
                self.token_expiry = time.time() + (24 * 60 * 60)  # 24 hours for API tokens
                
                # Test the API token by making a simple validation request
                try:
                    self.test_api_token()
                    self.logger.info('API token authentication successful')
                    return self.session_token
                except Exception as token_error:
                    self.logger.error(f'API token validation failed: {str(token_error)}')
                    raise SisenseAPIError(f'Invalid API token: {str(token_error)}')
            
            # Priority 2: Username/Password fallback (matching React pattern)
            username = Config.SISENSE_USERNAME.strip() if Config.SISENSE_USERNAME else None
            password = Config.SISENSE_PASSWORD.strip() if Config.SISENSE_PASSWORD else None
            
            if not username or not password:
                raise SisenseAPIError(
                    'No valid authentication method available. '
                    'Please provide either SISENSE_API_TOKEN or SISENSE_USERNAME/SISENSE_PASSWORD in your .env file.'
                )
            
            self.logger.info('Starting Sisense username/password authentication')
            
            login_url = f"{Config.get_sisense_base_url()}/api/v1/authentication/login"
            response = requests.post(login_url, 
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                data={'username': username, 'password': password},
                timeout=Config.REQUEST_TIMEOUT,
                verify=Config.SSL_VERIFY
            )
            
            if not response.ok:
                raise SisenseAPIError(f'Authentication failed: {response.status_text}')
            
            data = response.json()
            self.session_token = data['access_token']
            self.token_expiry = time.time() + 3600  # 1 hour
            
            self.logger.info('Sisense username/password authentication successful')
            return self.session_token
            
        except Exception as error:
            self.logger.error(f'Sisense authentication error: {str(error)}')
            raise error
    
    def get_valid_token(self) -> str:
        """
        Get a valid authentication token (matching React pattern).
        
        Returns:
            str: Valid authentication token.
        """
        if not self.session_token or time.time() > (self.token_expiry or 0):
            self.authenticate()
        return self.session_token
    
    def test_api_token(self) -> None:
        """
        Test API token validity (matching React pattern).
        
        Raises:
            SisenseAPIError: If token validation fails.
        """
        # Use a known working endpoint for validation
        # React uses '/api/v1/elasticubes/getElasticubes' for testing
        test_url = f"{Config.get_sisense_base_url()}/api/v1/dashboards"
        response = requests.get(test_url,
            headers={
                'Authorization': f'Bearer {self.api_token}',
                'Content-Type': 'application/json'
            },
            timeout=Config.REQUEST_TIMEOUT,
            verify=Config.SSL_VERIFY
        )
        
        if not response.ok:
            raise SisenseAPIError(
                f'Token validation failed: {response.status_code} {response.reason}'
            )
        
        self.logger.debug('API token validation successful')
    
    def invalidate_tokens(self) -> None:
        """
        Invalidate all cached tokens.
        """
        self.session_token = None
        self.token_expiry = None
        self.logger.debug('Authentication tokens invalidated')


# Global authentication client instance
_auth_client = None


def get_auth_client() -> ReactStyleAuthClient:
    """
    Get singleton authentication client instance.
    
    Returns:
        ReactStyleAuthClient: Authentication client instance.
    """
    global _auth_client
    if _auth_client is None:
        _auth_client = ReactStyleAuthClient()
    return _auth_client