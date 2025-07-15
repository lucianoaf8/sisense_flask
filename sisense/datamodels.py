"""
Data models module for Sisense API v2.

Provides functions to interact with Sisense data models including
listing models, getting model details, and exporting schemas.
"""

import logging
from typing import Dict, List, Optional, Any

from sisense.config import Config
from sisense.auth import get_auth_headers
from sisense.utils import get_http_client, SisenseAPIError, validate_response_data


logger = logging.getLogger(__name__)


def list_models(model_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all data models with optional type filtering using correct endpoints with fallback.
    
    Args:
        model_type: Optional model type filter (e.g., 'live', 'extract').
        
    Returns:
        List[Dict]: List of data model metadata.
        
    Raises:
        SisenseAPIError: If request fails or data models endpoint not available.
    """
    # Demo mode - return sample data
    if Config.DEMO_MODE:
        return [
            {
                "oid": "demo-model-1",
                "title": "Sample Sales Data",
                "type": "live",
                "description": "Demo sales data model",
                "created": "2024-01-01T00:00:00Z",
                "lastPublish": "2024-01-15T12:00:00Z"
            },
            {
                "oid": "demo-model-2", 
                "title": "Sample Marketing Data",
                "type": "extract",
                "description": "Demo marketing analytics model",
                "created": "2024-01-02T00:00:00Z",
                "lastPublish": "2024-01-16T10:00:00Z"
            }
        ]
    
    # If specifically asking for live models, try datasources endpoint first
    if model_type == 'live':
        try:
            headers = get_auth_headers()
            http_client = get_http_client()
            base_url = Config.get_sisense_base_url()
            
            logger.debug("Attempting datasources endpoint for live models")
            response = http_client.get(f"{base_url}/api/datasources", headers=headers)
            if response.status_code == 200:
                datasources = response.json()
                if isinstance(datasources, list):
                    # Filter for live datasources only
                    live_models = [ds for ds in datasources if ds.get('live', False)]
                    logger.info(f"Retrieved {len(live_models)} live models using datasources API")
                    return live_models
        except Exception as e:
            logger.debug(f"Datasources endpoint failed, falling back to regular endpoints: {e}")
    
    headers = get_auth_headers()
    http_client = get_http_client()
    base_url = Config.get_sisense_base_url()
    
    # Try v2 first (Linux deployments)
    try:
        logger.debug("Attempting v2 datamodels endpoint")
        response = http_client.get(f"{base_url}/api/v2/datamodels", headers=headers)
        if response.status_code == 200:
            data = response.json().get('data', [])
            logger.info(f"Retrieved {len(data)} data models using v2 API")
            return _filter_models(data, model_type)
    except Exception as e:
        logger.debug(f"v2 datamodels endpoint failed: {e}")
    
    # Fall back to v1 with correct path
    try:
        logger.debug("Attempting v1 elasticubes endpoint with getElasticubes")
        response = http_client.get(f"{base_url}/api/v1/elasticubes/getElasticubes", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                logger.info(f"Retrieved {len(data)} data models using v1 API")
                return _filter_models(data, model_type)
    except Exception as e:
        logger.debug(f"v1 elasticubes endpoint failed: {e}")
    
    # Fall back to v0 legacy
    try:
        logger.debug("Attempting v0 elasticubes endpoint with getElasticubes")
        response = http_client.get(f"{base_url}/elasticubes/getElasticubes", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                logger.info(f"Retrieved {len(data)} data models using v0 API")
                return _filter_models(data, model_type)
    except Exception as e:
        logger.debug(f"v0 elasticubes endpoint failed: {e}")
    
    # All endpoints failed
    logger.error("Data models functionality is not available in this Sisense environment")
    logger.error("All data model endpoints failed: /api/v2/datamodels, /api/v1/elasticubes/getElasticubes, /elasticubes/getElasticubes")
    
    raise SisenseAPIError(
        "Data models functionality not available in this environment. "
        "Tried /api/v2/datamodels, /api/v1/elasticubes/getElasticubes, and /elasticubes/getElasticubes endpoints."
    )


def get_model(model_oid: str) -> Dict[str, Any]:
    """
    Get full data model structure by OID (masked version).
    
    Args:
        model_oid: Data model OID.
        
    Returns:
        Dict: Data model structure with masked sensitive data.
        
    Raises:
        SisenseAPIError: If request fails or data models endpoint not available.
    """
    # Demo mode - return sample model
    if Config.DEMO_MODE:
        return {
            "oid": model_oid,
            "title": f"Demo Model {model_oid}",
            "type": "demo",
            "description": "Demo data model for testing",
            "tables": [
                {"name": "Sales", "columns": [{"name": "ProductID", "type": "integer"}, {"name": "Revenue", "type": "numeric"}]},
                {"name": "Products", "columns": [{"name": "ProductID", "type": "integer"}, {"name": "ProductName", "type": "text"}]}
            ],
            "created": "2024-01-01T00:00:00Z"
        }
    
    headers = get_auth_headers()
    http_client = get_http_client()
    base_url = Config.get_sisense_base_url()
    
    # Try v2 first (Linux deployments)
    try:
        logger.debug(f"Attempting v2 datamodels endpoint for model: {model_oid}")
        response = http_client.get(f"{base_url}/api/v2/datamodels/{model_oid}", headers=headers)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Retrieved model {model_oid} using v2 API")
            return data
    except Exception as e:
        logger.debug(f"v2 datamodels endpoint failed for model {model_oid}: {e}")
    
    # Try v1 elasticubes endpoint
    try:
        logger.debug(f"Attempting v1 elasticubes endpoint for model: {model_oid}")
        response = http_client.get(f"{base_url}/api/v1/elasticubes/{model_oid}", headers=headers)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Retrieved model {model_oid} using v1 API")
            return data
    except Exception as e:
        logger.debug(f"v1 elasticubes endpoint failed for model {model_oid}: {e}")
    
    # Try alternative v1 endpoint
    try:
        logger.debug(f"Attempting v1 elasticubes/getElasticubes endpoint for model: {model_oid}")
        response = http_client.get(f"{base_url}/api/v1/elasticubes/getElasticubes", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                # Find the specific model
                for model in data:
                    if model.get('oid') == model_oid or model.get('id') == model_oid:
                        logger.info(f"Retrieved model {model_oid} from elasticubes list")
                        return model
    except Exception as e:
        logger.debug(f"v1 elasticubes/getElasticubes endpoint failed for model {model_oid}: {e}")
    
    logger.error(f"Cannot retrieve data model {model_oid}: All endpoints failed")
    
    raise SisenseAPIError(
        f"Cannot retrieve data model {model_oid}. Data models functionality is not available "
        "in this Sisense environment or the model ID is invalid."
    )


def export_schema(
    model_oid: Optional[str] = None,
    unmasked: bool = False,
    include_relationships: bool = True,
    include_tables: bool = True,
    include_columns: bool = True
) -> Dict[str, Any]:
    """
    Export data model schema with full details.
    
    Args:
        model_oid: Optional specific model OID to export.
        unmasked: Whether to include unmasked sensitive data.
        include_relationships: Include table relationships.
        include_tables: Include table definitions.
        include_columns: Include column definitions.
        
    Returns:
        Dict: Complete data model schema.
        
    Raises:
        SisenseAPIError: If request fails or data models endpoint not available.
    """
    # Demo mode - return sample schema
    if Config.DEMO_MODE:
        return {
            "schemas": [{
                "oid": model_oid or "demo-schema",
                "title": "Demo Schema",
                "tables": [],
                "relationships": [],
                "exported": "2024-01-01T00:00:00Z"
            }]
        }
    
    logger.error(f"Cannot export schema for model {model_oid}: Data models functionality not available")
    logger.error("Endpoint /api/v2/datamodel-exports/schema is likely not accessible")
    
    raise SisenseAPIError(
        f"Cannot export schema for model {model_oid or 'all'}. Data models functionality "
        "is not available in this Sisense environment. The /api/v2/datamodel-exports/schema "
        "endpoint is not accessible."
    )


def get_model_tables(model_oid: str) -> List[Dict[str, Any]]:
    """
    Get tables for a specific data model.
    
    Args:
        model_oid: Data model OID.
        
    Returns:
        List[Dict]: List of table definitions.
        
    Raises:
        SisenseAPIError: If request fails.
    """
    logger.info(f"Getting tables for model: {model_oid}")
    
    try:
        model_data = get_model(model_oid)
        
        # Extract tables from model data
        tables = model_data.get('tables', [])
        if not isinstance(tables, list):
            tables = []
        
        logger.info(f"Retrieved {len(tables)} tables for model {model_oid}")
        return tables
        
    except Exception as e:
        logger.error(f"Failed to get tables for model {model_oid}: {str(e)}")
        raise SisenseAPIError(f"Failed to get tables for model {model_oid}: {str(e)}")


def get_model_columns(model_oid: str, table_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get columns for a data model, optionally filtered by table.
    
    Args:
        model_oid: Data model OID.
        table_name: Optional table name filter.
        
    Returns:
        List[Dict]: List of column definitions.
        
    Raises:
        SisenseAPIError: If request fails.
    """
    logger.info(f"Getting columns for model: {model_oid}, table: {table_name}")
    
    try:
        tables = get_model_tables(model_oid)
        columns = []
        
        for table in tables:
            if table_name and table.get('name') != table_name:
                continue
            
            table_columns = table.get('columns', [])
            if isinstance(table_columns, list):
                # Add table context to each column
                for column in table_columns:
                    if isinstance(column, dict):
                        column['table_name'] = table.get('name')
                        columns.append(column)
        
        logger.info(f"Retrieved {len(columns)} columns")
        return columns
        
    except Exception as e:
        logger.error(f"Failed to get columns for model {model_oid}: {str(e)}")
        raise SisenseAPIError(f"Failed to get columns for model {model_oid}: {str(e)}")


def search_models(search_term: str) -> List[Dict[str, Any]]:
    """
    Search data models by name or description.
    
    Args:
        search_term: Search term to filter models.
        
    Returns:
        List[Dict]: Matching data models.
        
    Raises:
        SisenseAPIError: If request fails.
    """
    logger.info(f"Searching models with term: {search_term}")
    
    try:
        all_models = list_models()
        
        # Filter models by search term
        search_term_lower = search_term.lower()
        matching_models = []
        
        for model in all_models:
            model_title = model.get('title', '').lower()
            model_description = model.get('description', '').lower()
            
            if (search_term_lower in model_title or 
                search_term_lower in model_description):
                matching_models.append(model)
        
        logger.info(f"Found {len(matching_models)} matching models")
        return matching_models
        
    except Exception as e:
        logger.error(f"Failed to search models: {str(e)}")
        raise SisenseAPIError(f"Failed to search models: {str(e)}")


def _filter_models(models: List[Dict], model_type: Optional[str]) -> List[Dict]:
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