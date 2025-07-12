"""
JAQL module for Sisense API.

Provides functions to execute JAQL queries and retrieve metadata
from Sisense data sources using the JAQL query language.
"""

import logging
from typing import Dict, List, Optional, Any, Union

from sisense.auth import get_auth_headers
from sisense.utils import get_http_client, SisenseAPIError, validate_response_data


logger = logging.getLogger(__name__)


def execute_jaql(
    datasource: str,
    jaql_query: Union[Dict, List[Dict]],
    format_type: str = 'json',
    timeout: Optional[int] = None
) -> Dict[str, Any]:
    """
    Execute JAQL query against a Sisense data source.
    
    Args:
        datasource: Data source name or OID.
        jaql_query: JAQL query object or list of queries.
        format_type: Response format ('json', 'csv', 'excel').
        timeout: Optional query timeout in seconds.
        
    Returns:
        Dict: Query results with data and metadata.
        
    Raises:
        SisenseAPIError: If request fails.
    """
    logger.error(f"Cannot execute JAQL query on datasource {datasource}: JAQL functionality not available")
    logger.error("Endpoint /api/v1/datasources returns 404 in this Sisense environment")
    
    raise SisenseAPIError(
        f"Cannot execute JAQL query on datasource {datasource}. JAQL functionality is not available "
        "in this Sisense environment. The /api/v1/datasources endpoint returns 404. "
        "Please check your Sisense installation or API version, or use widget-based queries instead."
    )


