"""
Widgets module for Sisense API v1.

Provides functions to interact with Sisense widgets including
getting widget details, JAQL queries, and styling information.
"""

import logging
from typing import Dict, List, Optional, Any

from sisense.config import Config
from sisense.auth import get_auth_headers
from sisense.utils import get_http_client, SisenseAPIError, validate_response_data


logger = logging.getLogger(__name__)


def get_dashboard_widgets(dashboard_id: str) -> List[Dict[str, Any]]:
    """
    Get all widgets for a specific dashboard through the dashboard hierarchy.
    
    Args:
        dashboard_id: Dashboard ID (OID).
        
    Returns:
        List[Dict]: List of widgets in the dashboard.
        
    Raises:
        SisenseAPIError: If request fails.
    """
    # Import here to avoid circular imports
    from sisense.dashboards import get_dashboard
    
    try:
        # Get full dashboard details which includes widgets
        dashboard_data = get_dashboard(dashboard_id)
        
        # Extract widgets from dashboard data
        widgets = dashboard_data.get('widgets', [])
        
        if not isinstance(widgets, list):
            widgets = []
        
        logger.debug(f"Retrieved {len(widgets)} widgets for dashboard {dashboard_id}")
        return widgets
        
    except Exception as e:
        logger.error(f"Failed to get widgets for dashboard {dashboard_id}: {str(e)}")
        raise SisenseAPIError(f"Failed to get widgets for dashboard {dashboard_id}: {str(e)}")


def list_widgets() -> List[Dict[str, Any]]:
    """
    List all widgets across all accessible dashboards.
    
    Returns:
        List[Dict]: List of all widgets with dashboard context.
    """
    if Config.DEMO_MODE:
        return [
            {
                "oid": "demo-widget-1",
                "title": "Demo Chart Widget",
                "type": "chart",
                "dashboard_id": "demo-dashboard-1"
            },
            {
                "oid": "demo-widget-2", 
                "title": "Demo Table Widget",
                "type": "table",
                "dashboard_id": "demo-dashboard-2"
            }
        ]
    
    from sisense.dashboards import list_dashboards
    
    all_widgets = []
    logger.info("Collecting widgets from all dashboards")
    
    try:
        dashboards = list_dashboards()
        
        for dashboard in dashboards:
            dashboard_id = dashboard.get('oid')
            if not dashboard_id:
                continue
                
            try:
                widgets = get_dashboard_widgets(dashboard_id)
                
                # Add dashboard context to each widget
                for widget in widgets:
                    widget['dashboard_id'] = dashboard_id
                    widget['dashboard_title'] = dashboard.get('title', 'Unknown')
                    all_widgets.append(widget)
                    
            except Exception as e:
                logger.debug(f"Failed to get widgets for dashboard {dashboard_id}: {e}")
                continue
        
        logger.info(f"Retrieved {len(all_widgets)} total widgets")
        return all_widgets
        
    except Exception as e:
        logger.error(f"Failed to list widgets: {str(e)}")
        raise SisenseAPIError(f"Failed to list widgets: {str(e)}")


