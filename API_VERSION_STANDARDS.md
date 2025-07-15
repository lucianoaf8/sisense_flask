# API Version Standards - Sisense Flask Integration

## Overview
This document defines the standardized API version usage across the Sisense Flask integration project to ensure consistency and predictability.

## API Version Standards by Resource Type

### 1. Authentication
- **Primary Version**: Smart Routing (v1/v2 automatic detection)
- **Endpoints Used**:
  - Primary: `/api/v1/auth/isauth`
  - Fallback: `/api/v2/auth/isauth`
  - Validation: `/api/v1/dashboards` (connectivity test)
- **Rationale**: Different Sisense deployments use different auth endpoints

### 2. Data Models / Elasticubes
- **Primary Version**: v2
- **Fallback Version**: v1
- **Endpoints Used**:
  - Primary: `/api/v2/datamodels`
  - Fallback 1: `/api/v1/elasticubes/getElasticubes`
  - Fallback 2: `/api/v1/elasticubes/{model_oid}`
- **Rationale**: v2 is the modern API, but many deployments still use v1

### 3. Dashboards
- **Primary Version**: v1
- **Endpoints Used**:
  - List: `/api/v1/dashboards`
  - Get: `/api/v1/dashboards/{dashboard_id}`
  - Widgets: `/api/v1/dashboards/{dashboard_id}/widgets`
  - Export: `/api/v1/dashboards/{dashboard_id}/export/{type}`
- **Rationale**: v1 API is stable and widely supported for dashboards

### 4. Widgets
- **Primary Version**: v1
- **Endpoints Used**:
  - List: `/api/v1/widgets`
  - Get: `/api/v1/widgets/{widget_id}`
  - Data: `/api/v1/widgets/{widget_id}/data`
  - JAQL: `/api/v1/widgets/{widget_id}/jaql`
  - Export: `/api/v1/widgets/{widget_id}/export/{type}`
- **Rationale**: Widget API is mature in v1

### 5. Connections
- **Primary Version**: v2
- **Endpoints Used**:
  - List: `/api/v2/connections`
  - Get: `/api/v2/connections/{connection_id}`
  - Test: `/api/v2/connections/{connection_id}/test`
  - Schema: `/api/v2/connections/{connection_id}/schema`
- **Rationale**: Connection management is a v2 feature

### 6. Query Execution
- **Primary Version**: v1
- **Endpoints Used**:
  - SQL: `/api/v1/query/sql`
  - JAQL: `/api/v1/query`
  - Validate: `/api/v1/query/sql/validate`
- **Rationale**: Query execution is stable in v1

## Implementation Guidelines

### 1. Always Use Primary Version First
```python
def get_resource():
    try:
        # Try primary version
        return call_v2_api()
    except SisenseAPIError:
        # Fallback to secondary version
        return call_v1_api()
```

### 2. Log Version Used
```python
logger.info(f"Retrieved data using v2 API")  # Always log which version succeeded
```

### 3. Handle Version-Specific Response Formats
```python
# v1 might return direct array
if isinstance(response, list):
    return response

# v2 typically wraps in data object
if isinstance(response, dict) and 'data' in response:
    return response['data']
```

### 4. Document Fallback Behavior
Each module should clearly document its fallback behavior in docstrings:
```python
def list_models():
    """
    List all data models.
    
    API Version Strategy:
    1. Try v2: /api/v2/datamodels
    2. Fallback to v1: /api/v1/elasticubes/getElasticubes
    3. Final fallback: /elasticubes/getElasticubes (legacy)
    """
```

## Testing API Versions

### 1. Version Detection
```python
# Use the SisenseAPIVersionDetector
from sisense_api_detector import SisenseAPIVersionDetector

detector = SisenseAPIVersionDetector(base_url, token)
capabilities = detector.detect_capabilities()
print(f"v1 endpoints: {capabilities['v1_endpoints']}")
print(f"v2 endpoints: {capabilities['v2_endpoints']}")
```

### 2. Manual Testing
```bash
# Test v1 endpoint
curl -H "Authorization: Bearer $TOKEN" https://sisense.com/api/v1/dashboards

# Test v2 endpoint  
curl -H "Authorization: Bearer $TOKEN" https://sisense.com/api/v2/datamodels
```

### 3. Automated Testing
Use `test_all_apis.py` to validate all endpoints and their versions.

## Migration Path

### Phase 1 (Current)
- Mixed v1/v2 usage with smart fallbacks
- Document actual versions used

### Phase 2 (Future)
- Standardize on v2 where possible
- Maintain v1 fallbacks for compatibility

### Phase 3 (Long-term)
- Full v2 adoption when all deployments support it
- Deprecate v1 endpoints

## Endpoint Mapping Reference

| Resource | Flask Route | Sisense v1 API | Sisense v2 API |
|----------|------------|----------------|-----------------|
| Auth Validation | `/api/auth/validate` | `/api/v1/auth/isauth` | `/api/v2/auth/isauth` |
| List Models | `/api/datamodels` | `/api/v1/elasticubes/getElasticubes` | `/api/v2/datamodels` |
| Get Model | `/api/datamodels/{id}` | `/api/v1/elasticubes/{id}` | `/api/v2/datamodels/{id}` |
| List Dashboards | `/api/dashboards` | `/api/v1/dashboards` | N/A |
| List Connections | `/api/connections` | N/A | `/api/v2/connections` |
| Execute SQL | `/api/sql` | `/api/v1/query/sql` | N/A |
| Execute JAQL | `/api/jaql` | `/api/v1/query` | N/A |

## Error Handling

### Version-Specific Errors
```python
try:
    # Try v2
    response = http_client.get("/api/v2/datamodels")
except SisenseAPIError as e:
    if e.status_code == 404:
        logger.debug("v2 endpoint not found, trying v1")
        # Try v1
    else:
        # Real error, propagate
        raise
```

### Consistent Error Messages
Always include which API version failed in error messages:
```python
raise SisenseAPIError(
    f"Failed to retrieve data models. "
    f"Tried v2 (/api/v2/datamodels) and v1 (/api/v1/elasticubes/getElasticubes)."
)
```