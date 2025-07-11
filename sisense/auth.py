"""
Authentication module for Sisense API.

Handles API token-based authentication for Sisense API calls.
With API tokens, we don't need login/logout or token refresh logic.
"""

import logging
from typing import Dict

from config import Config
from sisense.utils import SisenseAPIError


logger = logging.getLogger(__name__)


def get_auth_headers() -> Dict[str, str]:
    """
    Get authentication headers with API token.
    
    Returns:
        Dict[str, str]: Headers with authorization token.
        
    Raises:
        SisenseAPIError: If API token is not configured.
    """
    if Config.DEMO_MODE:
        return {"Authorization": "Bearer demo-token", "Content-Type": "application/json"}
        
    if not Config.SISENSE_API_TOKEN:
        raise SisenseAPIError("SISENSE_API_TOKEN is not configured")
    
    return Config.get_auth_headers(Config.SISENSE_API_TOKEN)


def validate_authentication() -> bool:
    """
    Validate current authentication by checking if API token is configured.
    
    Returns:
        bool: True if API token is configured.
    """
    try:
        # For API token auth, we just check if token is configured
        # Actual validation happens when making API calls
        return bool(Config.SISENSE_API_TOKEN)
    except Exception:
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
    Invalidate token (no-op for API token authentication).
    
    With API tokens, there's no need to invalidate as they are static.
    This function is kept for API compatibility.
    """
    logger.debug("Token invalidation called (no-op for API token auth)")
    pass