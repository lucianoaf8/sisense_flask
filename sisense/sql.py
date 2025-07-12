"""
SQL module for Sisense API.

Provides functions to execute SQL queries against Sisense data sources.
Requires admin privileges for SQL execution.
"""

import logging
from typing import Dict, List, Optional, Any, Union

from sisense.auth import get_auth_headers
from sisense.utils import get_http_client, SisenseAPIError, validate_response_data


logger = logging.getLogger(__name__)


def execute_sql(
    datasource: str,
    query: str,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    timeout: Optional[int] = None
) -> Dict[str, Any]:
    """
    Execute SQL query against a Sisense data source.
    
    Args:
        datasource: Data source name or OID.
        query: SQL query string (read-only queries only).
        limit: Optional limit on number of rows returned.
        offset: Optional offset for pagination.
        timeout: Optional query timeout in seconds.
        
    Returns:
        Dict: Query results including data, columns, and metadata.
        
    Raises:
        SisenseAPIError: If request fails or query is invalid.
    """
    logger.error(f"Cannot execute SQL query on datasource {datasource}: SQL functionality not available")
    logger.error("Endpoint /api/v1/datasources returns 404 in this Sisense environment")
    
    raise SisenseAPIError(
        f"Cannot execute SQL query on datasource {datasource}. SQL functionality is not available "
        "in this Sisense environment. The /api/v1/datasources endpoint returns 404. "
        "Please check your Sisense installation or API version, or use JAQL queries instead."
    )


def validate_sql_query(query: str) -> Dict[str, Any]:
    """
    Validate SQL query syntax and permissions.
    
    Args:
        query: SQL query string to validate.
        
    Returns:
        Dict: Validation results with status and messages.
        
    Raises:
        SisenseAPIError: If validation fails.
    """
    logger.info("Validating SQL query")
    
    try:
        validation_result = {
            'valid': True,
            'is_read_only': False,
            'warnings': [],
            'errors': []
        }
        
        # Check if query is read-only
        if not _is_read_only_query(query):
            validation_result['valid'] = False
            validation_result['errors'].append("Only read-only SELECT queries are allowed")
        else:
            validation_result['is_read_only'] = True
        
        # Check for potentially dangerous keywords
        dangerous_keywords = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 'TRUNCATE']
        query_upper = query.upper()
        
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                validation_result['valid'] = False
                validation_result['errors'].append(f"Dangerous keyword '{keyword}' found in query")
        
        # Check for common SQL injection patterns
        injection_patterns = [';--', 'UNION', 'EXEC', 'EXECUTE', 'SP_', 'XP_']
        for pattern in injection_patterns:
            if pattern in query_upper:
                validation_result['warnings'].append(f"Potential SQL injection pattern '{pattern}' detected")
        
        # Check query length
        if len(query) > 10000:
            validation_result['warnings'].append("Query is very long, consider breaking it into smaller parts")
        
        logger.info(f"SQL query validation completed: valid={validation_result['valid']}")
        return validation_result
        
    except Exception as e:
        logger.error(f"Failed to validate SQL query: {str(e)}")
        raise SisenseAPIError(f"Failed to validate SQL query: {str(e)}")


def get_datasource_tables(datasource: str) -> List[Dict[str, Any]]:
    """
    Get list of tables available in a data source.
    
    Args:
        datasource: Data source name or OID.
        
    Returns:
        List[Dict]: List of table information.
        
    Raises:
        SisenseAPIError: If request fails.
    """
    logger.info(f"Getting tables for datasource: {datasource}")
    
    try:
        # Execute SHOW TABLES query
        query = "SHOW TABLES"
        response = execute_sql(datasource, query)
        
        # Parse results into table list
        tables = []
        if 'data' in response:
            for row in response['data']:
                if isinstance(row, list) and len(row) > 0:
                    tables.append({
                        'name': row[0],
                        'type': 'table'
                    })
                elif isinstance(row, dict) and 'Tables_in_' in str(row):
                    # Handle MySQL format
                    table_name = list(row.values())[0]
                    tables.append({
                        'name': table_name,
                        'type': 'table'
                    })
        
        logger.info(f"Retrieved {len(tables)} tables for datasource {datasource}")
        return tables
        
    except Exception as e:
        logger.error(f"Failed to get tables for datasource {datasource}: {str(e)}")
        raise SisenseAPIError(f"Failed to get tables for datasource {datasource}: {str(e)}")


def get_table_schema(datasource: str, table_name: str) -> Dict[str, Any]:
    """
    Get schema information for a specific table.
    
    Args:
        datasource: Data source name or OID.
        table_name: Table name.
        
    Returns:
        Dict: Table schema including columns and data types.
        
    Raises:
        SisenseAPIError: If request fails.
    """
    logger.info(f"Getting schema for table: {table_name} in datasource: {datasource}")
    
    try:
        # Execute DESCRIBE or SHOW COLUMNS query
        query = f"DESCRIBE {table_name}"
        response = execute_sql(datasource, query)
        
        # Parse results into schema
        columns = []
        if 'data' in response:
            for row in response['data']:
                if isinstance(row, list) and len(row) >= 2:
                    columns.append({
                        'name': row[0],
                        'type': row[1],
                        'nullable': row[2] if len(row) > 2 else None,
                        'key': row[3] if len(row) > 3 else None,
                        'default': row[4] if len(row) > 4 else None,
                        'extra': row[5] if len(row) > 5 else None
                    })
        
        schema = {
            'datasource': datasource,
            'table_name': table_name,
            'columns': columns,
            'column_count': len(columns)
        }
        
        logger.info(f"Retrieved schema for table {table_name} with {len(columns)} columns")
        return schema
        
    except Exception as e:
        logger.error(f"Failed to get schema for table {table_name}: {str(e)}")
        raise SisenseAPIError(f"Failed to get schema for table {table_name}: {str(e)}")


