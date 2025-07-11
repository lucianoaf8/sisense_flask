"""
Widgets module for Sisense API v1.

Provides functions to interact with Sisense widgets including
getting widget details, JAQL queries, and styling information.
"""

import logging
from typing import Dict, List, Optional, Any

from sisense.auth import get_auth_headers
from sisense.utils import get_http_client, SisenseAPIError, validate_response_data


logger = logging.getLogger(__name__)


def get_widget(widget_id: str, fields: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Get specific widget details by ID.
    
    Args:
        widget_id: Widget ID.
        fields: Optional list of fields to include in response.
        
    Returns:
        Dict: Widget structure including JAQL and style information.
        
    Raises:
        SisenseAPIError: If request fails.
    """
    http_client = get_http_client()
    headers = get_auth_headers()
    
    params = {}
    if fields:
        params['fields'] = ','.join(fields)
    
    logger.info(f"Getting widget: {widget_id}")
    
    try:
        response = http_client.get(
            endpoint=f'/api/v1/widgets/{widget_id}',
            headers=headers,
            params=params
        )
        
        # Validate required fields
        required_fields = ['oid', 'title', 'type']
        validate_response_data(response, required_fields)
        
        logger.info(f"Retrieved widget: {response.get('title', 'Unknown')}")
        return response
        
    except Exception as e:
        logger.error(f"Failed to get widget {widget_id}: {str(e)}")
        raise SisenseAPIError(f"Failed to get widget {widget_id}: {str(e)}")


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
    Get data for a specific widget with optional filters.
    
    Args:
        widget_id: Widget ID.
        filters: Optional list of filters to apply.
        
    Returns:
        Dict: Widget data results.
        
    Raises:
        SisenseAPIError: If request fails.
    """
    http_client = get_http_client()
    headers = get_auth_headers()
    
    logger.info(f"Getting data for widget: {widget_id}")
    
    try:
        # Get widget JAQL
        jaql = get_widget_jaql(widget_id)
        
        # Apply filters if provided
        if filters:
            if 'filters' not in jaql:
                jaql['filters'] = []
            jaql['filters'].extend(filters)
        
        # Execute JAQL query
        response = http_client.post(
            endpoint=f'/api/v1/widgets/{widget_id}/data',
            headers=headers,
            json=jaql
        )
        
        logger.info(f"Retrieved data for widget {widget_id}")
        return response
        
    except Exception as e:
        logger.error(f"Failed to get data for widget {widget_id}: {str(e)}")
        raise SisenseAPIError(f"Failed to get data for widget {widget_id}: {str(e)}")


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