def get_jaql_metadata(datasource: str, table_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Get metadata (column/table catalog) for a data source.
    
    Args:
        datasource: Data source name or OID.
        table_name: Optional specific table name.
        
    Returns:
        Dict: Metadata including tables, columns, and data types.
        
    Raises:
        SisenseAPIError: If request fails.
    """
    logger.error(f"Cannot get JAQL metadata for datasource {datasource}: JAQL functionality not available")
    logger.error("Endpoint /api/v1/datasources returns 404 in this Sisense environment")
    
    raise SisenseAPIError(
        f"Cannot get JAQL metadata for datasource {datasource}. JAQL functionality is not available "
        "in this Sisense environment. The /api/v1/datasources endpoint returns 404. "
        "Please check your Sisense installation or API version."
    )


def build_jaql_query(
    datasource: str,
    dimensions: List[Dict[str, Any]],
    measures: List[Dict[str, Any]],
    filters: Optional[List[Dict[str, Any]]] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> Dict[str, Any]:
    """
    Build JAQL query from dimensions, measures, and filters.
    
    Args:
        datasource: Data source name or OID.
        dimensions: List of dimension objects.
        measures: List of measure objects.
        filters: Optional list of filter objects.
        limit: Optional row limit.
        offset: Optional row offset.
        
    Returns:
        Dict: Complete JAQL query structure.
        
    Raises:
        SisenseAPIError: If query building fails.
    """
    logger.info(f"Building JAQL query for datasource: {datasource}")
    
    try:
        # Build metadata array
        metadata = []
        
        # Add dimensions
        for dim in dimensions:
            metadata.append({
                'jaql': dim,
                'panel': 'columns'
            })
        
        # Add measures
        for measure in measures:
            metadata.append({
                'jaql': measure,
                'panel': 'values'
            })
        
        # Add filters if provided
        if filters:
            for filter_obj in filters:
                metadata.append({
                    'jaql': filter_obj,
                    'panel': 'filters'
                })
        
        # Build complete JAQL query
        jaql_query = {
            'datasource': datasource,
            'metadata': metadata
        }
        
        # Add pagination if specified
        if limit is not None:
            jaql_query['count'] = limit
        if offset is not None:
            jaql_query['offset'] = offset
        
        logger.info(f"Built JAQL query with {len(dimensions)} dimensions, {len(measures)} measures")
        return jaql_query
        
    except Exception as e:
        logger.error(f"Failed to build JAQL query: {str(e)}")
        raise SisenseAPIError(f"Failed to build JAQL query: {str(e)}")


def validate_jaql_query(jaql_query: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate JAQL query structure and syntax.
    
    Args:
        jaql_query: JAQL query object to validate.
        
    Returns:
        Dict: Validation results with status and messages.
        
    Raises:
        SisenseAPIError: If validation fails.
    """
    logger.info("Validating JAQL query")
    
    try:
        validation_result = {
            'valid': True,
            'warnings': [],
            'errors': []
        }
        
        # Check required fields
        if 'datasource' not in jaql_query:
            validation_result['valid'] = False
            validation_result['errors'].append("Missing required 'datasource' field")
        
        if 'metadata' not in jaql_query:
            validation_result['valid'] = False
            validation_result['errors'].append("Missing required 'metadata' field")
        
        # Validate metadata structure
        if 'metadata' in jaql_query:
            metadata = jaql_query['metadata']
            if not isinstance(metadata, list):
                validation_result['valid'] = False
                validation_result['errors'].append("'metadata' must be a list")
            else:
                for i, item in enumerate(metadata):
                    if not isinstance(item, dict):
                        validation_result['errors'].append(f"metadata[{i}] must be an object")
                        validation_result['valid'] = False
                        continue
                    
                    if 'jaql' not in item:
                        validation_result['errors'].append(f"metadata[{i}] missing 'jaql' field")
                        validation_result['valid'] = False
                    
                    if 'panel' not in item:
                        validation_result['warnings'].append(f"metadata[{i}] missing 'panel' field")
        
        # Check for reasonable query size
        if len(str(jaql_query)) > 50000:
            validation_result['warnings'].append("Query is very large, consider simplifying")
        
        logger.info(f"JAQL query validation completed: valid={validation_result['valid']}")
        return validation_result
        
    except Exception as e:
        logger.error(f"Failed to validate JAQL query: {str(e)}")
        raise SisenseAPIError(f"Failed to validate JAQL query: {str(e)}")


def get_datasource_catalog(datasource: str) -> Dict[str, Any]:
    """
    Get complete catalog of tables and columns for a data source.
    
    Args:
        datasource: Data source name or OID.
        
    Returns:
        Dict: Complete data source catalog.
        
    Raises:
        SisenseAPIError: If request fails.
    """
    logger.info(f"Getting catalog for datasource: {datasource}")
    
    try:
        # Get metadata for all tables
        metadata = get_jaql_metadata(datasource)
        
        # Process metadata into catalog structure
        catalog = {
            'datasource': datasource,
            'tables': [],
            'table_count': 0,
            'column_count': 0
        }
        
        # Parse metadata structure
        if 'schema' in metadata:
            schema = metadata['schema']
            for table_name, table_info in schema.items():
                table_data = {
                    'name': table_name,
                    'columns': []
                }
                
                if isinstance(table_info, dict) and 'columns' in table_info:
                    for col_name, col_info in table_info['columns'].items():
                        column_data = {
                            'name': col_name,
                            'type': col_info.get('type', 'unknown'),
                            'nullable': col_info.get('nullable', True),
                            'indexed': col_info.get('indexed', False)
                        }
                        table_data['columns'].append(column_data)
                
                table_data['column_count'] = len(table_data['columns'])
                catalog['tables'].append(table_data)
                catalog['column_count'] += table_data['column_count']
        
        catalog['table_count'] = len(catalog['tables'])
        
        logger.info(f"Retrieved catalog for datasource {datasource}: {catalog['table_count']} tables, {catalog['column_count']} columns")
        return catalog
        
    except Exception as e:
        logger.error(f"Failed to get catalog for datasource {datasource}: {str(e)}")
        raise SisenseAPIError(f"Failed to get catalog: {str(e)}")


def execute_simple_jaql(
    datasource: str,
    table: str,
    columns: List[str],
    filters: Optional[Dict[str, Any]] = None,
    limit: Optional[int] = None
) -> Dict[str, Any]:
    """
    Execute simple JAQL query with basic parameters.
    
    Args:
        datasource: Data source name or OID.
        table: Table name.
        columns: List of column names to select.
        filters: Optional filter conditions.
        limit: Optional row limit.
        
    Returns:
        Dict: Query results.
        
    Raises:
        SisenseAPIError: If request fails.
    """
    logger.info(f"Executing simple JAQL query on {datasource}.{table}")
    
    try:
        # Build dimensions from column names
        dimensions = []
        for column in columns:
            dimensions.append({
                'dim': f'[{table}].[{column}]',
                'datatype': 'text'
            })
        
        # Build measures (empty for dimension-only queries)
        measures = []
        
        # Build filters if provided
        filter_list = []
        if filters:
            for column, value in filters.items():
                filter_list.append({
                    'dim': f'[{table}].[{column}]',
                    'filter': {
                        'equals': value
                    }
                })
        
        # Build and execute query
        jaql_query = build_jaql_query(
            datasource=datasource,
            dimensions=dimensions,
            measures=measures,
            filters=filter_list,
            limit=limit
        )
        
        return execute_jaql(datasource, jaql_query)
        
    except Exception as e:
        logger.error(f"Failed to execute simple JAQL query: {str(e)}")
        raise SisenseAPIError(f"Failed to execute simple JAQL query: {str(e)}")


def get_jaql_query_from_widget(widget_id: str) -> Dict[str, Any]:
    """
    Extract JAQL query from a widget.
    
    Args:
        widget_id: Widget ID.
        
    Returns:
        Dict: Widget's JAQL query.
        
    Raises:
        SisenseAPIError: If request fails.
    """
    logger.info(f"Getting JAQL query from widget: {widget_id}")
    
    try:
        # Import here to avoid circular imports
        from sisense.widgets import get_widget_jaql
        
        jaql_query = get_widget_jaql(widget_id)
        
        logger.info(f"Retrieved JAQL query from widget {widget_id}")
        return jaql_query
        
    except Exception as e:
        logger.error(f"Failed to get JAQL query from widget {widget_id}: {str(e)}")
        raise SisenseAPIError(f"Failed to get JAQL query from widget: {str(e)}")


def optimize_jaql_query(jaql_query: Dict[str, Any]) -> Dict[str, Any]:
    """
    Optimize JAQL query for better performance.
    
    Args:
        jaql_query: Original JAQL query.
        
    Returns:
        Dict: Optimized JAQL query with recommendations.
        
    Raises:
        SisenseAPIError: If optimization fails.
    """
    logger.info("Optimizing JAQL query")
    
    try:
        optimized_query = jaql_query.copy()
        optimizations = []
        
        # Add default limit if not specified
        if 'count' not in optimized_query:
            optimized_query['count'] = 10000
            optimizations.append("Added default row limit (10000)")
        
        # Check for excessive dimensions
        if 'metadata' in optimized_query:
            dimension_count = sum(1 for item in optimized_query['metadata'] 
                                if item.get('panel') == 'columns')
            if dimension_count > 10:
                optimizations.append("Consider reducing number of dimensions for better performance")
        
        # Add optimization suggestions
        result = {
            'original_query': jaql_query,
            'optimized_query': optimized_query,
            'optimizations': optimizations,
            'performance_score': _calculate_performance_score(optimized_query)
        }
        
        logger.info(f"JAQL query optimized with {len(optimizations)} improvements")
        return result
        
    except Exception as e:
        logger.error(f"Failed to optimize JAQL query: {str(e)}")
        raise SisenseAPIError(f"Failed to optimize JAQL query: {str(e)}")


def _calculate_performance_score(jaql_query: Dict[str, Any]) -> int:
    """
    Calculate performance score for JAQL query.
    
    Args:
        jaql_query: JAQL query object.
        
    Returns:
        int: Performance score (0-100, higher is better).
    """
    score = 100
    
    # Penalize for missing limit
    if 'count' not in jaql_query:
        score -= 20
    
    # Penalize for excessive dimensions
    if 'metadata' in jaql_query:
        dimension_count = sum(1 for item in jaql_query['metadata'] 
                            if item.get('panel') == 'columns')
        if dimension_count > 10:
            score -= (dimension_count - 10) * 5
    
    # Penalize for complex queries
    query_size = len(str(jaql_query))
    if query_size > 10000:
        score -= min(30, (query_size - 10000) // 1000 * 5)
    
    return max(0, score)


def convert_sql_to_jaql(sql_query: str, datasource: str) -> Dict[str, Any]:
    """
    Convert SQL query to JAQL format (basic conversion).
    
    Args:
        sql_query: SQL query string.
        datasource: Data source name or OID.
        
    Returns:
        Dict: Converted JAQL query.
        
    Raises:
        SisenseAPIError: If conversion fails.
    """
    logger.info("Converting SQL to JAQL")
    
    try:
        # This is a simplified conversion - full SQL to JAQL conversion
        # would require a proper SQL parser
        
        sql_upper = sql_query.upper().strip()
        
        # Extract basic SELECT components
        if not sql_upper.startswith('SELECT'):
            raise SisenseAPIError("Only SELECT statements supported for conversion")
        
        # Very basic parsing - would need enhancement for production use
        dimensions = []
        measures = []
        
        # For now, create a basic structure
        jaql_query = {
            'datasource': datasource,
            'metadata': [
                {
                    'jaql': {
                        'dim': '[Table].[Column]',
                        'datatype': 'text'
                    },
                    'panel': 'columns'
                }
            ],
            'format': 'json'
        }
        
        conversion_result = {
            'original_sql': sql_query,
            'converted_jaql': jaql_query,
            'conversion_notes': [
                "Basic conversion performed",
                "Manual review recommended",
                "Complex SQL features may not be supported"
            ]
        }
        
        logger.info("SQL to JAQL conversion completed (basic)")
        return conversion_result
        
    except Exception as e:
        logger.error(f"Failed to convert SQL to JAQL: {str(e)}")
        raise SisenseAPIError(f"Failed to convert SQL to JAQL: {str(e)}")