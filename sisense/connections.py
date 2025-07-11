"""
Connections module for Sisense API v2.

Provides functions to interact with Sisense data source connections
including listing connections and getting connection details.
"""

import logging
from typing import Dict, List, Optional, Any

from sisense.auth import get_auth_headers
from sisense.utils import get_http_client, SisenseAPIError, validate_response_data


logger = logging.getLogger(__name__)


def list_connections(
    connection_type: Optional[str] = None,
    include_credentials: bool = False
) -> List[Dict[str, Any]]:
    """
    List all data source connections.
    
    Args:
        connection_type: Optional connection type filter (e.g., 'mysql', 'postgresql').
        include_credentials: Whether to include connection credentials (admin only).
        
    Returns:
        List[Dict]: List of connection configurations.
        
    Raises:
        SisenseAPIError: If request fails.
    """
    http_client = get_http_client()
    headers = get_auth_headers()
    
    params = {}
    if connection_type:
        params['type'] = connection_type
    if include_credentials:
        params['includeCredentials'] = 'true'
    
    logger.info(f"Listing connections with type filter: {connection_type}")
    
    try:
        response = http_client.get(
            endpoint='/api/v2/connections',
            headers=headers,
            params=params
        )
        
        # Validate response structure
        if isinstance(response, list):
            connections = response
        elif isinstance(response, dict) and 'data' in response:
            connections = response['data']
        else:
            connections = [response] if response else []
        
        logger.info(f"Retrieved {len(connections)} connections")
        return connections
        
    except Exception as e:
        logger.error(f"Failed to list connections: {str(e)}")
        raise SisenseAPIError(f"Failed to list connections: {str(e)}")


def get_connection(connection_id: str, include_credentials: bool = False) -> Dict[str, Any]:
    """
    Get specific connection details by ID.
    
    Args:
        connection_id: Connection ID.
        include_credentials: Whether to include connection credentials (admin only).
        
    Returns:
        Dict: Connection configuration details.
        
    Raises:
        SisenseAPIError: If request fails.
    """
    http_client = get_http_client()
    headers = get_auth_headers()
    
    params = {}
    if include_credentials:
        params['includeCredentials'] = 'true'
    
    logger.info(f"Getting connection: {connection_id}")
    
    try:
        response = http_client.get(
            endpoint=f'/api/v2/connections/{connection_id}',
            headers=headers,
            params=params
        )
        
        # Validate required fields
        required_fields = ['id', 'type']
        validate_response_data(response, required_fields)
        
        logger.info(f"Retrieved connection: {response.get('id', 'Unknown')}")
        return response
        
    except Exception as e:
        logger.error(f"Failed to get connection {connection_id}: {str(e)}")
        raise SisenseAPIError(f"Failed to get connection {connection_id}: {str(e)}")


def get_connection_types() -> List[Dict[str, Any]]:
    """
    Get available connection types and their configurations.
    
    Returns:
        List[Dict]: Available connection types.
        
    Raises:
        SisenseAPIError: If request fails.
    """
    logger.info("Getting available connection types")
    
    try:
        # Get all connections and extract unique types
        all_connections = list_connections()
        
        connection_types = {}
        for connection in all_connections:
            conn_type = connection.get('type')
            if conn_type and conn_type not in connection_types:
                connection_types[conn_type] = {
                    'type': conn_type,
                    'name': connection.get('typeName', conn_type),
                    'description': connection.get('typeDescription', ''),
                    'examples': []
                }
            
            if conn_type:
                # Add connection as example (without credentials)
                example = {
                    'id': connection.get('id'),
                    'name': connection.get('name', ''),
                    'host': connection.get('host', ''),
                    'port': connection.get('port', ''),
                    'database': connection.get('database', '')
                }
                connection_types[conn_type]['examples'].append(example)
        
        types_list = list(connection_types.values())
        logger.info(f"Retrieved {len(types_list)} connection types")
        return types_list
        
    except Exception as e:
        logger.error(f"Failed to get connection types: {str(e)}")
        raise SisenseAPIError(f"Failed to get connection types: {str(e)}")