def get_widget(widget_id: str, fields: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Get specific widget details by ID.
    
    Args:
        widget_id: Widget ID.
        fields: Optional list of fields to include in response.
        
    Returns:
        Dict: Widget structure including JAQL and style information.
        
    Raises:
        SisenseAPIError: If request fails or widget not found.
    """
    # Demo mode - return sample widget
    if Config.DEMO_MODE:
        return {
            "oid": widget_id,
            "title": f"Demo Widget {widget_id}",
            "type": "chart",
            "subtype": "column",
            "desc": "Demo widget for testing",
            "metadata": {
                "jaql": {"datasource": "demo"}
            },
            "style": {},
            "created": "2024-01-01T00:00:00Z"
        }
    
    # Since standalone widget endpoints don't work, we need to find the widget 
    # through its parent dashboard
    from sisense.dashboards import list_dashboards
    
    logger.info(f"Searching for widget {widget_id} across all dashboards")
    
    try:
        dashboards = list_dashboards()
        
        for dashboard in dashboards:
            dashboard_id = dashboard.get('oid')
            if not dashboard_id:
                continue
                
            try:
                # Try to get widgets for this dashboard
                widgets = get_dashboard_widgets(dashboard_id)
                
                # Look for our widget in this dashboard
                for widget in widgets:
                    if widget.get('oid') == widget_id or widget.get('_id') == widget_id:
                        logger.info(f"Found widget {widget_id} in dashboard {dashboard_id}")
                        return widget
                        
            except Exception as e:
                logger.debug(f"Failed to get widgets for dashboard {dashboard_id}: {e}")
                continue
        
        # Widget not found in any dashboard
        raise SisenseAPIError(f"Widget {widget_id} not found in any accessible dashboard")
        
    except Exception as e:
        logger.error(f"Failed to find widget {widget_id}: {str(e)}")
        raise SisenseAPIError(f"Failed to find widget {widget_id}: {str(e)}")


def get_widget_jaql(widget_id: str) -> Dict[str, Any]:
    """
    Get JAQL query for a specific widget.
    
    Args:
        widget_id: Widget ID.
        
    Returns:
        Dict: Widget JAQL query structure.
        
    Raises:
        SisenseAPIError: If request fails.
    """
    logger.info(f"Getting JAQL for widget: {widget_id}")
    
    try:
        widget = get_widget(widget_id)
        
        # Extract JAQL from widget data
        jaql = widget.get('metadata', {}).get('jaql', {})
        if not jaql:
            jaql = widget.get('jaql', {})
        
        if not jaql:
            logger.warning(f"No JAQL found for widget {widget_id}")
            jaql = {}
        
        logger.info(f"Retrieved JAQL for widget {widget_id}")
        return jaql
        
    except Exception as e:
        logger.error(f"Failed to get JAQL for widget {widget_id}: {str(e)}")
        raise SisenseAPIError(f"Failed to get JAQL for widget {widget_id}: {str(e)}")


def get_widget_style(widget_id: str) -> Dict[str, Any]:
    """
    Get style configuration for a specific widget.
    
    Args:
        widget_id: Widget ID.
        
    Returns:
        Dict: Widget style configuration.
        
    Raises:
        SisenseAPIError: If request fails.
    """
    logger.info(f"Getting style for widget: {widget_id}")
    
    try:
        widget = get_widget(widget_id)
        
        # Extract style from widget data
        style = widget.get('style', {})
        if not style:
            style = widget.get('metadata', {}).get('style', {})
        
        logger.info(f"Retrieved style for widget {widget_id}")
        return style
        
    except Exception as e:
        logger.error(f"Failed to get style for widget {widget_id}: {str(e)}")
        raise SisenseAPIError(f"Failed to get style for widget {widget_id}: {str(e)}")


def get_widget_data(widget_id: str, filters: Optional[List[Dict]] = None) -> Dict[str, Any]:
    """
    Get data for a specific widget by extracting JAQL and executing via unified query endpoint.
    
    Args:
        widget_id: Widget ID.
        filters: Optional list of filters to apply.
        
    Returns:
        Dict: Widget data results.
        
    Raises:
        SisenseAPIError: If request fails or widget JAQL cannot be executed.
    """
    # Demo mode - return sample data
    if Config.DEMO_MODE:
        return {
            "headers": ["Category", "Sales", "Profit"],
            "values": [
                ["Product A", 1000, 200],
                ["Product B", 1500, 300],
                ["Product C", 800, 150]
            ],
            "metadata": {
                "widget_id": widget_id,
                "filters_applied": len(filters) if filters else 0
            }
        }
    
    logger.info(f"Getting data for widget {widget_id} via JAQL execution")
    
    try:
        # Get widget details and extract JAQL
        widget = get_widget(widget_id)
        jaql_query = get_widget_jaql(widget_id)
        
        if not jaql_query:
            raise SisenseAPIError(f"No JAQL query found for widget {widget_id}")
        
        # Apply additional filters if provided
        if filters:
            if 'metadata' not in jaql_query:
                jaql_query['metadata'] = []
            
            for filter_item in filters:
                jaql_query['metadata'].append({
                    'jaql': filter_item,
                    'panel': 'filters'
                })
        
        # Execute JAQL query via unified endpoint
        from sisense.jaql import execute_jaql
        
        # Get datasource from widget or JAQL
        datasource = widget.get('datasource', {}).get('title') or jaql_query.get('datasource', '')
        if not datasource:
            raise SisenseAPIError(f"No datasource found for widget {widget_id}")
        
        result = execute_jaql(datasource, jaql_query)
        
        logger.info(f"Successfully retrieved data for widget {widget_id}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to get data for widget {widget_id}: {str(e)}")
        raise SisenseAPIError(f"Failed to get widget data: {str(e)}")


def get_widget_metadata(widget_id: str) -> Dict[str, Any]:
    """
    Get metadata for a specific widget.
    
    Args:
        widget_id: Widget ID.
        
    Returns:
        Dict: Widget metadata including dimensions, measures, and filters.
        
    Raises:
        SisenseAPIError: If request fails.
    """
    logger.info(f"Getting metadata for widget: {widget_id}")
    
    try:
        widget = get_widget(widget_id)
        
        # Extract metadata
        metadata = widget.get('metadata', {})
        
        # Parse JAQL to extract dimensions and measures
        jaql = metadata.get('jaql', {})
        
        dimensions = []
        measures = []
        filters = []
        
        if 'metadata' in jaql:
            for item in jaql['metadata']:
                if item.get('panel') == 'columns':
                    dimensions.append(item)
                elif item.get('panel') == 'values':
                    measures.append(item)
                elif item.get('panel') == 'filters':
                    filters.append(item)
        
        enhanced_metadata = {
            'widget_id': widget_id,
            'title': widget.get('title'),
            'type': widget.get('type'),
            'datasource': widget.get('datasource', {}),
            'dimensions': dimensions,
            'measures': measures,
            'filters': filters,
            'raw_metadata': metadata
        }
        
        logger.info(f"Retrieved metadata for widget {widget_id}")
        return enhanced_metadata
        
    except Exception as e:
        logger.error(f"Failed to get metadata for widget {widget_id}: {str(e)}")
        raise SisenseAPIError(f"Failed to get metadata for widget {widget_id}: {str(e)}")


def get_widget_export_url(widget_id: str, export_type: str = 'png') -> str:
    """
    Get export URL for a widget.
    
    Args:
        widget_id: Widget ID.
        export_type: Export format (png, pdf, etc.).
        
    Returns:
        str: Export URL.
        
    Raises:
        SisenseAPIError: If request fails.
    """
    http_client = get_http_client()
    base_url = http_client.base_url
    
    logger.info(f"Getting export URL for widget: {widget_id}, type: {export_type}")
    
    try:
        # Construct export URL
        export_url = f"{base_url}/api/v1/widgets/{widget_id}/export/{export_type}"
        
        logger.info(f"Generated export URL for widget {widget_id}")
        return export_url
        
    except Exception as e:
        logger.error(f"Failed to get export URL for widget {widget_id}: {str(e)}")
        raise SisenseAPIError(f"Failed to get export URL for widget {widget_id}: {str(e)}")


def get_widget_summary(widget_id: str) -> Dict[str, Any]:
    """
    Get summary information for a widget.
    
    Args:
        widget_id: Widget ID.
        
    Returns:
        Dict: Widget summary including type, dimensions, measures, etc.
        
    Raises:
        SisenseAPIError: If request fails.
    """
    logger.info(f"Getting summary for widget: {widget_id}")
    
    try:
        # Get widget details
        widget = get_widget(widget_id)
        
        # Get metadata
        metadata = get_widget_metadata(widget_id)
        
        # Create summary
        summary = {
            'id': widget.get('oid'),
            'title': widget.get('title'),
            'description': widget.get('description', ''),
            'type': widget.get('type'),
            'subtype': widget.get('subtype'),
            'datasource': widget.get('datasource', {}).get('title', ''),
            'owner': widget.get('owner'),
            'created': widget.get('created'),
            'lastModified': widget.get('lastModified'),
            'dimension_count': len(metadata.get('dimensions', [])),
            'measure_count': len(metadata.get('measures', [])),
            'filter_count': len(metadata.get('filters', [])),
            'dimensions': [d.get('dim', {}).get('title', '') for d in metadata.get('dimensions', [])],
            'measures': [m.get('title', '') for m in metadata.get('measures', [])],
            'chart_type': widget.get('type', 'unknown')
        }
        
        logger.info(f"Generated summary for widget {widget_id}")
        return summary
        
    except Exception as e:
        logger.error(f"Failed to get summary for widget {widget_id}: {str(e)}")
        raise SisenseAPIError(f"Failed to get summary for widget {widget_id}: {str(e)}")


def search_widgets_by_type(widget_type: str, dashboard_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Search widgets by type, optionally within a specific dashboard.
    
    Args:
        widget_type: Widget type to search for.
        dashboard_id: Optional dashboard ID to limit search.
        
    Returns:
        List[Dict]: Matching widgets.
        
    Raises:
        SisenseAPIError: If request fails.
    """
    logger.info(f"Searching widgets by type: {widget_type}, dashboard: {dashboard_id}")
    
    try:
        if dashboard_id:
            # Import here to avoid circular imports
            from sisense.dashboards import get_dashboard_widgets
            widgets = get_dashboard_widgets(dashboard_id)
        else:
            # Search all dashboards - this would require getting all dashboards first
            # For now, require dashboard_id
            raise SisenseAPIError("Dashboard ID is required for widget search")
        
        # Filter widgets by type
        matching_widgets = []
        for widget in widgets:
            if widget.get('type', '').lower() == widget_type.lower():
                matching_widgets.append(widget)
        
        logger.info(f"Found {len(matching_widgets)} widgets of type {widget_type}")
        return matching_widgets
        
    except Exception as e:
        logger.error(f"Failed to search widgets by type {widget_type}: {str(e)}")
        raise SisenseAPIError(f"Failed to search widgets by type {widget_type}: {str(e)}")


def get_widget_dimensions(widget_id: str) -> List[Dict[str, Any]]:
    """
    Get dimensions used in a specific widget.
    
    Args:
        widget_id: Widget ID.
        
    Returns:
        List[Dict]: Widget dimensions.
        
    Raises:
        SisenseAPIError: If request fails.
    """
    logger.info(f"Getting dimensions for widget: {widget_id}")
    
    try:
        metadata = get_widget_metadata(widget_id)
        dimensions = metadata.get('dimensions', [])
        
        logger.info(f"Retrieved {len(dimensions)} dimensions for widget {widget_id}")
        return dimensions
        
    except Exception as e:
        logger.error(f"Failed to get dimensions for widget {widget_id}: {str(e)}")
        raise SisenseAPIError(f"Failed to get dimensions for widget {widget_id}: {str(e)}")


def get_widget_measures(widget_id: str) -> List[Dict[str, Any]]:
    """
    Get measures used in a specific widget.
    
    Args:
        widget_id: Widget ID.
        
    Returns:
        List[Dict]: Widget measures.
        
    Raises:
        SisenseAPIError: If request fails.
    """
    logger.info(f"Getting measures for widget: {widget_id}")
    
    try:
        metadata = get_widget_metadata(widget_id)
        measures = metadata.get('measures', [])
        
        logger.info(f"Retrieved {len(measures)} measures for widget {widget_id}")
        return measures
        
    except Exception as e:
        logger.error(f"Failed to get measures for widget {widget_id}: {str(e)}")
        raise SisenseAPIError(f"Failed to get measures for widget {widget_id}: {str(e)}")