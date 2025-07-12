"""
Dashboards module for Sisense API v1.

Provides functions to interact with Sisense dashboards including
listing dashboards, getting dashboard details, and managing widgets.
"""

import logging
from typing import Dict, List, Optional, Any

from config import Config
from sisense.auth import get_auth_headers
from sisense.utils import get_http_client, SisenseAPIError, validate_response_data
from sisense.env_config import get_environment_config


logger = logging.getLogger(__name__)


def _get_dashboard_endpoint(endpoint_suffix: str = "") -> str:
    """Get environment-aware dashboard endpoint."""
    env_config = get_environment_config()
    return env_config.get_endpoint_url('dashboards', endpoint_suffix)


def list_dashboards(
    owner: Optional[str] = None,
    shared: Optional[bool] = None,
    fields: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    List all dashboards with optional filtering.
    
    Args:
        owner: Optional owner filter (user ID).
        shared: Optional filter for shared dashboards.
        fields: Optional list of fields to include in response.
    """
    # Demo mode - return sample dashboards
    if Config.DEMO_MODE:
        return [
            {
                "oid": "demo-dashboard-1",
                "title": "Sales Performance Dashboard",
                "desc": "Demo dashboard showing sales metrics",
                "owner": "demo-user-123",
                "created": "2024-01-01T00:00:00Z",
                "lastOpened": "2024-01-20T10:00:00Z"
            },
            {
                "oid": "demo-dashboard-2",
                "title": "Marketing Analytics",
                "desc": "Demo marketing performance dashboard", 
                "owner": "demo-user-123",
                "created": "2024-01-05T00:00:00Z",
                "lastOpened": "2024-01-19T15:30:00Z"
            }
        ]
    http_client = get_http_client()
    headers = get_auth_headers()
    
    params = {}
    if owner:
        params['owner'] = owner
    if shared is not None:
        params['shared'] = 'true' if shared else 'false'
    if fields:
        params['fields'] = ','.join(fields)
    
    logger.info(f"Listing dashboards with owner: {owner}, shared: {shared}")
    
    try:
        endpoint = _get_dashboard_endpoint()
        response = http_client.get(
            endpoint=endpoint,
            headers=headers,
            params=params
        )
        
        # Validate response structure
        if isinstance(response, list):
            dashboards = response
        elif isinstance(response, dict) and 'data' in response:
            dashboards = response['data']
        else:
            dashboards = [response] if response else []
        
        logger.info(f"Retrieved {len(dashboards)} dashboards")
        return dashboards
        
    except Exception as e:
        logger.error(f"Failed to list dashboards: {str(e)}")
        raise SisenseAPIError(f"Failed to list dashboards: {str(e)}")


def get_dashboard(dashboard_id: str, fields: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Get specific dashboard details by ID.
    
    Args:
        dashboard_id: Dashboard ID.
        fields: Optional list of fields to include in response.
        
    Returns:
        Dict: Dashboard definition and metadata.
        
    Raises:
        SisenseAPIError: If request fails.
    """
    http_client = get_http_client()
    headers = get_auth_headers()
    
    params = {}
    if fields:
        params['fields'] = ','.join(fields)
    
    logger.info(f"Getting dashboard: {dashboard_id}")
    
    try:
        endpoint = _get_dashboard_endpoint(dashboard_id)
        response = http_client.get(
            endpoint=endpoint,
            headers=headers,
            params=params
        )
        
        # Validate required fields
        required_fields = ['oid', 'title']
        validate_response_data(response, required_fields)
        
        logger.info(f"Retrieved dashboard: {response.get('title', 'Unknown')}")
        return response
        
    except Exception as e:
        logger.error(f"Failed to get dashboard {dashboard_id}: {str(e)}")
        raise SisenseAPIError(f"Failed to get dashboard {dashboard_id}: {str(e)}")


def get_dashboard_widgets(dashboard_id: str) -> List[Dict[str, Any]]:
    """
    Get all widgets for a specific dashboard.
    
    Args:
        dashboard_id: Dashboard ID.
        
    Returns:
        List[Dict]: List of widget definitions.
        
    Raises:
        SisenseAPIError: If request fails.
    """
    http_client = get_http_client()
    headers = get_auth_headers()
    
    logger.info(f"Getting widgets for dashboard: {dashboard_id}")
    
    try:
        response = http_client.get(
            endpoint=f'/api/v1/dashboards/{dashboard_id}/widgets',
            headers=headers
        )
        
        # Validate response structure
        if isinstance(response, list):
            widgets = response
        elif isinstance(response, dict) and 'data' in response:
            widgets = response['data']
        else:
            widgets = [response] if response else []
        
        logger.info(f"Retrieved {len(widgets)} widgets for dashboard {dashboard_id}")
        return widgets
        
    except Exception as e:
        logger.error(f"Failed to get widgets for dashboard {dashboard_id}: {str(e)}")
        raise SisenseAPIError(f"Failed to get widgets for dashboard {dashboard_id}: {str(e)}")


def get_dashboard_filters(dashboard_id: str) -> List[Dict[str, Any]]:
    """
    Get filters for a specific dashboard.
    
    Args:
        dashboard_id: Dashboard ID.
        
    Returns:
        List[Dict]: List of dashboard filters.
        
    Raises:
        SisenseAPIError: If request fails.
    """
    logger.info(f"Getting filters for dashboard: {dashboard_id}")
    
    try:
        dashboard = get_dashboard(dashboard_id)
        
        # Extract filters from dashboard data
        filters = dashboard.get('filters', [])
        if not isinstance(filters, list):
            filters = []
        
        logger.info(f"Retrieved {len(filters)} filters for dashboard {dashboard_id}")
        return filters
        
    except Exception as e:
        logger.error(f"Failed to get filters for dashboard {dashboard_id}: {str(e)}")
        raise SisenseAPIError(f"Failed to get filters for dashboard {dashboard_id}: {str(e)}")


def get_dashboard_sharing(dashboard_id: str) -> Dict[str, Any]:
    """
    Get sharing settings for a specific dashboard.
    
    Args:
        dashboard_id: Dashboard ID.
        
    Returns:
        Dict: Dashboard sharing configuration.
        
    Raises:
        SisenseAPIError: If request fails.
    """
    http_client = get_http_client()
    headers = get_auth_headers()
    
    logger.info(f"Getting sharing settings for dashboard: {dashboard_id}")
    
    try:
        response = http_client.get(
            endpoint=f'/api/v1/dashboards/{dashboard_id}/sharing',
            headers=headers
        )
        
        logger.info(f"Retrieved sharing settings for dashboard {dashboard_id}")
        return response
        
    except Exception as e:
        logger.error(f"Failed to get sharing settings for dashboard {dashboard_id}: {str(e)}")
        raise SisenseAPIError(f"Failed to get sharing settings for dashboard {dashboard_id}: {str(e)}")


def search_dashboards(search_term: str) -> List[Dict[str, Any]]:
    """
    Search dashboards by title or description.
    
    Args:
        search_term: Search term to filter dashboards.
        
    Returns:
        List[Dict]: Matching dashboards.
        
    Raises:
        SisenseAPIError: If request fails.
    """
    logger.info(f"Searching dashboards with term: {search_term}")
    
    try:
        all_dashboards = list_dashboards()
        
        # Filter dashboards by search term
        search_term_lower = search_term.lower()
        matching_dashboards = []
        
        for dashboard in all_dashboards:
            dashboard_title = dashboard.get('title', '').lower()
            dashboard_description = dashboard.get('description', '').lower()
            
            if (search_term_lower in dashboard_title or 
                search_term_lower in dashboard_description):
                matching_dashboards.append(dashboard)
        
        logger.info(f"Found {len(matching_dashboards)} matching dashboards")
        return matching_dashboards
        
    except Exception as e:
        logger.error(f"Failed to search dashboards: {str(e)}")
        raise SisenseAPIError(f"Failed to search dashboards: {str(e)}")


def get_dashboard_export_url(dashboard_id: str, export_type: str = 'png') -> str:
    """
    Get export URL for a dashboard.
    
    Args:
        dashboard_id: Dashboard ID.
        export_type: Export format (png, pdf, etc.).
        
    Returns:
        str: Export URL.
        
    Raises:
        SisenseAPIError: If request fails.
    """
    http_client = get_http_client()
    base_url = http_client.base_url
    
    logger.info(f"Getting export URL for dashboard: {dashboard_id}, type: {export_type}")
    
    try:
        # Construct export URL
        export_url = f"{base_url}/api/v1/dashboards/{dashboard_id}/export/{export_type}"
        
        logger.info(f"Generated export URL for dashboard {dashboard_id}")
        return export_url
        
    except Exception as e:
        logger.error(f"Failed to get export URL for dashboard {dashboard_id}: {str(e)}")
        raise SisenseAPIError(f"Failed to get export URL for dashboard {dashboard_id}: {str(e)}")


def get_dashboard_summary(dashboard_id: str) -> Dict[str, Any]:
    """
    Get summary information for a dashboard.
    
    Args:
        dashboard_id: Dashboard ID.
        
    Returns:
        Dict: Dashboard summary including widget count, filters, etc.
        
    Raises:
        SisenseAPIError: If request fails.
    """
    logger.info(f"Getting summary for dashboard: {dashboard_id}")
    
    try:
        # Get dashboard details
        dashboard = get_dashboard(dashboard_id)
        
        # Get widgets
        widgets = get_dashboard_widgets(dashboard_id)
        
        # Get filters
        filters = get_dashboard_filters(dashboard_id)
        
        # Create summary
        summary = {
            'id': dashboard.get('oid'),
            'title': dashboard.get('title'),
            'description': dashboard.get('description', ''),
            'owner': dashboard.get('owner'),
            'created': dashboard.get('created'),
            'lastModified': dashboard.get('lastModified'),
            'widget_count': len(widgets),
            'filter_count': len(filters),
            'data_sources': [],
            'widget_types': []
        }
        
        # Extract data sources and widget types
        data_sources = set()
        widget_types = set()
        
        for widget in widgets:
            if 'datasource' in widget:
                ds_title = widget['datasource'].get('title', '')
                if ds_title:
                    data_sources.add(ds_title)
            
            widget_type = widget.get('type', 'unknown')
            widget_types.add(widget_type)
        
        summary['data_sources'] = list(data_sources)
        summary['widget_types'] = list(widget_types)
        
        logger.info(f"Generated summary for dashboard {dashboard_id}")
        return summary
        
    except Exception as e:
        logger.error(f"Failed to get summary for dashboard {dashboard_id}: {str(e)}")
        raise SisenseAPIError(f"Failed to get summary for dashboard {dashboard_id}: {str(e)}")