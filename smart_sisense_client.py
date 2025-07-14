"""
Unified Smart Sisense Client with automatic API version detection and routing.

This module provides a single client interface that automatically detects
available API capabilities and routes requests to the appropriate endpoints.
"""

import logging
import requests
from typing import Dict, List, Optional, Any, Union
from sisense.config import Config
from sisense_api_detector import SisenseAPIVersionDetector


class SisenseAPIError(Exception):
    """Custom exception for Sisense API related errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class SmartSisenseClient:
    """
    Smart Sisense client that automatically detects API capabilities
    and routes requests to the appropriate endpoints.
    """
    
    def __init__(self, base_url: str, token: str):
        """
        Initialize the smart Sisense client.
        
        Args:
            base_url: Base URL of the Sisense instance
            token: API authentication token
        """
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.logger = logging.getLogger(__name__)
        
        # Initialize API detector
        self.detector = SisenseAPIVersionDetector(base_url, token)
        self.capabilities = None
        
        # Initialize capabilities on first use
        self._ensure_capabilities()
    
    def _ensure_capabilities(self):
        """Ensure capabilities have been detected."""
        if not self.capabilities:
            self.capabilities = self.detector.detect_capabilities()
    
    def authenticate(self) -> bool:
        """
        Validate authentication using detected auth pattern.
        
        Returns:
            True if authentication is valid, False otherwise
            
        Raises:
            SisenseAPIError: If authentication cannot be validated
        """
        self._ensure_capabilities()
        auth_pattern = self.capabilities.get('auth_pattern')
        
        try:
            if auth_pattern == 'v1_auth':
                response = self._call_api('GET', '/api/v1/auth/isauth')
                return response.status_code == 200
            elif auth_pattern == 'v0_auth':
                response = self._call_api('GET', '/auth/isauth')
                return response.status_code == 200
            elif auth_pattern == 'v2_auth':
                response = self._call_api('GET', '/api/v2/auth/isauth')
                return response.status_code == 200
            else:
                # Fallback: validate using working dashboards endpoint
                response = self._call_api('GET', '/api/v1/dashboards')
                return response.status_code == 200
                
        except Exception as e:
            self.logger.error(f"Authentication validation failed: {e}")
            return False
    
    def list_data_models(self, model_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List data models using detected data model pattern.
        
        Args:
            model_type: Optional filter for model type
            
        Returns:
            List of data models
            
        Raises:
            SisenseAPIError: If data models cannot be retrieved
        """
        self._ensure_capabilities()
        pattern = self.capabilities.get('data_model_pattern')
        
        if pattern == 'v2_datamodels':
            response = self._call_api('GET', '/api/v2/datamodels')
            if response.status_code == 200:
                data = response.json().get('data', [])
                return self._filter_models(data, model_type)
        elif pattern == 'v1_elasticubes':
            response = self._call_api('GET', '/api/v1/elasticubes/getElasticubes')
            if response.status_code == 200:
                data = response.json()
                return self._filter_models(data, model_type)
        elif pattern == 'v0_elasticubes':
            response = self._call_api('GET', '/elasticubes/getElasticubes')
            if response.status_code == 200:
                data = response.json()
                return self._filter_models(data, model_type)
        else:
            raise SisenseAPIError("Data models functionality not available in this environment")
    
    def execute_query(self, query_type: str, query_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute query using available query patterns.
        
        Args:
            query_type: Type of query ('jaql' or 'sql')
            query_data: Query data/payload
            
        Returns:
            Query results
            
        Raises:
            SisenseAPIError: If query execution fails or is not supported
        """
        self._ensure_capabilities()
        
        if query_type.lower() == 'jaql':
            query_pattern = self.capabilities.get('query_pattern')
            
            if query_pattern == 'v1_unified_query':
                response = self._call_api('POST', '/api/v1/query', json=query_data)
                if response.status_code == 200:
                    return response.json()
                else:
                    raise SisenseAPIError(f"JAQL query failed: {response.status_code}", response.status_code)
            else:
                raise SisenseAPIError("JAQL query functionality not available in this environment")
                
        elif query_type.lower() == 'sql':
            raise SisenseAPIError(
                "Direct SQL execution not supported in this Sisense environment. "
                "Use JAQL queries instead or extract queries from existing widgets."
            )
        else:
            raise SisenseAPIError(f"Query type '{query_type}' not supported")
    
    def get_widget_info(self, widget_id: str) -> Dict[str, Any]:
        """
        Get widget information through dashboard hierarchy.
        
        Args:
            widget_id: ID of the widget to retrieve
            
        Returns:
            Widget information
            
        Raises:
            SisenseAPIError: If widget cannot be found
        """
        self._ensure_capabilities()
        
        widget_pattern = self.capabilities.get('widget_pattern')
        
        if widget_pattern == 'dashboard_hierarchy':
            # Get all dashboards and search for the widget
            dashboards = self.list_dashboards()
            
            for dashboard in dashboards:
                dashboard_detail = self.get_dashboard(dashboard['oid'])
                
                for widget in dashboard_detail.get('widgets', []):
                    if widget.get('oid') == widget_id:
                        return widget
            
            raise SisenseAPIError(f"Widget {widget_id} not found")
        else:
            raise SisenseAPIError("Widget access not available in this environment")
    
    def list_dashboards(self) -> List[Dict[str, Any]]:
        """
        List available dashboards.
        
        Returns:
            List of dashboards
            
        Raises:
            SisenseAPIError: If dashboards cannot be retrieved
        """
        response = self._call_api('GET', '/api/v1/dashboards')
        if response.status_code == 200:
            return response.json()
        else:
            raise SisenseAPIError(f"Failed to list dashboards: {response.status_code}", response.status_code)
    
    def get_dashboard(self, dashboard_id: str) -> Dict[str, Any]:
        """
        Get detailed dashboard information.
        
        Args:
            dashboard_id: ID of the dashboard to retrieve
            
        Returns:
            Dashboard details including widgets
            
        Raises:
            SisenseAPIError: If dashboard cannot be retrieved
        """
        response = self._call_api('GET', f'/api/v1/dashboards/{dashboard_id}')
        if response.status_code == 200:
            return response.json()
        else:
            raise SisenseAPIError(f"Failed to get dashboard {dashboard_id}: {response.status_code}", response.status_code)
    
    def list_connections(self) -> List[Dict[str, Any]]:
        """
        List available connections (v2 only).
        
        Returns:
            List of connections
            
        Raises:
            SisenseAPIError: If connections cannot be retrieved or not supported
        """
        self._ensure_capabilities()
        
        if self.capabilities.get('v2_connections'):
            response = self._call_api('GET', '/api/v2/connections')
            if response.status_code == 200:
                return response.json().get('data', [])
            else:
                raise SisenseAPIError(f"Failed to list connections: {response.status_code}", response.status_code)
        else:
            raise SisenseAPIError("Connections functionality not available in this environment")
    
    def _call_api(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Make an API call to the Sisense instance.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            **kwargs: Additional arguments for requests
            
        Returns:
            Response object
            
        Raises:
            SisenseAPIError: If the API call fails
        """
        url = f"{self.base_url}{endpoint}"
        headers = self._get_auth_headers()
        
        # Merge provided headers with auth headers
        if 'headers' in kwargs:
            headers.update(kwargs.pop('headers'))
        
        try:
            response = requests.request(
                method,
                url,
                headers=headers,
                timeout=Config.REQUEST_TIMEOUT,
                verify=Config.SSL_VERIFY,
                **kwargs
            )
            
            self.logger.debug(f"{method} {endpoint} -> {response.status_code}")
            return response
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API call failed: {method} {endpoint} - {e}")
            raise SisenseAPIError(f"API call failed: {e}")
    
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
    
    def _filter_models(self, models: List[Dict], model_type: Optional[str]) -> List[Dict]:
        """
        Filter models by type if specified.
        
        Args:
            models: List of model dictionaries
            model_type: Optional model type filter
            
        Returns:
            Filtered list of models
        """
        if not model_type:
            return models
            
        # Filter based on model type
        filtered = []
        for model in models:
            # Check various possible type fields
            if (model.get('type') == model_type or 
                model.get('subtype') == model_type or
                model_type.lower() in model.get('title', '').lower()):
                filtered.append(model)
        
        return filtered
    
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get detected API capabilities.
        
        Returns:
            Dictionary of detected capabilities
        """
        self._ensure_capabilities()
        return self.capabilities.copy()
    
    def get_capability_summary(self) -> str:
        """
        Get human-readable capability summary.
        
        Returns:
            String summary of capabilities
        """
        return self.detector.get_capability_summary()