"""
Optimized HTTP Client for Sisense API Integration.

Provides enhanced reliability, performance, and error handling through:
- Connection pooling for better performance
- Intelligent rate limiting to prevent 429 errors
- Exponential backoff with jitter for retries
- Circuit breaker pattern for failing endpoints
- Comprehensive request/response logging
- Endpoint-specific timeout optimization
"""

import logging
import time
import random
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union, Deque
from urllib.parse import urljoin, urlparse
import hashlib

import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException
from urllib3.util.retry import Retry
from urllib3.poolmanager import PoolManager

from config import Config
from sisense.utils import SisenseAPIError
from sisense.env_config import get_environment_config


@dataclass
class RequestMetrics:
    """Metrics for request monitoring."""
    endpoint: str
    method: str
    status_code: int
    response_time_ms: float
    request_size: int
    response_size: int
    timestamp: datetime
    error_message: str = ""


@dataclass
class CircuitBreakerState:
    """Circuit breaker state for an endpoint."""
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    state: str = "closed"  # closed, open, half_open
    next_attempt_time: Optional[datetime] = None
    success_count: int = 0
    total_requests: int = 0


@dataclass
class RateLimitState:
    """Rate limiting state for rate limiting."""
    request_times: Deque[float] = field(default_factory=lambda: deque(maxlen=100))
    last_429_time: Optional[float] = None
    retry_after: int = 0
    requests_per_minute: int = 60  # Default limit


class OptimizedHTTPAdapter(HTTPAdapter):
    """Optimized HTTP adapter with connection pooling."""
    
    def __init__(self, pool_connections=20, pool_maxsize=50, max_retries=0, 
                 pool_block=False, **kwargs):
        """
        Initialize optimized adapter.
        
        Args:
            pool_connections: Number of connection pools to cache
            pool_maxsize: Maximum number of connections in each pool
            max_retries: Maximum retries (we handle this manually)
            pool_block: Whether to block when pool is full
        """
        super().__init__(max_retries=max_retries, **kwargs)
        self.config = {
            'pool_connections': pool_connections,
            'pool_maxsize': pool_maxsize,
            'pool_block': pool_block
        }
    
    def init_poolmanager(self, *args, **kwargs):
        """Initialize the pool manager with optimized settings."""
        kwargs.update(self.config)
        return super().init_poolmanager(*args, **kwargs)


