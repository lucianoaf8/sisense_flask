"""
Runtime Endpoint Validation System for Sisense API Integration.

Provides runtime validation of API endpoints before use to prevent
errors from calling non-working endpoints.
"""

import logging
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
from functools import wraps

from config import Config
from sisense.env_config import get_environment_config


class EndpointAvailability(Enum):
    """Endpoint availability status."""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


@dataclass
class EndpointValidationCache:
    """Cache for endpoint validation results."""
    endpoint: str
    availability: EndpointAvailability
    last_checked: float
    status_code: int = 0
    error_message: str = ""
    
    def is_expired(self, cache_duration: int = 300) -> bool:
        """Check if cache entry is expired."""
        return time.time() - self.last_checked > cache_duration


class RuntimeEndpointValidator:
    """
    Runtime endpoint validation system.
    
    Validates endpoints before use and caches results to avoid
    repeated failed API calls.
    """

    def __init__(self):
        """Initialize the runtime validator."""
        self.logger = logging.getLogger(__name__)
        self.env_config = get_environment_config()
        
        # Validation cache
        self.validation_cache: Dict[str, EndpointValidationCache] = {}
        self.cache_duration = 300  # 5 minutes default
        
        # Known endpoint mappings based on platform
        self.known_working_endpoints = self._get_known_working_endpoints()
        self.known_broken_endpoints = self._get_known_broken_endpoints()
        
        self.logger.debug("Initialized runtime endpoint validator")

    def _get_known_working_endpoints(self) -> List[str]:
        """Get list of known working endpoints based on platform detection."""
        platform = self.env_config.detect_platform_capabilities()
        
        # Base working endpoints (confirmed from analysis)
        working = [
            "/api/v1/dashboards",
        ]
        
        # Platform-specific additions
        if platform.supports_v2:
            working.extend([
                "/api/v2/connections",
            ])
        else:
            working.extend([
                "/api/v1/elasticubes/getElasticubes",
                "/api/v1/connection"
            ])
        
        return working

    def _get_known_broken_endpoints(self) -> List[str]:
        """Get list of known broken endpoints based on analysis."""
        # These endpoints consistently return 404/422 in our analysis
        broken = [
            "/api/v1/authentication/me",
            "/api/v1/authentication",
            "/api/v1/users/me",
            "/api/users/me",
            "/api/v2/datamodels",
            "/api/v1/elasticubes",
            "/api/elasticubes",
            "/api/v1/widgets",
            "/api/widgets"
        ]
        
        return broken

    def validate_endpoint_quickly(self, endpoint: str) -> EndpointAvailability:
        """
        Quickly validate endpoint availability using cached results and known patterns.
        
        Args:
            endpoint: API endpoint to validate.
            
        Returns:
            EndpointAvailability: Availability status.
        """
        # Check cache first
        if endpoint in self.validation_cache:
            cache_entry = self.validation_cache[endpoint]
            if not cache_entry.is_expired(self.cache_duration):
                self.logger.debug(f"Using cached result for {endpoint}: {cache_entry.availability.value}")
                return cache_entry.availability
        
        # Check known working endpoints
        if endpoint in self.known_working_endpoints:
            self.logger.debug(f"Endpoint {endpoint} is in known working list")
            self._cache_result(endpoint, EndpointAvailability.AVAILABLE, 200, "")
            return EndpointAvailability.AVAILABLE
        
        # Check known broken endpoints
        if endpoint in self.known_broken_endpoints:
            self.logger.debug(f"Endpoint {endpoint} is in known broken list")
            self._cache_result(endpoint, EndpointAvailability.UNAVAILABLE, 404, "Known broken endpoint")
            return EndpointAvailability.UNAVAILABLE
        
        # For unknown endpoints, return unknown (could be validated later)
        self.logger.debug(f"Endpoint {endpoint} availability unknown")
        return EndpointAvailability.UNKNOWN

    def validate_endpoint_with_test(self, endpoint: str, timeout: int = 5) -> EndpointAvailability:
        """
        Validate endpoint with actual API test call.
        
        Args:
            endpoint: API endpoint to validate.
            timeout: Request timeout in seconds.
            
        Returns:
            EndpointAvailability: Availability status.
        """
        # Check cache first
        quick_result = self.validate_endpoint_quickly(endpoint)
        if quick_result != EndpointAvailability.UNKNOWN:
            return quick_result
        
        self.logger.debug(f"Testing endpoint {endpoint} with API call")
        
        try:
            # Import here to avoid circular imports
            from sisense.auth import get_auth_headers
            from sisense.utils import get_http_client
            
            http_client = get_http_client()
            headers = get_auth_headers()
            
            # Make a lightweight test call
            response_data = http_client.get(
                endpoint=endpoint,
                headers=headers,
                timeout=timeout
            )
            
            # If we got here without exception, endpoint is available
            self.logger.debug(f"Endpoint {endpoint} test successful")
            self._cache_result(endpoint, EndpointAvailability.AVAILABLE, 200, "")
            return EndpointAvailability.AVAILABLE
            
        except Exception as e:
            error_message = str(e)
            
            # Determine status code from error
            status_code = 0
            if "404" in error_message:
                status_code = 404
            elif "422" in error_message:
                status_code = 422
            elif "401" in error_message:
                status_code = 401
            elif "403" in error_message:
                status_code = 403
            
            self.logger.debug(f"Endpoint {endpoint} test failed: {error_message}")
            self._cache_result(endpoint, EndpointAvailability.UNAVAILABLE, status_code, error_message)
            return EndpointAvailability.UNAVAILABLE

    def _cache_result(self, endpoint: str, availability: EndpointAvailability, 
                     status_code: int, error_message: str):
        """Cache validation result."""
        self.validation_cache[endpoint] = EndpointValidationCache(
            endpoint=endpoint,
            availability=availability,
            last_checked=time.time(),
            status_code=status_code,
            error_message=error_message
        )

    def get_alternative_endpoint(self, endpoint: str) -> Optional[str]:
        """
        Get alternative endpoint if the requested one is not available.
        
        Args:
            endpoint: Original endpoint.
            
        Returns:
            str: Alternative endpoint or None.
        """
        # Endpoint alternatives based on functionality
        alternatives = {
            # Authentication alternatives
            "/api/v1/authentication/me": "/api/v1/dashboards",  # Use for auth validation
            "/api/v1/users/me": "/api/v1/dashboards",
            "/api/users/me": "/api/v1/dashboards",
            
            # Data model alternatives
            "/api/v2/datamodels": "/api/v1/elasticubes/getElasticubes",
            "/api/v1/elasticubes": "/api/v1/elasticubes/getElasticubes",
            "/api/elasticubes": "/api/v1/elasticubes/getElasticubes",
            
            # Connection alternatives
            "/api/v1/connection": "/api/v2/connections",
            "/api/connection": "/api/v2/connections",
            
            # Widget alternatives
            "/api/v1/widgets": None,  # No working alternative found
            "/api/widgets": None,
        }
        
        alternative = alternatives.get(endpoint)
        
        # Validate alternative if provided
        if alternative:
            alt_availability = self.validate_endpoint_quickly(alternative)
            if alt_availability == EndpointAvailability.AVAILABLE:
                self.logger.info(f"Using alternative endpoint {alternative} for {endpoint}")
                return alternative
        
        return None

    def is_endpoint_available(self, endpoint: str, test_if_unknown: bool = False) -> bool:
        """
        Check if endpoint is available.
        
        Args:
            endpoint: API endpoint to check.
            test_if_unknown: Whether to test unknown endpoints with API calls.
            
        Returns:
            bool: True if endpoint is available.
        """
        if test_if_unknown:
            availability = self.validate_endpoint_with_test(endpoint)
        else:
            availability = self.validate_endpoint_quickly(endpoint)
        
        return availability == EndpointAvailability.AVAILABLE

    def get_validation_report(self) -> Dict[str, Any]:
        """
        Get comprehensive validation report.
        
        Returns:
            Dict: Validation report with cache status and recommendations.
        """
        cached_available = []
        cached_unavailable = []
        
        for endpoint, cache_entry in self.validation_cache.items():
            if cache_entry.availability == EndpointAvailability.AVAILABLE:
                cached_available.append({
                    "endpoint": endpoint,
                    "last_checked": cache_entry.last_checked,
                    "status_code": cache_entry.status_code
                })
            else:
                cached_unavailable.append({
                    "endpoint": endpoint,
                    "last_checked": cache_entry.last_checked,
                    "status_code": cache_entry.status_code,
                    "error": cache_entry.error_message
                })
        
        return {
            "cache_stats": {
                "total_cached": len(self.validation_cache),
                "available_endpoints": len(cached_available),
                "unavailable_endpoints": len(cached_unavailable),
                "cache_duration": self.cache_duration
            },
            "known_working": self.known_working_endpoints,
            "known_broken": self.known_broken_endpoints,
            "cached_available": cached_available,
            "cached_unavailable": cached_unavailable,
            "platform_info": {
                "platform": self.env_config.detect_platform_capabilities().platform.value,
                "supports_v2": self.env_config.detect_platform_capabilities().supports_v2
            }
        }