def execute_query_with_pagination(
    datasource: str,
    query: str,
    page_size: int = 1000,
    max_pages: int = 10
) -> Dict[str, Any]:
    """
    Execute SQL query with automatic pagination.
    
    Args:
        datasource: Data source name or OID.
        query: SQL query string.
        page_size: Number of rows per page.
        max_pages: Maximum number of pages to retrieve.
        
    Returns:
        Dict: Paginated query results.
        
    Raises:
        SisenseAPIError: If request fails.
    """
    logger.info(f"Executing paginated query on datasource: {datasource}")
    
    try:
        all_data = []
        page = 0
        total_rows = 0
        
        while page < max_pages:
            offset = page * page_size
            
            response = execute_sql(
                datasource=datasource,
                query=query,
                limit=page_size,
                offset=offset
            )
            
            page_data = response.get('data', [])
            if not page_data:
                break
            
            all_data.extend(page_data)
            total_rows += len(page_data)
            
            # If we got fewer rows than page_size, we're done
            if len(page_data) < page_size:
                break
            
            page += 1
        
        result = {
            'data': all_data,
            'columns': response.get('columns', []),
            'total_rows': total_rows,
            'pages_retrieved': page + 1,
            'page_size': page_size
        }
        
        logger.info(f"Paginated query completed: {total_rows} rows, {page + 1} pages")
        return result
        
    except Exception as e:
        logger.error(f"Failed to execute paginated query: {str(e)}")
        raise SisenseAPIError(f"Failed to execute paginated query: {str(e)}")


def _is_read_only_query(query: str) -> bool:
    """
    Check if SQL query is read-only (SELECT only).
    
    Args:
        query: SQL query string.
        
    Returns:
        bool: True if query is read-only.
    """
    query_stripped = query.strip().upper()
    
    # Must start with SELECT
    if not query_stripped.startswith('SELECT'):
        return False
    
    # Check for dangerous keywords
    dangerous_keywords = [
        'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 
        'TRUNCATE', 'EXEC', 'EXECUTE', 'CALL', 'MERGE'
    ]
    
    for keyword in dangerous_keywords:
        if keyword in query_stripped:
            return False
    
    return True


def get_query_execution_plan(datasource: str, query: str) -> Dict[str, Any]:
    """
    Get execution plan for a SQL query.
    
    Args:
        datasource: Data source name or OID.
        query: SQL query string.
        
    Returns:
        Dict: Query execution plan.
        
    Raises:
        SisenseAPIError: If request fails.
    """
    logger.info(f"Getting execution plan for query on datasource: {datasource}")
    
    try:
        # Add EXPLAIN to the query
        explain_query = f"EXPLAIN {query}"
        
        response = execute_sql(datasource, explain_query)
        
        execution_plan = {
            'datasource': datasource,
            'original_query': query,
            'plan': response.get('data', []),
            'columns': response.get('columns', [])
        }
        
        logger.info(f"Retrieved execution plan for query on datasource {datasource}")
        return execution_plan
        
    except Exception as e:
        logger.error(f"Failed to get execution plan: {str(e)}")
        raise SisenseAPIError(f"Failed to get execution plan: {str(e)}")


def estimate_query_cost(datasource: str, query: str) -> Dict[str, Any]:
    """
    Estimate cost/complexity of a SQL query.
    
    Args:
        datasource: Data source name or OID.
        query: SQL query string.
        
    Returns:
        Dict: Query cost estimation.
        
    Raises:
        SisenseAPIError: If request fails.
    """
    logger.info(f"Estimating cost for query on datasource: {datasource}")
    
    try:
        # Simple cost estimation based on query characteristics
        cost_estimate = {
            'datasource': datasource,
            'query': query,
            'complexity_score': 0,
            'factors': [],
            'recommendations': []
        }
        
        query_upper = query.upper()
        
        # Check for expensive operations
        if 'JOIN' in query_upper:
            cost_estimate['complexity_score'] += 2
            cost_estimate['factors'].append('Contains JOIN operations')
        
        if 'GROUP BY' in query_upper:
            cost_estimate['complexity_score'] += 1
            cost_estimate['factors'].append('Contains GROUP BY')
        
        if 'ORDER BY' in query_upper:
            cost_estimate['complexity_score'] += 1
            cost_estimate['factors'].append('Contains ORDER BY')
        
        if 'DISTINCT' in query_upper:
            cost_estimate['complexity_score'] += 1
            cost_estimate['factors'].append('Contains DISTINCT')
        
        if 'SUBQUERY' in query_upper or '(' in query:
            cost_estimate['complexity_score'] += 2
            cost_estimate['factors'].append('Contains subqueries')
        
        # Provide recommendations
        if cost_estimate['complexity_score'] > 5:
            cost_estimate['recommendations'].append('Consider adding appropriate indexes')
            cost_estimate['recommendations'].append('Consider using LIMIT to reduce result set')
        
        if len(query) > 1000:
            cost_estimate['recommendations'].append('Query is complex, consider breaking into smaller parts')
        
        logger.info(f"Estimated query cost: {cost_estimate['complexity_score']}")
        return cost_estimate
        
    except Exception as e:
        logger.error(f"Failed to estimate query cost: {str(e)}")
        raise SisenseAPIError(f"Failed to estimate query cost: {str(e)}")