class OptimizedSisenseHTTPClient:
    """
    Optimized HTTP client for Sisense API with enhanced reliability and performance.
    
    Features:
    - Connection pooling for improved performance
    - Exponential backoff with jitter for retries
    - Intelligent rate limiting based on 429 responses
    - Circuit breaker pattern for failing endpoints
    - Comprehensive request/response logging
    - Endpoint-specific timeout configuration
    """

    def __init__(self):
        """Initialize the optimized HTTP client."""
        self.logger = logging.getLogger(__name__)
        self.env_config = get_environment_config()
        self.base_url = Config.get_sisense_base_url()
        
        # Performance and reliability settings
        self.retry_attempts = Config.REQUEST_RETRIES
        self.base_timeout = Config.REQUEST_TIMEOUT
        self.base_delay = Config.REQUEST_RETRY_DELAY
        self.backoff_factor = Config.REQUEST_RETRY_BACKOFF
        
        # Enhanced configuration
        self.max_jitter = 1.0  # Maximum jitter in seconds
        self.circuit_breaker_threshold = 5  # Failures before opening circuit
        self.circuit_breaker_timeout = 60  # Seconds before trying half-open
        self.rate_limit_buffer = 0.9  # Use 90% of detected rate limit
        
        # Monitoring and state
        self.request_metrics: Deque[RequestMetrics] = deque(maxlen=1000)
        self.circuit_breakers: Dict[str, CircuitBreakerState] = defaultdict(CircuitBreakerState)
        self.rate_limiters: Dict[str, RateLimitState] = defaultdict(RateLimitState)
        self._lock = threading.Lock()
        
        # Session configuration
        self.session = self._create_optimized_session()
        
        # Endpoint-specific timeout mapping
        self.endpoint_timeouts = self._configure_endpoint_timeouts()
        
        self.logger.info("Initialized optimized Sisense HTTP client")

    def _create_optimized_session(self) -> requests.Session:
        """Create session with optimized connection pooling."""
        session = requests.Session()
        
        # Optimized adapter with connection pooling
        adapter = OptimizedHTTPAdapter(
            pool_connections=20,  # Number of connection pools
            pool_maxsize=50,      # Max connections per pool
            pool_block=False,     # Don't block when pool is full
            max_retries=0         # We handle retries manually
        )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # SSL configuration
        session.verify = Config.SSL_VERIFY
        if Config.SSL_CERT_PATH:
            session.verify = Config.SSL_CERT_PATH
        
        # Default headers
        session.headers.update({
            'User-Agent': 'SisenseFlaskClient/2.0 (Optimized)',
            'Accept': 'application/json',
            'Connection': 'keep-alive'
        })
        
        return session

    def _configure_endpoint_timeouts(self) -> Dict[str, int]:
        """Configure endpoint-specific timeouts."""
        return {
            # Fast endpoints
            '/api/v1/dashboards': self.base_timeout,
            '/api/v2/connections': self.base_timeout,
            '/api/version': 10,  # Version info should be fast
            '/api/health': 10,   # Health checks should be fast
            
            # Slower endpoints (data-heavy)
            '/api/v1/dashboards/{id}/widgets': self.base_timeout * 1.5,
            '/api/v1/widgets/{id}/data': self.base_timeout * 2,
            '/api/v1/datasources/{id}/sql': self.base_timeout * 3,  # SQL queries can be slow
            '/api/v1/datasources/{id}/jaql': self.base_timeout * 3, # JAQL queries can be slow
            
            # Default for unknown endpoints
            'default': self.base_timeout
        }

    def _get_endpoint_timeout(self, endpoint: str) -> int:
        """Get timeout for specific endpoint."""
        # Try exact match first
        if endpoint in self.endpoint_timeouts:
            return self.endpoint_timeouts[endpoint]
        
        # Try pattern matching for parameterized endpoints
        for pattern, timeout in self.endpoint_timeouts.items():
            if '{' in pattern:
                # Simple pattern matching for parameterized endpoints
                pattern_parts = pattern.split('/')
                endpoint_parts = endpoint.split('/')
                
                if len(pattern_parts) == len(endpoint_parts):
                    match = True
                    for p_part, e_part in zip(pattern_parts, endpoint_parts):
                        if p_part != e_part and not p_part.startswith('{'):
                            match = False
                            break
                    if match:
                        return timeout
        
        return self.endpoint_timeouts['default']

    def _get_endpoint_key(self, endpoint: str) -> str:
        """Get normalized endpoint key for circuit breaker and rate limiting."""
        # Normalize parameterized endpoints (e.g., /api/dashboards/123 -> /api/dashboards/{id})
        parts = endpoint.split('/')
        normalized_parts = []
        
        for i, part in enumerate(parts):
            if i > 0 and part and part.replace('-', '').replace('_', '').isalnum() and len(part) > 10:
                # Likely an ID, replace with {id}
                normalized_parts.append('{id}')
            else:
                normalized_parts.append(part)
        
        return '/'.join(normalized_parts)

    def _add_jitter(self, delay: float) -> float:
        """Add jitter to delay to prevent thundering herd."""
        jitter = random.uniform(0, min(delay * 0.1, self.max_jitter))
        return delay + jitter

    def _calculate_backoff_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay with jitter."""
        # Exponential backoff: base_delay * (backoff_factor ^ (attempt - 1))
        delay = self.base_delay * (self.backoff_factor ** (attempt - 1))
        
        # Cap maximum delay
        max_delay = 60.0  # Maximum 60 seconds
        delay = min(delay, max_delay)
        
        # Add jitter
        return self._add_jitter(delay)

    def _check_circuit_breaker(self, endpoint_key: str) -> bool:
        """Check if circuit breaker allows request."""
        with self._lock:
            breaker = self.circuit_breakers[endpoint_key]
            now = datetime.now()
            
            if breaker.state == "open":
                # Check if we should try half-open
                if (breaker.next_attempt_time and 
                    now >= breaker.next_attempt_time):
                    breaker.state = "half_open"
                    breaker.success_count = 0
                    self.logger.info(f"Circuit breaker for {endpoint_key} entering half-open state")
                    return True
                else:
                    self.logger.warning(f"Circuit breaker for {endpoint_key} is open, rejecting request")
                    return False
            
            return True  # closed or half_open

    def _record_circuit_breaker_result(self, endpoint_key: str, success: bool, error_message: str = ""):
        """Record result for circuit breaker."""
        with self._lock:
            breaker = self.circuit_breakers[endpoint_key]
            breaker.total_requests += 1
            now = datetime.now()
            
            if success:
                breaker.failure_count = 0
                breaker.success_count += 1
                
                # If half-open and successful, close the circuit
                if breaker.state == "half_open":
                    breaker.state = "closed"
                    self.logger.info(f"Circuit breaker for {endpoint_key} closed after successful request")
            else:
                breaker.failure_count += 1
                breaker.last_failure_time = now
                
                # Open circuit if failure threshold reached
                if (breaker.state in ["closed", "half_open"] and 
                    breaker.failure_count >= self.circuit_breaker_threshold):
                    breaker.state = "open"
                    breaker.next_attempt_time = now + timedelta(seconds=self.circuit_breaker_timeout)
                    self.logger.warning(
                        f"Circuit breaker for {endpoint_key} opened after {breaker.failure_count} failures. "
                        f"Error: {error_message}"
                    )

    def _check_rate_limit(self, endpoint_key: str) -> bool:
        """Check if request is allowed by rate limiter."""
        with self._lock:
            limiter = self.rate_limiters[endpoint_key]
            now = time.time()
            
            # Check if we're in a rate limit cooldown
            if limiter.last_429_time and limiter.retry_after:
                if now < limiter.last_429_time + limiter.retry_after:
                    remaining = (limiter.last_429_time + limiter.retry_after) - now
                    self.logger.warning(f"Rate limited for {endpoint_key}, waiting {remaining:.1f}s")
                    return False
            
            # Check requests per minute
            # Remove old requests (older than 1 minute)
            cutoff_time = now - 60
            while limiter.request_times and limiter.request_times[0] < cutoff_time:
                limiter.request_times.popleft()
            
            # Check if we're under the limit
            current_rate = len(limiter.request_times)
            if current_rate >= limiter.requests_per_minute * self.rate_limit_buffer:
                self.logger.warning(f"Rate limit approaching for {endpoint_key} ({current_rate} req/min)")
                return False
            
            # Record this request
            limiter.request_times.append(now)
            return True

    def _handle_rate_limit_response(self, endpoint_key: str, response: requests.Response):
        """Handle 429 response and update rate limiting."""
        with self._lock:
            limiter = self.rate_limiters[endpoint_key]
            
            # Parse Retry-After header
            retry_after = response.headers.get('Retry-After', '60')
            try:
                limiter.retry_after = int(retry_after)
            except ValueError:
                limiter.retry_after = 60  # Default to 60 seconds
            
            limiter.last_429_time = time.time()
            
            # Parse rate limit headers if available
            rate_limit_headers = [
                'X-RateLimit-Limit',
                'X-Rate-Limit-Limit', 
                'RateLimit-Limit'
            ]
            
            for header in rate_limit_headers:
                if header in response.headers:
                    try:
                        limit = int(response.headers[header])
                        limiter.requests_per_minute = limit
                        self.logger.info(f"Updated rate limit for {endpoint_key} to {limit} req/min")
                        break
                    except ValueError:
                        pass
            
            self.logger.warning(f"Rate limited for {endpoint_key}, retry after {limiter.retry_after}s")

    def _log_request(self, method: str, url: str, headers: Dict, params: Dict, 
                    data: Any, json_data: Dict, timeout: int):
        """Log request details for debugging."""
        if self.logger.isEnabledFor(logging.DEBUG):
            # Safe header logging (hide sensitive data)
            safe_headers = {k: v for k, v in (headers or {}).items() 
                          if k.lower() not in ['authorization', 'x-api-key']}
            if 'authorization' in (headers or {}):
                safe_headers['authorization'] = '[REDACTED]'
            
            self.logger.debug(f"HTTP Request: {method} {url}")
            self.logger.debug(f"Headers: {safe_headers}")
            self.logger.debug(f"Params: {params}")
            self.logger.debug(f"Timeout: {timeout}s")
            
            if json_data and self.logger.isEnabledFor(logging.DEBUG):
                self.logger.debug(f"JSON Body: {json_data}")

    def _log_response(self, response: requests.Response, response_time_ms: float):
        """Log response details for debugging."""
        self.logger.debug(f"HTTP Response: {response.status_code} ({response_time_ms:.1f}ms)")
        self.logger.debug(f"Response Headers: {dict(response.headers)}")
        
        if self.logger.isEnabledFor(logging.DEBUG) and response.content:
            content_type = response.headers.get('content-type', '')
            if 'application/json' in content_type:
                try:
                    json_content = response.json()
                    # Truncate large responses for logging
                    if len(str(json_content)) > 1000:
                        self.logger.debug("Response Body: [Large JSON response - truncated]")
                    else:
                        self.logger.debug(f"Response Body: {json_content}")
                except:
                    self.logger.debug("Response Body: [Invalid JSON]")

    def _record_metrics(self, endpoint: str, method: str, status_code: int,
                       response_time_ms: float, request_size: int, response_size: int,
                       error_message: str = ""):
        """Record request metrics."""
        metrics = RequestMetrics(
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time_ms=response_time_ms,
            request_size=request_size,
            response_size=response_size,
            timestamp=datetime.now(),
            error_message=error_message
        )
        
        self.request_metrics.append(metrics)

    def _build_url(self, endpoint: str) -> str:
        """Build URL for API endpoint (inherited from base implementation)."""
        # Get environment profile for URL construction strategy
        env_profile = self.env_config.get_environment_profile()
        
        # Apply base path override if configured
        if Config.SISENSE_BASE_PATH_OVERRIDE:
            base_path = Config.SISENSE_BASE_PATH_OVERRIDE.strip('/')
            if endpoint.startswith('/api/'):
                endpoint = f"/{base_path}{endpoint}"
        
        # Match React pattern: relative URLs in development, absolute in production
        if env_profile['is_development'] and 'localhost' in (Config.SISENSE_URL or ''):
            return endpoint
        
        return urljoin(self.base_url, endpoint.lstrip('/'))

    def _handle_response(self, response: requests.Response) -> Dict[Any, Any]:
        """Handle HTTP response and extract data (inherited from base implementation)."""
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
            
            raise SisenseAPIError(
                message=error_message,
                status_code=response.status_code,
                response_data=response_data
            )
        
        return response_data

    def request_with_optimization(
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
        Make HTTP request with all optimizations enabled.
        
        Args:
            method: HTTP method
            endpoint: API endpoint path
            headers: Optional headers
            params: Optional query parameters
            data: Optional form data
            json: Optional JSON data
            timeout: Optional timeout override
            attempt: Current attempt number
            
        Returns:
            Dict: Response data
            
        Raises:
            SisenseAPIError: If request fails after all retries
        """
        url = self._build_url(endpoint)
        endpoint_key = self._get_endpoint_key(endpoint)
        request_timeout = timeout or self._get_endpoint_timeout(endpoint)
        
        # Circuit breaker check
        if not self._check_circuit_breaker(endpoint_key):
            raise SisenseAPIError(
                f"Circuit breaker is open for {endpoint_key}",
                status_code=503
            )
        
        # Rate limiting check
        if not self._check_rate_limit(endpoint_key):
            # Wait for rate limit and retry
            limiter = self.rate_limiters[endpoint_key]
            if limiter.last_429_time and limiter.retry_after:
                wait_time = max(0, (limiter.last_429_time + limiter.retry_after) - time.time())
                if wait_time > 0:
                    self.logger.info(f"Waiting {wait_time:.1f}s for rate limit")
                    time.sleep(wait_time)
        
        # Prepare headers
        if headers is None:
            headers = {}
        
        # Add environment-specific headers
        env_headers = self.env_config.get_platform_headers()
        headers.update(env_headers)
        
        # Calculate request size for metrics
        request_size = 0
        if data:
            request_size = len(str(data))
        elif json:
            request_size = len(str(json))
        
        # Log request
        self._log_request(method, url, headers, params, data, json, request_timeout)
        
        start_time = time.time()
        response = None
        error_message = ""
        
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
            
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            response_size = len(response.content) if response.content else 0
            
            # Log response
            self._log_response(response, response_time_ms)
            
            # Handle rate limiting
            if response.status_code == 429:
                self._handle_rate_limit_response(endpoint_key, response)
                
                # Record metrics for rate limited request
                self._record_metrics(
                    endpoint, method, response.status_code, response_time_ms,
                    request_size, response_size, "Rate limited"
                )
                
                # Retry if we have attempts left
                if attempt < self.retry_attempts:
                    delay = self._calculate_backoff_delay(attempt)
                    self.logger.info(f"Rate limited, retrying in {delay:.1f}s (attempt {attempt + 1})")
                    time.sleep(delay)
                    return self.request_with_optimization(
                        method, endpoint, headers, params, data, json, timeout, attempt + 1
                    )
                else:
                    # Record circuit breaker failure and raise
                    self._record_circuit_breaker_result(endpoint_key, False, "Rate limited")
                    raise SisenseAPIError("Rate limited", status_code=429)
            
            # Process successful response
            response_data = self._handle_response(response)
            
            # Record metrics and circuit breaker success
            self._record_metrics(
                endpoint, method, response.status_code, response_time_ms,
                request_size, response_size
            )
            self._record_circuit_breaker_result(endpoint_key, True)
            
            return response_data
            
        except (RequestException, SisenseAPIError) as e:
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            error_message = str(e)
            status_code = getattr(e, 'status_code', 0)
            
            # Record metrics for failed request
            self._record_metrics(
                endpoint, method, status_code, response_time_ms,
                request_size, 0, error_message
            )
            
            # Check if we should retry
            should_retry = (
                attempt < self.retry_attempts and
                not self._is_abort_error(e) and
                self._is_retryable_error(e)
            )
            
            if should_retry:
                delay = self._calculate_backoff_delay(attempt)
                self.logger.warning(
                    f"Request failed, retrying in {delay:.1f}s "
                    f"(attempt {attempt + 1}/{self.retry_attempts}): {error_message}"
                )
                time.sleep(delay)
                return self.request_with_optimization(
                    method, endpoint, headers, params, data, json, timeout, attempt + 1
                )
            else:
                # Record circuit breaker failure
                self._record_circuit_breaker_result(endpoint_key, False, error_message)
                
                self.logger.error(f"Request failed after {attempt} attempts: {error_message}")
                
                if isinstance(e, SisenseAPIError):
                    raise e
                else:
                    raise SisenseAPIError(f"Request failed: {error_message}")

    def _is_abort_error(self, error: Exception) -> bool:
        """Check if error should not be retried."""
        error_str = str(error).lower()
        return (
            'timeout' in error_str or 
            'abort' in error_str or
            'connection aborted' in error_str
        )

    def _is_retryable_error(self, error: Exception) -> bool:
        """Check if error is retryable."""
        if isinstance(error, SisenseAPIError):
            # Retry on server errors, but not client errors
            return error.status_code >= 500 or error.status_code == 429
        
        # Retry on connection errors
        return isinstance(error, RequestException)

    # Convenience methods that use the optimized request
    def request(self, method: str, endpoint: str, **kwargs) -> Dict[Any, Any]:
        """Make optimized HTTP request."""
        return self.request_with_optimization(method, endpoint, **kwargs)

    def get(self, endpoint: str, **kwargs) -> Dict[Any, Any]:
        """Make optimized GET request."""
        return self.request_with_optimization("GET", endpoint, **kwargs)

    def post(self, endpoint: str, **kwargs) -> Dict[Any, Any]:
        """Make optimized POST request."""
        return self.request_with_optimization("POST", endpoint, **kwargs)

    def put(self, endpoint: str, **kwargs) -> Dict[Any, Any]:
        """Make optimized PUT request."""
        return self.request_with_optimization("PUT", endpoint, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> Dict[Any, Any]:
        """Make optimized DELETE request."""
        return self.request_with_optimization("DELETE", endpoint, **kwargs)

    # Monitoring and diagnostics
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for monitoring."""
        if not self.request_metrics:
            return {"error": "No metrics available"}
        
        # Calculate statistics
        response_times = [m.response_time_ms for m in self.request_metrics]
        status_codes = [m.status_code for m in self.request_metrics]
        
        success_count = sum(1 for code in status_codes if 200 <= code < 300)
        error_count = len(status_codes) - success_count
        
        return {
            "total_requests": len(self.request_metrics),
            "success_rate": (success_count / len(status_codes)) * 100,
            "avg_response_time_ms": sum(response_times) / len(response_times),
            "min_response_time_ms": min(response_times),
            "max_response_time_ms": max(response_times),
            "p95_response_time_ms": sorted(response_times)[int(len(response_times) * 0.95)],
            "error_count": error_count,
            "recent_errors": [
                {"endpoint": m.endpoint, "error": m.error_message, "time": m.timestamp.isoformat()}
                for m in list(self.request_metrics)[-10:] if m.error_message
            ]
        }

    def get_circuit_breaker_status(self) -> Dict[str, Dict[str, Any]]:
        """Get circuit breaker status for all endpoints."""
        status = {}
        for endpoint_key, breaker in self.circuit_breakers.items():
            status[endpoint_key] = {
                "state": breaker.state,
                "failure_count": breaker.failure_count,
                "total_requests": breaker.total_requests,
                "last_failure": breaker.last_failure_time.isoformat() if breaker.last_failure_time else None,
                "next_attempt": breaker.next_attempt_time.isoformat() if breaker.next_attempt_time else None
            }
        return status

    def get_rate_limit_status(self) -> Dict[str, Dict[str, Any]]:
        """Get rate limiting status for all endpoints."""
        status = {}
        for endpoint_key, limiter in self.rate_limiters.items():
            now = time.time()
            current_requests = sum(1 for t in limiter.request_times if t > now - 60)
            
            status[endpoint_key] = {
                "requests_per_minute": limiter.requests_per_minute,
                "current_requests": current_requests,
                "utilization_percent": (current_requests / limiter.requests_per_minute) * 100,
                "last_429_time": limiter.last_429_time,
                "retry_after": limiter.retry_after
            }
        return status

    def reset_circuit_breaker(self, endpoint_key: str = None):
        """Reset circuit breaker(s)."""
        with self._lock:
            if endpoint_key:
                if endpoint_key in self.circuit_breakers:
                    self.circuit_breakers[endpoint_key] = CircuitBreakerState()
                    self.logger.info(f"Reset circuit breaker for {endpoint_key}")
            else:
                self.circuit_breakers.clear()
                self.logger.info("Reset all circuit breakers")


# Global optimized client instance
_optimized_client = None


def get_optimized_http_client() -> OptimizedSisenseHTTPClient:
    """Get singleton optimized HTTP client instance."""
    global _optimized_client
    if _optimized_client is None:
        _optimized_client = OptimizedSisenseHTTPClient()
    return _optimized_client