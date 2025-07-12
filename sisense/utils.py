"""
Utility module for Sisense API interactions.

This module provides centralized HTTP session management, logging, error handling,
and retry logic for all Sisense API calls.
"""

import logging
import time
import asyncio
from typing import Dict, Any, Optional, Union
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException
from urllib3.util.retry import Retry

from sisense.config import Config


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
    """HTTP client for Sisense API interactions matching React patterns."""
    
    def __init__(self):
        """Initialize the HTTP client with session and retry configuration."""
        self.logger = logging.getLogger(__name__)
        self.session = self._create_session()
        self.base_url = Config.get_sisense_base_url()
        self.retry_attempts = Config.REQUEST_RETRIES
        self.request_timeout = Config.REQUEST_TIMEOUT
        
        # Environment configuration integration
        from sisense.env_config import get_environment_config
        self.env_config = get_environment_config()
        
        # Platform detection cache (matching React pattern)
        self.api_capabilities = None
    
    def _create_session(self) -> requests.Session:
        """
        Create and configure HTTP session WITHOUT automatic retry.
        React handles retry manually, so we disable requests' built-in retry.
        
        Returns:
            requests.Session: Configured session object.
        """
        session = requests.Session()
        
        # Disable automatic retries - we'll handle them manually like React
        # React uses manual retry with specific timing: 1s, 2s, 3s
        retry_strategy = Retry(
            total=0,  # Disable automatic retries
            backoff_factor=0,
            status_forcelist=[],
            allowed_methods=[]
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
        Build URL for API endpoint matching React's smart URL handling with environment awareness.
        
        Args:
            endpoint: API endpoint path.
            
        Returns:
            str: URL for the endpoint (relative in dev, absolute in prod).
        """
        # Get environment profile for URL construction strategy
        env_profile = self.env_config.get_environment_profile()
        
        # Apply base path override if configured
        if Config.SISENSE_BASE_PATH_OVERRIDE:
            # Transform endpoint to include base path override
            # e.g., /api/v1/dashboards -> /app/api/v1/dashboards
            base_path = Config.SISENSE_BASE_PATH_OVERRIDE.strip('/')
            if endpoint.startswith('/api/'):
                endpoint = f"/{base_path}{endpoint}"
            
        # Match React pattern: relative URLs in development, absolute in production
        if env_profile['is_development'] and 'localhost' in (Config.SISENSE_URL or ''):
            # Return relative URL for development (like React proxy mode)
            self.logger.debug(f"Using relative URL for development: {endpoint}")
            return endpoint
        
        # Return full URL for production
        full_url = urljoin(self.base_url, endpoint.lstrip('/'))
        self.logger.debug(f"Using full URL: {full_url}")
        return full_url
    
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
    
    def request_with_retry(
        self,
        method: str,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict, str]] = None,
        json: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
        attempt: int = 1
    ) -> Dict[Any, Any]:
        """
        Make HTTP request with React-style manual retry logic.
        
        Args:
            method: HTTP method (GET, POST, etc.).
            endpoint: API endpoint path.
            headers: Optional headers dictionary.
            params: Optional query parameters.
            data: Optional form data.
            json: Optional JSON data.
            timeout: Optional request timeout.
            attempt: Current attempt number.
            
        Returns:
            Dict: Response data.
            
        Raises:
            SisenseAPIError: If request fails after all retries.
        """
        url = self._build_url(endpoint)
        request_timeout = timeout or self.request_timeout
        
        # Add environment-specific headers
        env_headers = self.env_config.get_platform_headers()
        if headers:
            headers.update(env_headers)
        else:
            headers = env_headers
        
        # Log request details
        self.logger.debug(
            f"Making {method} request to {url} (attempt {attempt}/{self.retry_attempts})"
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
            
        except (RequestException, SisenseAPIError) as e:
            # Implement React's retry logic: attempt < retryAttempts
            if attempt < self.retry_attempts and not self._is_abort_error(e):
                self.logger.warn(
                    f"Request failed, retrying ({attempt}/{self.retry_attempts}): {str(e)}"
                )
                # React pattern: delay = 1000 * attempt (1s, 2s, 3s)
                delay_seconds = attempt  # 1, 2, 3 seconds
                time.sleep(delay_seconds)
                return self.request_with_retry(
                    method, endpoint, headers, params, data, json, timeout, attempt + 1
                )
            
            self.logger.error(f"Request failed after {attempt} attempts: {str(e)}")
            if isinstance(e, SisenseAPIError):
                raise e
            else:
                raise SisenseAPIError(f"Request failed: {str(e)}")
    
    def _is_abort_error(self, error: Exception) -> bool:
        """
        Check if error is equivalent to React's AbortError.
        
        Args:
            error: Exception to check.
            
        Returns:
            bool: True if this is a timeout/abort type error.
        """
        error_str = str(error).lower()
        return (
            'timeout' in error_str or 
            'abort' in error_str or
            'connection aborted' in error_str
        )
    
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
        Make HTTP request to Sisense API with React-style retry.
        
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
        return self.request_with_retry(
            method, endpoint, headers, params, data, json, timeout
        )
    
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


def get_http_client():
    """
    Get singleton HTTP client instance with React-style patterns.
    
    Returns:
        ReactStyleSisenseClient: Enhanced HTTP client instance.
    """
    global _http_client
    if _http_client is None:
        _http_client = ReactStyleSisenseClient()
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


class ReactStyleSisenseClient(SisenseHTTPClient):
    """Enhanced HTTP client matching React's API patterns exactly."""
    
    def __init__(self):
        """Initialize with React-style capabilities and environment awareness."""
        super().__init__()
        self.api_capabilities = None
        
        # Get environment-aware endpoint mappings
        capabilities = self.env_config.detect_endpoint_capabilities()
        self.endpoint_mappings = capabilities.platform_specific_endpoints or {
            'connections': '/api/v2/connections',
            'datamodels': '/api/v2/datamodels', 
            'dashboards': '/api/v1/dashboards',
            'widgets': '/api/v1/widgets'
        }
    
    def detect_api_capabilities(self) -> Dict[str, Any]:
        """
        Detect API capabilities using environment configuration.
        
        Returns:
            Dict: Capabilities information.
        """
        if self.api_capabilities:
            return self.api_capabilities
        
        self.logger.info('Detecting API capabilities via environment config...')
        
        # Use environment configuration for capabilities
        env_capabilities = self.env_config.detect_endpoint_capabilities()
        platform_info = self.env_config.detect_platform_capabilities()
        
        # Convert to React-compatible format
        capabilities = {
            'v1_available': env_capabilities.v1_available,
            'v2_available': env_capabilities.v2_available,
            'v2_datamodels_endpoint': env_capabilities.v2_datamodels_available,
            'preferred_version': env_capabilities.preferred_version.value,
            'working_v2_endpoint': env_capabilities.working_v2_endpoint,
            'detected_at': env_capabilities.tested_at,
            'errors': [],
            'endpoint_mappings': env_capabilities.platform_specific_endpoints,
            'platform_info': {
                'platform': platform_info.platform.value,
                'deployment': platform_info.deployment.value,
                'supports_v2': platform_info.supports_v2,
                'limitations': platform_info.limitations
            }
        }
        
        self.api_capabilities = capabilities
        self.logger.info(f'API capabilities detected: V1={capabilities["v1_available"]}, V2={capabilities["v2_available"]}, Platform={platform_info.platform.value}')
        
        return capabilities
    
    def _get_test_headers(self) -> Dict[str, str]:
        """Get headers for testing API endpoints."""
        from sisense.auth import get_auth_headers
        try:
            return get_auth_headers()
        except Exception:
            # Return basic headers for testing if auth fails
            return {'Content-Type': 'application/json'}
    
    def get_preferred_endpoint(self, resource_type: str) -> Optional[str]:
        """
        Get the preferred endpoint for a resource type using environment configuration.
        
        Args:
            resource_type: Type of resource ('connections', 'datamodels', etc.).
            
        Returns:
            str: Preferred endpoint URL or None.
        """
        return self.env_config.get_endpoint_url(resource_type)
    
    def detect_platform_by_endpoints(self) -> Dict[str, Any]:
        """
        Detect platform based on endpoint availability using environment configuration.
        
        Returns:
            Dict: Platform information.
        """
        platform_info = self.env_config.detect_platform_capabilities()
        
        # Convert to React-compatible format
        platform = {
            'platform': platform_info.platform.value,
            'version': platform_info.version,
            'is_linux': platform_info.platform == platform_info.platform.LINUX,
            'is_windows': platform_info.platform == platform_info.platform.WINDOWS,
            'supports_v2': platform_info.supports_v2,
            'detected_at': platform_info.detected_at,
            'deployment': platform_info.deployment.value,
            'limitations': platform_info.limitations,
            'supported_endpoints': platform_info.supported_endpoints
        }
        
        return platform