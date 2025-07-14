"""
Smart API Version Detection System for Sisense REST API.

This module provides capability detection for different Sisense API versions
and patterns to enable smart routing and fallback mechanisms.
"""

import requests
import logging
from typing import Dict, Optional, Tuple
from sisense.config import Config


class SisenseAPIVersionDetector:
    """
    Detects available API capabilities for a Sisense instance.
    
    This class tests various API endpoints to determine which versions
    and patterns are supported by the target Sisense environment.
    """
    
    def __init__(self, base_url: str, token: str):
        """
        Initialize the API version detector.
        
        Args:
            base_url: Base URL of the Sisense instance
            token: API authentication token
        """
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.capabilities = None
        self.logger = logging.getLogger(__name__)
        
    def detect_capabilities(self) -> Dict[str, any]:
        """
        Detect actual API capabilities of the Sisense instance.
        
        Returns:
            Dict containing detected capabilities and patterns
        """
        if self.capabilities:
            return self.capabilities
            
        self.logger.info("Starting API capability detection")
        
        capabilities = {
            'v0_available': False,
            'v1_available': False,
            'v2_available': False,
            'v2_datamodels': False,
            'v2_connections': False,
            'auth_pattern': None,
            'data_model_pattern': None,
            'query_pattern': None,
            'widget_pattern': None
        }
        
        # Test authentication patterns
        auth_tests = [
            ('/api/v1/auth/isauth', 'v1_auth'),
            ('/auth/isauth', 'v0_auth'),
            ('/api/v2/auth/isauth', 'v2_auth')
        ]
        
        for endpoint, pattern in auth_tests:
            if self._test_endpoint(endpoint):
                capabilities['auth_pattern'] = pattern
                self.logger.info(f"Authentication pattern detected: {pattern}")
                break
        
        # Test data model patterns
        datamodel_tests = [
            ('/api/v2/datamodels', 'v2_datamodels'),
            ('/api/v1/elasticubes/getElasticubes', 'v1_elasticubes'),
            ('/elasticubes/getElasticubes', 'v0_elasticubes')
        ]
        
        for endpoint, pattern in datamodel_tests:
            if self._test_endpoint(endpoint):
                capabilities['data_model_pattern'] = pattern
                self.logger.info(f"Data model pattern detected: {pattern}")
                break
        
        # Test query patterns
        query_tests = [
            ('/api/v1/query', 'v1_unified_query')
        ]
        
        for endpoint, pattern in query_tests:
            if self._test_endpoint(endpoint, method='POST'):
                capabilities['query_pattern'] = pattern
                self.logger.info(f"Query pattern detected: {pattern}")
                break
        
        # Test specific v2 capabilities
        capabilities['v2_connections'] = self._test_endpoint('/api/v2/connections')
        capabilities['v2_datamodels'] = self._test_endpoint('/api/v2/datamodels')
        
        # Test dashboard availability (should always work)
        capabilities['dashboards_available'] = self._test_endpoint('/api/v1/dashboards')
        
        # Set widget pattern based on dashboard availability
        if capabilities['dashboards_available']:
            capabilities['widget_pattern'] = 'dashboard_hierarchy'
            
        # Determine overall API version availability
        capabilities['v0_available'] = any([
            capabilities['auth_pattern'] == 'v0_auth',
            capabilities['data_model_pattern'] == 'v0_elasticubes'
        ])
        
        capabilities['v1_available'] = any([
            capabilities['auth_pattern'] == 'v1_auth',
            capabilities['data_model_pattern'] == 'v1_elasticubes',
            capabilities['query_pattern'] == 'v1_unified_query',
            capabilities['dashboards_available']
        ])
        
        capabilities['v2_available'] = any([
            capabilities['auth_pattern'] == 'v2_auth',
            capabilities['v2_connections'],
            capabilities['v2_datamodels']
        ])
        
        self.capabilities = capabilities
        self.logger.info(f"API capability detection completed: {capabilities}")
        return capabilities
    
    def _test_endpoint(self, endpoint: str, method: str = 'GET') -> bool:
        """
        Test if an endpoint is available.
        
        Args:
            endpoint: API endpoint to test
            method: HTTP method to use (GET or POST)
            
        Returns:
            True if endpoint is available, False otherwise
        """
        try:
            headers = self._get_auth_headers()
            url = f"{self.base_url}{endpoint}"
            
            if method.upper() == 'GET':
                response = requests.get(
                    url,
                    headers=headers,
                    timeout=Config.REQUEST_TIMEOUT,
                    verify=Config.SSL_VERIFY
                )
            elif method.upper() == 'POST':
                # For POST endpoints, send minimal test payload
                response = requests.post(
                    url,
                    headers=headers,
                    json={},
                    timeout=Config.REQUEST_TIMEOUT,
                    verify=Config.SSL_VERIFY
                )
            else:
                return False
                
            # Endpoint is available if we get 200, 401, 403, or 422
            # (not 404 which means endpoint doesn't exist)
            available = response.status_code in [200, 401, 403, 422]
            
            self.logger.debug(f"Endpoint {endpoint} test: {response.status_code} -> {'available' if available else 'not available'}")
            return available
            
        except requests.exceptions.RequestException as e:
            self.logger.debug(f"Endpoint {endpoint} test failed: {e}")
            return False
        except Exception as e:
            self.logger.debug(f"Unexpected error testing {endpoint}: {e}")
            return False
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for API requests.
        
        Returns:
            Dictionary containing authentication headers
        """
        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def get_capability_summary(self) -> str:
        """
        Get a human-readable summary of detected capabilities.
        
        Returns:
            String summary of API capabilities
        """
        if not self.capabilities:
            self.detect_capabilities()
            
        summary_lines = []
        caps = self.capabilities
        
        summary_lines.append("Sisense API Capability Detection Summary:")
        summary_lines.append("=" * 45)
        
        # API Version Availability
        summary_lines.append(f"v0 API Available: {'Yes' if caps['v0_available'] else 'No'}")
        summary_lines.append(f"v1 API Available: {'Yes' if caps['v1_available'] else 'No'}")
        summary_lines.append(f"v2 API Available: {'Yes' if caps['v2_available'] else 'No'}")
        summary_lines.append("")
        
        # Specific Patterns
        summary_lines.append("Detected Patterns:")
        summary_lines.append(f"  Authentication: {caps['auth_pattern'] or 'Not detected'}")
        summary_lines.append(f"  Data Models: {caps['data_model_pattern'] or 'Not detected'}")
        summary_lines.append(f"  Queries: {caps['query_pattern'] or 'Not detected'}")
        summary_lines.append(f"  Widgets: {caps['widget_pattern'] or 'Not detected'}")
        summary_lines.append("")
        
        # Specific Features
        summary_lines.append("Feature Availability:")
        summary_lines.append(f"  v2 Connections: {'Yes' if caps['v2_connections'] else 'No'}")
        summary_lines.append(f"  v2 DataModels: {'Yes' if caps['v2_datamodels'] else 'No'}")
        summary_lines.append(f"  Dashboards: {'Yes' if caps['dashboards_available'] else 'No'}")
        
        return "\n".join(summary_lines)