# Global validator instance
_runtime_validator = None


def get_runtime_validator() -> RuntimeEndpointValidator:
    """Get singleton runtime validator instance."""
    global _runtime_validator
    if _runtime_validator is None:
        _runtime_validator = RuntimeEndpointValidator()
    return _runtime_validator


def validate_endpoint(endpoint: str, test_if_unknown: bool = False) -> bool:
    """
    Validate endpoint availability.
    
    Args:
        endpoint: API endpoint to validate.
        test_if_unknown: Whether to test unknown endpoints.
        
    Returns:
        bool: True if endpoint is available.
    """
    validator = get_runtime_validator()
    return validator.is_endpoint_available(endpoint, test_if_unknown)


def endpoint_validator(test_unknown: bool = False, use_alternative: bool = True):
    """
    Decorator for endpoint validation.
    
    Args:
        test_unknown: Whether to test unknown endpoints.
        use_alternative: Whether to use alternative endpoints if original fails.
        
    Returns:
        Decorator function.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract endpoint from function arguments or name
            endpoint = None
            
            # Try to find endpoint in kwargs
            if 'endpoint' in kwargs:
                endpoint = kwargs['endpoint']
            elif args and isinstance(args[0], str) and args[0].startswith('/api/'):
                endpoint = args[0]
            
            if endpoint:
                validator = get_runtime_validator()
                
                # Check if endpoint is available
                if not validator.is_endpoint_available(endpoint, test_unknown):
                    # Try to get alternative if enabled
                    if use_alternative:
                        alternative = validator.get_alternative_endpoint(endpoint)
                        if alternative:
                            # Replace endpoint with alternative
                            if 'endpoint' in kwargs:
                                kwargs['endpoint'] = alternative
                            elif args and isinstance(args[0], str):
                                args = (alternative,) + args[1:]
                            
                            logging.getLogger(__name__).info(
                                f"Replaced unavailable endpoint {endpoint} with {alternative}"
                            )
                        else:
                            # No alternative available
                            from sisense.utils import SisenseAPIError
                            raise SisenseAPIError(
                                f"Endpoint {endpoint} is not available in this Sisense environment. "
                                f"No working alternative found."
                            )
                    else:
                        # Endpoint not available and alternatives disabled
                        from sisense.utils import SisenseAPIError
                        raise SisenseAPIError(
                            f"Endpoint {endpoint} is not available in this Sisense environment."
                        )
            
            # Call original function
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def validate_endpoints_for_module(module_name: str, endpoints: List[str]) -> Dict[str, bool]:
    """
    Validate multiple endpoints for a module.
    
    Args:
        module_name: Name of the module.
        endpoints: List of endpoints to validate.
        
    Returns:
        Dict[str, bool]: Validation results for each endpoint.
    """
    validator = get_runtime_validator()
    logger = logging.getLogger(__name__)
    
    logger.info(f"Validating {len(endpoints)} endpoints for {module_name}")
    
    results = {}
    available_count = 0
    
    for endpoint in endpoints:
        is_available = validator.is_endpoint_available(endpoint)
        results[endpoint] = is_available
        
        if is_available:
            available_count += 1
            logger.debug(f"✅ {endpoint} - Available")
        else:
            alternative = validator.get_alternative_endpoint(endpoint)
            if alternative:
                logger.info(f"⚠️  {endpoint} - Not available, alternative: {alternative}")
            else:
                logger.warning(f"❌ {endpoint} - Not available, no alternative")
    
    logger.info(f"{module_name}: {available_count}/{len(endpoints)} endpoints available")
    
    return results


# Example usage functions for integration
def validate_dashboard_endpoints() -> Dict[str, bool]:
    """Validate dashboard-related endpoints."""
    endpoints = [
        "/api/v1/dashboards",
        "/api/dashboards",
        "/api/v1/dashboards/{id}/widgets"
    ]
    return validate_endpoints_for_module("dashboards", endpoints)


def validate_connection_endpoints() -> Dict[str, bool]:
    """Validate connection-related endpoints."""
    endpoints = [
        "/api/v2/connections",
        "/api/v1/connection",
        "/api/connection"
    ]
    return validate_endpoints_for_module("connections", endpoints)


def validate_datamodel_endpoints() -> Dict[str, bool]:
    """Validate data model related endpoints."""
    endpoints = [
        "/api/v2/datamodels",
        "/api/v1/elasticubes",
        "/api/elasticubes",
        "/api/v1/elasticubes/getElasticubes"
    ]
    return validate_endpoints_for_module("datamodels", endpoints)


def main():
    """Demo runtime validation functionality."""
    import logging
    
    logging.basicConfig(level=logging.INFO)
    
    print("🔍 Runtime Endpoint Validator Demo")
    print("=" * 40)
    
    validator = get_runtime_validator()
    
    # Test known endpoints
    test_endpoints = [
        "/api/v1/dashboards",
        "/api/v2/connections", 
        "/api/v2/datamodels",
        "/api/v1/authentication/me",
        "/api/v1/widgets"
    ]
    
    print("Testing endpoint availability:")
    for endpoint in test_endpoints:
        is_available = validator.is_endpoint_available(endpoint)
        status = "✅ Available" if is_available else "❌ Not Available"
        print(f"  {endpoint}: {status}")
        
        if not is_available:
            alternative = validator.get_alternative_endpoint(endpoint)
            if alternative:
                print(f"    Alternative: {alternative}")
    
    # Generate validation report
    report = validator.get_validation_report()
    
    print(f"\n📊 Validation Report:")
    print(f"Known Working: {len(report['known_working'])}")
    print(f"Known Broken: {len(report['known_broken'])}")
    print(f"Cache Entries: {report['cache_stats']['total_cached']}")
    print(f"Platform: {report['platform_info']['platform']}")
    
    print(f"\n💡 Recommendations:")
    print("- Use @endpoint_validator decorator on API functions")
    print("- Enable use_alternative=True for automatic fallbacks")
    print("- Call validate_endpoints_for_module() during module initialization")


if __name__ == "__main__":
    main()