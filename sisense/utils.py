"""
Utility module for Sisense API interactions.

This module provides centralized HTTP session management, logging, error handling,
and retry logic for all Sisense API calls.
"""

import logging
import time
from typing import Dict, Any, Optional, Union
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException
from urllib3.util.retry import Retry

from config import Config


class SisenseAPIError(Exception):
    """Custom exception for Sisense API errors."""
    
    def __init__(self, message: str, status_code: int = None, response_data: Dict = None):
        """
        Initialize SisenseAPIError.
        
        Args:
            message: Error message.
            status_code: HTTP status code.
            response_data: Response data from API.
        """
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}


class SisenseHTTPClient:
    """HTTP client for Sisense API interactions."""
    
    def __init__(self):
        """Initialize the HTTP client with session and retry configuration."""
        self.logger = logging.getLogger(__name__)
        self.session = self._create_session()
        self.base_url = Config.get_sisense_base_url()
    
    def _create_session(self) -> requests.Session:
        """
        Create and configure HTTP session with retry strategy.
        
        Returns:
            requests.Session: Configured session object.
        """
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=Config.REQUEST_RETRIES,
            backoff_factor=Config.REQUEST_RETRY_BACKOFF,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Configure SSL verification
        session.verify = Config.SSL_VERIFY
        if Config.SSL_CERT_PATH:
            session.verify = Config.SSL_CERT_PATH
        
        return session
    
    def _build_url(self, endpoint: str) -> str:
        """
        Build full URL for API endpoint.
        
        Args:
            endpoint: API endpoint path.
            
        Returns:
            str: Full URL for the endpoint.
        """
        return urljoin(self.base_url, endpoint.lstrip('/'))
    
    def _handle_response(self, response: requests.Response) -> Dict[Any, Any]:
        """
        Handle HTTP response and extract data.
        
        Args:
            response: HTTP response object.
            
        Returns:
            Dict: Response data.
            
        Raises:
            SisenseAPIError: If response indicates an error.
        """
        try:
            response_data = response.json() if response.content else {}
        except ValueError:
            response_data = {'raw_content': response.text}
        
        if not response.ok:
            error_message = (
                response_data.get('message') or 
                response_data.get('error') or 
                f"HTTP {response.status_code} error"
            )
            
            self.logger.error(
                f"API request failed: {error_message} "
                f"(Status: {response.status_code}, URL: {response.url})"
            )
            
            raise SisenseAPIError(
                message=error_message,
                status_code=response.status_code,
                response_data=response_data
            )
        
        return response_data
    
    def request(
        self,
        method: str,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict, str]] = None,
        json: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None
    ) -> Dict[Any, Any]:
        """
        Make HTTP request to Sisense API.
        
        Args:
            method: HTTP method (GET, POST, etc.).
            endpoint: API endpoint path.
            headers: Optional headers dictionary.
            params: Optional query parameters.
            data: Optional form data.
            json: Optional JSON data.
            timeout: Optional request timeout.
            
        Returns:
            Dict: Response data.
            
        Raises:
            SisenseAPIError: If request fails.
        """
        url = self._build_url(endpoint)
        request_timeout = timeout or Config.REQUEST_TIMEOUT
        
        # Log request details
        self.logger.debug(
            f"Making {method} request to {url} "
            f"with params: {params}, headers: {headers}"
        )
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                data=data,
                json=json,
                timeout=request_timeout
            )
            
            return self._handle_response(response)
            
        except RequestException as e:
            self.logger.error(f"Request failed: {str(e)}")
            raise SisenseAPIError(f"Request failed: {str(e)}")
    
    def get(
        self,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None
    ) -> Dict[Any, Any]:
        """
        Make GET request to Sisense API.
        
        Args:
            endpoint: API endpoint path.
            headers: Optional headers dictionary.
            params: Optional query parameters.
            timeout: Optional request timeout.
            
        Returns:
            Dict: Response data.
        """
        return self.request("GET", endpoint, headers=headers, params=params, timeout=timeout)
    
    def post(
        self,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict, str]] = None,
        json: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None
    ) -> Dict[Any, Any]:
        """
        Make POST request to Sisense API.
        
        Args:
            endpoint: API endpoint path.
            headers: Optional headers dictionary.
            params: Optional query parameters.
            data: Optional form data.
            json: Optional JSON data.
            timeout: Optional request timeout.
            
        Returns:
            Dict: Response data.
        """
        return self.request(
            "POST", 
            endpoint, 
            headers=headers, 
            params=params, 
            data=data, 
            json=json,
            timeout=timeout
        )


# Global HTTP client instance
_http_client = None


def get_http_client() -> SisenseHTTPClient:
    """
    Get singleton HTTP client instance.
    
    Returns:
        SisenseHTTPClient: HTTP client instance.
    """
    global _http_client
    if _http_client is None:
        _http_client = SisenseHTTPClient()
    return _http_client


def setup_logging() -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL.upper()),
        format=Config.LOG_FORMAT,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('sisense_flask.log')
        ]
    )


def validate_response_data(data: Dict, required_fields: list) -> None:
    """
    Validate that response data contains required fields.
    
    Args:
        data: Response data dictionary.
        required_fields: List of required field names.
        
    Raises:
        SisenseAPIError: If required fields are missing.
    """
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise SisenseAPIError(
            f"Response missing required fields: {', '.join(missing_fields)}"
        )