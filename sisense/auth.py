"""
Authentication module for Sisense API.

Handles API token-based authentication for Sisense API calls.
With API tokens, we don't need login/logout or token refresh logic.
"""

import logging
import requests
from typing import Dict
from sisense.config import Config
from sisense.utils import SisenseAPIError

logger = logging.getLogger(__name__)

def get_auth_headers() -> Dict[str, str]:
    """Get authentication headers with API token."""
    if Config.DEMO_MODE:
        return {"Authorization": "Bearer demo-token", "Content-Type": "application/json"}
    
    if not Config.SISENSE_API_TOKEN:
        raise SisenseAPIError("SISENSE_API_TOKEN is not configured")
    
    return {
        'Authorization': f'Bearer {Config.SISENSE_API_TOKEN}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

def validate_authentication() -> bool:
    """Validate authentication using correct authentication endpoints."""
    try:
        headers = get_auth_headers()
        base_url = Config.get_sisense_base_url()
        
        # Use correct authentication validation endpoints with fallback
        auth_endpoints = [
            '/api/v1/auth/isauth',    # Primary v1 endpoint
            '/auth/isauth',           # v0 fallback
            '/api/v2/auth/isauth'     # v2 if available
        ]
        
        for endpoint in auth_endpoints:
            try:
                response = requests.get(
                    f"{base_url}{endpoint}",
                    headers=headers,
                    timeout=Config.REQUEST_TIMEOUT,
                    verify=Config.SSL_VERIFY
                )
                if response.status_code == 200:
                    logger.debug(f"Authentication validated using {endpoint}")
                    return True
            except Exception as e:
                logger.debug(f"Authentication endpoint {endpoint} failed: {e}")
                continue
        
        # Fallback: validate using working dashboards endpoint
        response = requests.get(
            f"{base_url}/api/v1/dashboards",
            headers=headers,
            timeout=Config.REQUEST_TIMEOUT,
            verify=Config.SSL_VERIFY
        )
        
        if response.status_code == 200:
            logger.debug("Authentication validated using dashboards fallback")
            return True
        
        return False
        
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
    
    With API tokens, this is a no-op since tokens don't expire.
    """
    logger.debug("API tokens do not require invalidation")
    pass