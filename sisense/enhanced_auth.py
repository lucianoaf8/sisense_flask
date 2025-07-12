"""
Enhanced authentication module with real validation and caching.
"""

import logging
import time
from typing import Dict, Optional, Tuple
from functools import lru_cache

from config import Config
from sisense.utils import SisenseAPIError, get_http_client

logger = logging.getLogger(__name__)

# Cache for token validation results (token_hash -> (is_valid, timestamp))
_token_validation_cache = {}
_cache_duration = 300  # 5 minutes

def get_auth_headers() -> Dict[str, str]:
    """Get authentication headers with API token."""
    if Config.DEMO_MODE:
        return {"Authorization": "Bearer demo-token", "Content-Type": "application/json"}
    
    if not Config.SISENSE_API_TOKEN:
        raise SisenseAPIError("SISENSE_API_TOKEN is not configured")
    
    return Config.get_auth_headers(Config.SISENSE_API_TOKEN)

def validate_authentication() -> Tuple[bool, str]:
    """
    Validate API token against Sisense API with caching.
    Uses /api/v1/dashboards endpoint as it's confirmed working.
    
    Returns:
        Tuple[bool, str]: (is_valid, status_message)
    """
    # Demo mode - return simulated success
    if Config.DEMO_MODE:
        return True, "valid (demo mode)"
    
    if not Config.SISENSE_API_TOKEN:
        return False, "API token not configured"
    
    # Check cache first
    token_hash = hash(Config.SISENSE_API_TOKEN)
    current_time = time.time()
    
    if token_hash in _token_validation_cache:
        is_valid, timestamp = _token_validation_cache[token_hash]
        if current_time - timestamp < _cache_duration:
            status = "valid (cached)" if is_valid else "invalid (cached)"
            return is_valid, status
    
    # Validate against Sisense API using confirmed working endpoint
    try:
        http_client = get_http_client()
        headers = get_auth_headers()
        
        # Use /api/v1/dashboards as validation endpoint - confirmed working
        logger.debug("Validating API token using /api/v1/dashboards endpoint")
        response = http_client.get('/api/v1/dashboards', headers=headers)
        
        is_valid = True
        status = "valid"
        logger.info("API token validation successful using /api/v1/dashboards endpoint")
        
    except Exception as e:
        is_valid = False
        # Provide more specific error messages
        error_msg = str(e)
        if "404" in error_msg:
            status = "invalid: dashboards endpoint not found (404)"
        elif "422" in error_msg:
            status = "invalid: dashboards endpoint unprocessable (422)"
        elif "401" in error_msg or "403" in error_msg:
            status = "invalid: authentication failed - check API token"
        else:
            status = f"invalid: {error_msg}"
        
        logger.warning(f"API token validation failed using /api/v1/dashboards: {error_msg}")
    
    # Cache result
    _token_validation_cache[token_hash] = (is_valid, current_time)
    
    return is_valid, status

def invalidate_token_cache() -> None:
    """Clear token validation cache."""
    global _token_validation_cache
    _token_validation_cache.clear()
    logger.debug("Token validation cache cleared")

@lru_cache(maxsize=1)
def get_user_info() -> Optional[Dict]:
    """Get current user information with caching."""
    # Demo mode - return simulated user info
    if Config.DEMO_MODE:
        return {
            "userId": "demo-user-123",
            "userName": "Demo User",
            "email": "demo@example.com",
            "firstName": "Demo",
            "lastName": "User",
            "groups": ["Demo Group"]
        }
    
    # Since authentication endpoints don't work, return basic info based on token presence
    if Config.SISENSE_API_TOKEN:
        logger.info("User info endpoints not available - returning token-based info")
        return {
            "authenticated": True,
            "token_present": True,
            "note": "User details not available from API"
        }
    else:
        logger.error("No API token configured")
        return None

def login() -> str:
    """Get API token and validate it."""
    if not Config.SISENSE_API_TOKEN:
        raise SisenseAPIError("SISENSE_API_TOKEN is not configured")
    
    # Validate token on login
    is_valid, message = validate_authentication()
    if not is_valid:
        raise SisenseAPIError(f"Invalid API token: {message}")
    
    logger.debug("API token validated successfully")
    return Config.SISENSE_API_TOKEN