def test_connection(connection_id: str) -> Dict[str, Any]:
    """
    Test a specific connection to verify it's working.
    
    Args:
        connection_id: Connection ID to test.
        
    Returns:
        Dict: Test result with status and details.
        
    Raises:
        SisenseAPIError: If request fails.
    """
    http_client = get_http_client()
    headers = get_auth_headers()
    
    logger.info(f"Testing connection: {connection_id}")
    
    try:
        response = http_client.post(
            endpoint=f'/api/v2/connections/{connection_id}/test',
            headers=headers
        )
        
        # Validate response structure
        if 'status' not in response:
            response = {'status': 'success', 'details': response}
        
        logger.info(f"Connection test completed: {response.get('status', 'unknown')}")
        return response
        
    except Exception as e:
        logger.error(f"Failed to test connection {connection_id}: {str(e)}")
        raise SisenseAPIError(f"Failed to test connection {connection_id}: {str(e)}")


def get_connection_schema(connection_id: str) -> Dict[str, Any]:
    """
    Get schema information for a specific connection.
    
    Args:
        connection_id: Connection ID.
        
    Returns:
        Dict: Schema information including tables and columns.
        
    Raises:
        SisenseAPIError: If request fails.
    """
    http_client = get_http_client()
    headers = get_auth_headers()
    
    logger.info(f"Getting schema for connection: {connection_id}")
    
    try:
        response = http_client.get(
            endpoint=f'/api/v2/connections/{connection_id}/schema',
            headers=headers
        )
        
        # Validate response structure
        if 'tables' not in response:
            response = {'tables': response if isinstance(response, list) else []}
        
        table_count = len(response.get('tables', []))
        logger.info(f"Retrieved schema with {table_count} tables")
        return response
        
    except Exception as e:
        logger.error(f"Failed to get schema for connection {connection_id}: {str(e)}")
        raise SisenseAPIError(f"Failed to get schema for connection {connection_id}: {str(e)}")


def search_connections(search_term: str) -> List[Dict[str, Any]]:
    """
    Search connections by name or description.
    
    Args:
        search_term: Search term to filter connections.
        
    Returns:
        List[Dict]: Matching connections.
        
    Raises:
        SisenseAPIError: If request fails.
    """
    logger.info(f"Searching connections with term: {search_term}")
    
    try:
        all_connections = list_connections()
        
        # Filter connections by search term
        search_term_lower = search_term.lower()
        matching_connections = []
        
        for connection in all_connections:
            connection_name = connection.get('name', '').lower()
            connection_description = connection.get('description', '').lower()
            connection_type = connection.get('type', '').lower()
            
            if (search_term_lower in connection_name or 
                search_term_lower in connection_description or
                search_term_lower in connection_type):
                matching_connections.append(connection)
        
        logger.info(f"Found {len(matching_connections)} matching connections")
        return matching_connections
        
    except Exception as e:
        logger.error(f"Failed to search connections: {str(e)}")
        raise SisenseAPIError(f"Failed to search connections: {str(e)}")


def get_connection_status(connection_id: str) -> Dict[str, Any]:
    """
    Get the current status of a connection.
    
    Args:
        connection_id: Connection ID.
        
    Returns:
        Dict: Connection status information.
        
    Raises:
        SisenseAPIError: If request fails.
    """
    logger.info(f"Getting status for connection: {connection_id}")
    
    try:
        # Get connection details
        connection = get_connection(connection_id)
        
        # Try to test the connection to get current status
        try:
            test_result = test_connection(connection_id)
            status = {
                'id': connection_id,
                'name': connection.get('name', ''),
                'type': connection.get('type', ''),
                'status': test_result.get('status', 'unknown'),
                'last_tested': test_result.get('timestamp'),
                'details': test_result.get('details', {})
            }
        except SisenseAPIError:
            # If test fails, mark as offline
            status = {
                'id': connection_id,
                'name': connection.get('name', ''),
                'type': connection.get('type', ''),
                'status': 'offline',
                'last_tested': None,
                'details': {'error': 'Connection test failed'}
            }
        
        logger.info(f"Connection status: {status['status']}")
        return status
        
    except Exception as e:
        logger.error(f"Failed to get connection status {connection_id}: {str(e)}")
        raise SisenseAPIError(f"Failed to get connection status {connection_id}: {str(e)}")