def get_connection_health() -> Dict[str, any]:
    """
    Get detailed connection health information.
    
    Returns:
        Dict containing health metrics and status
    """
    start_time = time.time()
    
    # Demo mode - return simulated health data
    if Config.DEMO_MODE:
        return {
            'overall_status': 'healthy',
            'authentication': 'valid (demo mode)',
            'sisense_url': 'Demo Mode - No real connection',
            'timestamp': time.time(),
            'response_time_ms': 50.0,
            'health_checks': {
                'Authentication': {'status': 'healthy', 'response_time_ms': 15.0, 'error': None},
                'Data Models': {'status': 'healthy', 'response_time_ms': 20.0, 'error': None},
                'Dashboards': {'status': 'healthy', 'response_time_ms': 15.0, 'error': None}
            },
            'demo_mode': True
        }
    
    try:
        # Test basic connectivity
        http_client = get_http_client()
        headers = get_auth_headers()
        
        # Test only confirmed working endpoints (no fallback logic)
        endpoints_to_test = [
            ('/api/v1/dashboards', 'Dashboards'),
            ('/api/v2/connections', 'Connections')
        ]
        
        # Note: Data Models endpoints are not available in this environment
        
        health_results = {}
        overall_healthy = True
        total_response_time = 0
        
        for endpoint, name in endpoints_to_test:
            endpoint_start = time.time()
            
            try:
                logger.debug(f"Testing endpoint: {endpoint}")
                response = http_client.get(endpoint, headers=headers)
                endpoint_time = (time.time() - endpoint_start) * 1000  # Convert to ms
                
                health_results[name] = {
                    'status': 'healthy',
                    'response_time_ms': round(endpoint_time, 2),
                    'error': None,
                    'endpoint_used': endpoint
                }
                total_response_time += endpoint_time
                logger.debug(f"Endpoint {endpoint} is healthy")
                
            except Exception as e:
                endpoint_time = (time.time() - endpoint_start) * 1000
                error_detail = str(e)
                logger.warning(f"{name} endpoint failed: {error_detail}")
                health_results[name] = {
                    'status': 'unhealthy',
                    'response_time_ms': round(endpoint_time, 2),
                    'error': error_detail,
                    'endpoint_used': endpoint
                }
                overall_healthy = False
        
        # Add note about unavailable services
        health_results['Data Models'] = {
            'status': 'unavailable',
            'response_time_ms': 0,
            'error': 'Data models endpoints not available in this Sisense environment',
            'endpoint_used': 'N/A'
        }
        
        avg_response_time = total_response_time / len(endpoints_to_test)
        total_time = (time.time() - start_time) * 1000
        
        # Determine connection quality based on response times
        if avg_response_time < 100:
            quality = 'excellent'
        elif avg_response_time < 300:
            quality = 'good'
        elif avg_response_time < 1000:
            quality = 'fair'
        else:
            quality = 'poor'
        
        return {
            'overall_status': 'healthy' if overall_healthy else 'degraded',
            'connection_quality': quality,
            'total_check_time_ms': round(total_time, 2),
            'average_response_time_ms': round(avg_response_time, 2),
            'endpoints': health_results,
            'timestamp': time.time(),
            'sisense_url': Config.get_sisense_base_url()
        }
        
    except Exception as e:
        total_time = (time.time() - start_time) * 1000
        logger.error(f"Connection health check failed: {e}")
        
        return {
            'overall_status': 'unhealthy',
            'connection_quality': 'poor',
            'total_check_time_ms': round(total_time, 2),
            'average_response_time_ms': None,
            'endpoints': {},
            'error': str(e),
            'timestamp': time.time(),
            'sisense_url': Config.get_sisense_base_url()
        }

def test_api_endpoints() -> Dict[str, any]:
    """
    Test various API endpoints to verify functionality.
    
    Returns:
        Dict containing test results for each endpoint category
    """
    try:
        http_client = get_http_client()
        headers = get_auth_headers()
        
        # Test only confirmed working endpoints
        endpoints_to_test = {
            'authentication': '/api/v1/dashboards',  # Using dashboards for auth validation
            'dashboards': '/api/v1/dashboards',
            'connections': '/api/v2/connections'
        }
        
        test_results = {}
        
        for service_name, endpoint in endpoints_to_test.items():
            try:
                response = http_client.get(endpoint, headers=headers)
                test_results[service_name] = {
                    'tested': True,
                    'working': True,
                    'error': None,
                    'endpoint': endpoint
                }
                if service_name == 'authentication':
                    test_results[service_name]['note'] = 'Using dashboards endpoint for auth validation'
            except Exception as e:
                test_results[service_name] = {
                    'tested': True,
                    'working': False,
                    'error': str(e),
                    'endpoint': endpoint
                }
        
        # Add note about unavailable services
        test_results['datamodels'] = {
            'tested': False,
            'working': False,
            'error': 'Data models endpoints not available in this Sisense environment',
            'endpoint': 'N/A (all data model endpoints return 404)'
        }
        
        # Calculate overall success rate
        working_count = sum(1 for result in test_results.values() if result['working'])
        total_count = len(test_results)
        success_rate = (working_count / total_count) * 100
        
        return {
            'test_results': test_results,
            'success_rate': round(success_rate, 2),
            'working_endpoints': working_count,
            'total_endpoints': total_count,
            'timestamp': time.time()
        }
        
    except Exception as e:
        logger.error(f"API endpoint testing failed: {e}")
        return {
            'test_results': {},
            'success_rate': 0,
            'working_endpoints': 0,
            'total_endpoints': 0,
            'error': str(e),
            'timestamp': time.time()
        }

def get_enhanced_auth_status() -> Dict[str, any]:
    """
    Get comprehensive authentication status including caching info.
    
    Returns:
        Dict containing detailed authentication status
    """
    is_valid, message = validate_authentication()
    user_info = get_user_info()
    
    # Check cache status
    token_hash = hash(Config.SISENSE_API_TOKEN) if Config.SISENSE_API_TOKEN else None
    cache_info = None
    
    if token_hash and token_hash in _token_validation_cache:
        cached_valid, cached_timestamp = _token_validation_cache[token_hash]
        cache_age = time.time() - cached_timestamp
        cache_info = {
            'cached': True,
            'cache_age_seconds': round(cache_age, 2),
            'cache_expires_in_seconds': round(_cache_duration - cache_age, 2),
            'cached_result': cached_valid
        }
    else:
        cache_info = {'cached': False}
    
    return {
        'is_valid': is_valid,
        'message': message,
        'user_info': user_info,
        'cache_info': cache_info,
        'token_configured': bool(Config.SISENSE_API_TOKEN),
        'sisense_url': Config.get_sisense_base_url(),
        'timestamp': time.time()
    }