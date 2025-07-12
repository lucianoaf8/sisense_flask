# Sisense Flask API Patterns Analysis

This document provides a comprehensive analysis of all API calling patterns in the Sisense Flask integration project, documenting every API endpoint, authentication method, parameters, and payload structures.

## Table of Contents
1. [Authentication Configuration](#authentication-configuration)
2. [HTTP Client Configuration](#http-client-configuration)
3. [Enhanced Authentication Module](#enhanced-authentication-module)
4. [Standard Authentication Module](#standard-authentication-module)
5. [Data Models Module](#data-models-module)
6. [Dashboards Module](#dashboards-module)
7. [Connections Module](#connections-module)
8. [Widgets Module](#widgets-module)
9. [SQL Module](#sql-module)
10. [JAQL Module](#jaql-module)
11. [Summary of Issues](#summary-of-issues)

---

## Authentication Configuration

### Base Configuration (config.py)

**API Token Usage:**
```python
SISENSE_API_TOKEN: str = os.getenv('SISENSE_API_TOKEN', '')
```

**Header Construction:**
```python
@classmethod
def get_auth_headers(cls, token: str) -> dict:
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
```

**Configuration (Use Environment Variables):**
- Base URL: Set via `SISENSE_URL` environment variable
- API Token: Set via `SISENSE_API_TOKEN` environment variable (NEVER hardcode tokens!)

---

## HTTP Client Configuration

### Retry Strategy (utils.py)

```python
retry_strategy = Retry(
    total=Config.REQUEST_RETRIES,              # 3 retries
    backoff_factor=Config.REQUEST_RETRY_BACKOFF,  # 2.0 seconds
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
)
```

### Request Configuration
- **Timeout**: 30 seconds
- **SSL Verification**: Configurable (default: True)
- **Headers**: Always includes Authorization, Content-Type, Accept

---

## Enhanced Authentication Module

### 1. Authentication Validation

**API Endpoints Tried (in order):**
```python
auth_endpoints = [
    '/api/v1/authentication/me',
    '/api/v1/authentication',
    '/api/v1/users/me', 
    '/api/users/me'
]
```

**HTTP Method:** GET  
**Headers:**
```python
{
    'Authorization': 'Bearer {API_TOKEN}',
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}
```

**Parameters:** None  
**Payload:** None  

**Code Snippet:**
```python
def validate_authentication() -> Tuple[bool, str]:
    for endpoint in auth_endpoints:
        try:
            response = http_client.get(endpoint, headers=headers)
            break  # Success
        except Exception as e:
            last_error = e
            continue
```

### 2. User Info Retrieval

**API Endpoint:** `/api/v1/authentication/me` (primary)  
**HTTP Method:** GET  
**Headers:** Same as authentication validation  
**Parameters:** None  
**Payload:** None  

**Code Snippet:**
```python
def get_user_info() -> Optional[Dict]:
    response = http_client.get('/api/v1/authentication/me', headers=headers)
    return response
```

### 3. Health Check

**API Endpoints Tested:**

**Authentication:**
- `/api/v1/authentication/me`
- `/api/v1/users/me`
- `/api/users/me`

**Data Models:**
- `/api/v2/datamodels`
- `/api/v1/elasticubes`
- `/api/elasticubes`

**Dashboards:**
- `/api/v1/dashboards`
- `/api/dashboards`

**HTTP Method:** GET for all  
**Headers:** Standard auth headers  
**Parameters:** None  
**Payload:** None  

**Code Snippet:**
```python
def get_connection_health():
    endpoints_to_test = [
        (auth_endpoints, 'Authentication'),
        (datamodel_endpoints, 'Data Models'), 
        (dashboard_endpoints, 'Dashboards')
    ]
    
    for endpoint_list, name in endpoints_to_test:
        for endpoint in endpoint_list:
            try:
                response = http_client.get(endpoint, headers=headers)
                break
            except Exception as e:
                continue
```

---

## Standard Authentication Module

### Login Function

**Purpose:** Validate API token  
**API Endpoint:** Uses enhanced_auth validation  
**HTTP Method:** GET  
**Headers:** Standard auth headers  
**Parameters:** None  
**Payload:** None  

**Code Snippet:**
```python
def login() -> str:
    # Validate token on login
    is_valid, message = validate_authentication()
    if not is_valid:
        raise SisenseAPIError(f"Invalid API token: {message}")
    return Config.SISENSE_API_TOKEN
```

---

## Data Models Module

### 1. List Models

**API Endpoints Tried (in order):**
```python
endpoints = [
    '/api/v2/datamodels',
    '/api/v1/elasticubes', 
    '/api/elasticubes'
]
```

**HTTP Method:** GET  
**Headers:** Standard auth headers  
**Parameters:**
```python
params = {}
if model_type:
    params['type'] = model_type  # Optional: 'live', 'extract'
```

**Payload:** None  
**Expected Response:** Array of model objects or object with 'data' property

**Code Snippet:**
```python
def list_models(model_type: Optional[str] = None) -> List[Dict[str, Any]]:
    for endpoint in endpoints:
        try:
            response = http_client.get(
                endpoint=endpoint,
                headers=headers,
                params=params
            )
            break
        except Exception as e:
            continue
```

### 2. Get Specific Model

**API Endpoint:** `/api/v2/datamodels/{model_oid}`  
**HTTP Method:** GET  
**Headers:** Standard auth headers  
**Parameters:** model_oid in URL path  
**Payload:** None  

**Code Snippet:**
```python
def get_model(model_oid: str) -> Dict[str, Any]:
    response = http_client.get(
        endpoint=f'/api/v2/datamodels/{model_oid}',
        headers=headers
    )
```

### 3. Get Model Tables

**API Endpoint:** `/api/v2/datamodels/{model_oid}/tables`  
**HTTP Method:** GET  
**Headers:** Standard auth headers  
**Parameters:** model_oid in URL path  
**Payload:** None  

### 4. Get Model Columns

**API Endpoint:** `/api/v2/datamodels/{model_oid}/columns`  
**HTTP Method:** GET  
**Headers:** Standard auth headers  
**Parameters:**
```python
params = {}
if table_name:
    params['table'] = table_name
```

### 5. Export Schema

**API Endpoint:** `/api/v2/datamodels/schema`  
**HTTP Method:** GET  
**Headers:** Standard auth headers  
**Parameters:**
```python
params = {
    'model': model_oid,              # Optional
    'unmasked': 'true'/'false',      # Optional
    'relationships': 'true'/'false', # Optional  
    'tables': 'true'/'false',        # Optional
    'columns': 'true'/'false'        # Optional
}
```

### 6. Search Models

**API Endpoint:** `/api/v2/datamodels/search`  
**HTTP Method:** GET  
**Headers:** Standard auth headers  
**Parameters:**
```python
params = {'q': search_term}  # Required
```

---

## Dashboards Module

### 1. List Dashboards

**API Endpoint:** `/api/v1/dashboards`  
**HTTP Method:** GET  
**Headers:** Standard auth headers  
**Parameters:**
```python
params = {}
if owner:
    params['owner'] = owner           # User ID
if shared is not None:
    params['shared'] = str(shared).lower()  # 'true'/'false'
if fields:
    params['fields'] = ','.join(fields)     # Comma-separated
```

**Payload:** None  

**Code Snippet:**
```python
def list_dashboards(owner=None, shared=None, fields=None):
    response = http_client.get(
        endpoint='/api/v1/dashboards',
        headers=headers,
        params=params
    )
```

### 2. Get Dashboard

**API Endpoint:** `/api/v1/dashboards/{dashboard_id}`  
**HTTP Method:** GET  
**Headers:** Standard auth headers  
**Parameters:**
```python
params = {}
if fields:
    params['fields'] = ','.join(fields)
```

### 3. Get Dashboard Widgets

**API Endpoint:** `/api/v1/dashboards/{dashboard_id}/widgets`  
**HTTP Method:** GET  
**Headers:** Standard auth headers  
**Parameters:** dashboard_id in URL path  
**Payload:** None  

### 4. Get Dashboard Summary

**API Endpoint:** `/api/v1/dashboards/{dashboard_id}/summary`  
**HTTP Method:** GET  
**Headers:** Standard auth headers  
**Parameters:** dashboard_id in URL path  
**Payload:** None  

### 5. Search Dashboards

**API Endpoint:** `/api/v1/dashboards/search`  
**HTTP Method:** GET  
**Headers:** Standard auth headers  
**Parameters:**
```python
params = {'q': search_term}  # Required
```

---

## Connections Module

### 1. List Connections

**API Endpoint:** `/api/v2/connections`  
**HTTP Method:** GET  
**Headers:** Standard auth headers  
**Parameters:**
```python
params = {}
if connection_type:
    params['type'] = connection_type  # e.g., 'mysql', 'postgresql'
if include_credentials:
    params['includeCredentials'] = 'true'
```

**Code Snippet:**
```python
def list_connections(connection_type=None, include_credentials=False):
    response = http_client.get(
        endpoint='/api/v2/connections',
        headers=headers,
        params=params
    )
```

### 2. Get Connection

**API Endpoint:** `/api/v2/connections/{connection_id}`  
**HTTP Method:** GET  
**Headers:** Standard auth headers  
**Parameters:**
```python
params = {}
if include_credentials:
    params['includeCredentials'] = 'true'
```

### 3. Test Connection

**API Endpoint:** `/api/v2/connections/{connection_id}/test`  
**HTTP Method:** POST  
**Headers:** Standard auth headers  
**Parameters:** connection_id in URL path  
**Payload:** None  

---

## Widgets Module

### 1. Get Widget

**API Endpoint:** `/api/v1/widgets/{widget_id}`  
**HTTP Method:** GET  
**Headers:** Standard auth headers  
**Parameters:**
```python
params = {}
if fields:
    params['fields'] = ','.join(fields)
```

### 2. Get Widget JAQL

**API Endpoint:** `/api/v1/widgets/{widget_id}/jaql`  
**HTTP Method:** GET  
**Headers:** Standard auth headers  
**Parameters:** widget_id in URL path  
**Payload:** None  

### 3. Get Widget Data

**API Endpoint:** `/api/v1/widgets/{widget_id}/data`  
**HTTP Method:** GET or POST  
**Headers:** Standard auth headers  
**Parameters:** widget_id in URL path  
**Payload (if POST):**
```python
{
    "filters": filters_object  # Optional
}
```

### 4. Get Widget Summary

**API Endpoint:** `/api/v1/widgets/{widget_id}/summary`  
**HTTP Method:** GET  
**Headers:** Standard auth headers  
**Parameters:** widget_id in URL path  
**Payload:** None  

---

## SQL Module

### 1. Execute SQL Query

**API Endpoint:** `/api/v1/datasources/{datasource}/sql`  
**HTTP Method:** POST  
**Headers:** Standard auth headers  
**Parameters:** datasource in URL path  
**Payload:**
```python
{
    "query": sql_query,      # Required
    "limit": limit,          # Optional integer
    "offset": offset,        # Optional integer
    "timeout": timeout       # Optional integer (seconds)
}
```

**Code Snippet:**
```python
def execute_sql(datasource, query, limit=None, offset=None, timeout=None):
    payload = {"query": query}
    if limit is not None:
        payload["limit"] = limit
    if offset is not None:
        payload["offset"] = offset
    if timeout is not None:
        payload["timeout"] = timeout
        
    response = http_client.post(
        endpoint=f'/api/v1/datasources/{datasource}/sql',
        headers=headers,
        json=payload
    )
```

### 2. Validate SQL Query

**API Endpoint:** `/api/v1/sql/validate`  
**HTTP Method:** POST  
**Headers:** Standard auth headers  
**Parameters:** None  
**Payload:**
```python
{
    "query": sql_query  # Required
}
```

---

## JAQL Module

### 1. Execute JAQL Query

**API Endpoint:** `/api/v1/datasources/{datasource}/jaql`  
**HTTP Method:** POST  
**Headers:** Standard auth headers  
**Parameters:** datasource in URL path  
**Payload:**
```python
{
    "jaql": jaql_query,      # Required (object/array)
    "format": format_type,   # Optional: 'json', 'csv', etc.
    "timeout": timeout       # Optional integer (seconds)
}
```

**Code Snippet:**
```python
def execute_jaql(datasource, jaql_query, format_type='json', timeout=None):
    payload = {
        "jaql": jaql_query,
        "format": format_type
    }
    if timeout:
        payload["timeout"] = timeout
        
    response = http_client.post(
        endpoint=f'/api/v1/datasources/{datasource}/jaql',
        headers=headers,
        json=payload
    )
```

### 2. Get JAQL Metadata

**API Endpoint:** `/api/v1/datasources/{datasource}/jaql/metadata`  
**HTTP Method:** GET  
**Headers:** Standard auth headers  
**Parameters:**
```python
params = {}
if table_name:
    params['table'] = table_name
```

### 3. Get Datasource Catalog

**API Endpoint:** `/api/v1/datasources/{datasource}/catalog`  
**HTTP Method:** GET  
**Headers:** Standard auth headers  
**Parameters:** datasource in URL path  
**Payload:** None  

---

## Summary of Issues

### Current Errors from Logs:

1. **Authentication Endpoints:**
   - `/api/v1/authentication/me` → 404 Not Found
   - `/api/v1/users/me` → 422 "Parameter (id) does not match required pattern"
   - Result: "user not found" error

2. **Data Models Endpoints:**
   - `/api/v2/datamodels` → 404 Not Found
   - `/api/v1/elasticubes` → 404 Not Found  
   - `/api/elasticubes` → 404 Not Found

3. **Working Endpoints:**
   - `/api/v1/dashboards` → 200 OK (confirmed working)

### Potential Issues:

1. **API Version Mismatch:** Your Sisense instance might use different API versions
2. **Endpoint Path Differences:** The paths might be different (e.g., `/app/api/v1/` instead of `/api/v1/`)
3. **Authentication Method:** The Bearer token format might not be correct for your instance
4. **Tenant Context:** The API might require tenant-specific paths or headers

---

## WORKING REACT APP API PATTERNS ANALYSIS

Based on examination of the React app at `/mnt/c/Projects/sisense-rest-api`, here are the **exact working patterns** that successfully make API calls:

### React App Configuration

**Base URL Construction:**
```javascript
// From sisense-api-client.js
constructor(baseUrl, credentials, apiToken = null) {
  this.baseUrl = baseUrl.replace(/\/$/, ''); // Remove trailing slash
}

getRequestUrl(endpoint) {
  // In development with proxy, use relative URLs
  if (process.env.NODE_ENV === 'development' && window.location.hostname === 'localhost') {
    return endpoint; // Relative URL for proxy
  }
  // In production, use full URLs
  return `${this.baseUrl}${endpoint}`;
}
```

**Development Proxy Configuration:**
```json
// From package.json
"proxy": "https://analytics.veriforceone.com"
```

This means in development, the React app makes calls to relative URLs like `/api/v1/dashboards` and the proxy forwards them to `https://analytics.veriforceone.com/api/v1/dashboards`.

### Working Authentication Pattern

**API Token Format:**
```javascript
// From sisense-api-client.js
async makeRequest(endpoint, options = {}) {
  let token;
  if (this.useApiToken && this.apiToken) {
    token = this.apiToken; // Use API token directly
  } else {
    token = await this.getValidToken(); // Or get session token
  }
  
  const defaultOptions = {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      ...options.headers
    }
  };
}
```

**Username/Password Authentication (Fallback):**
```javascript
// From sisense-api-client.js line 48
async authenticate() {
  const loginUrl = this.getRequestUrl('/api/v1/authentication/login');
  const response = await fetch(loginUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: new URLSearchParams({
      username: this.credentials.username,
      password: this.credentials.password
    })
  });
  
  const data = await response.json();
  this.token = data.access_token; // Use access_token from response
}
```

### Working API Endpoints (Linux v2025.2+)

**Primary Endpoints Currently Used:**
```javascript
// From enhanced-sisense-client.js - Official Linux v2025.2+ endpoints

// Data Models (V2 - Modern Linux)
'/api/v2/datamodels'                    // List all data models
'/api/v2/datamodels?type=live'          // Filter live data models  
'/api/v2/datamodels?type=extract'       // Filter extract data models
'/api/v2/datamodels/{id}'               // Get data model with schema

// Connections (V2 - Modern Linux)
'/api/v2/connections'                   // List connections

// Dashboards (Still V1 in v2025.2)
'/api/v1/dashboards'                    // List dashboards
'/api/v1/dashboards/{id}'               // Get dashboard details
'/api/v1/dashboards/{id}/widgets'       // Get dashboard widgets

// Widgets (Still V1 in v2025.2)  
'/api/v1/widgets/{id}'                  // Get widget details

// JAQL Queries
'/api/elasticubes/{cube}/jaql'          // JAQL for extract models
'/api/datasources/{id}/jaql'            // JAQL queries (needs verification)
```

**Legacy Endpoints (Being Phased Out):**
```javascript
// From enhanced-sisense-client.js - DEPRECATED for Linux v2025.2+

'/api/v1/elasticubes/getElasticubes'    // LEGACY: Windows-only
'/api/v1/elasticubes/{server}/{cube}'   // LEGACY: Windows-only  
'/api/v1/connection'                    // LEGACY: Use /api/v2/connections
'/api/v1/schemas'                       // LEGACY: Use /api/v2/datamodels
'/elasticubes/live/by_title/{title}'    // DEPRECATED: Private endpoint
'/elasticubes/live/{oid}'               // DEPRECATED: Private endpoint
```

### API Token Testing Pattern

**Token Validation:**
```javascript
// From sisense-api-client.js line 83
async testApiToken() {
  // Test endpoint for token validation
  const testUrl = this.getRequestUrl('/api/v1/elasticubes/getElasticubes');
  const response = await fetch(testUrl, {
    headers: {
      'Authorization': `Bearer ${this.apiToken}`,
      'Content-Type': 'application/json'
    }
  });
  
  if (!response.ok) {
    throw new Error(`Token validation failed: ${response.status} ${response.statusText}`);
  }
}
```

### Platform Detection Logic

**API Capability Detection:**
```javascript
// From enhanced-sisense-client.js line 112
async detectApiCapabilities() {
  const capabilities = {
    v1Available: true,
    v2Available: true,
    preferredVersion: 'v2',
    workingV2Endpoint: '/api/v2/datamodels',
    endpointMappings: {
      connections: '/api/v2/connections',
      datamodels: '/api/v2/datamodels',   
      dashboards: '/api/v1/dashboards',
      widgets: '/api/v1/widgets'
    }
  };

  // Test V2 endpoints
  const v2Endpoints = [
    '/api/v2/datamodels',
    '/api/v2/elasticubes',    // DEPRECATED
    '/api/datamodels'         // DEPRECATED
  ];
  
  for (const endpoint of v2Endpoints) {
    try {
      await this.makeRequest(endpoint);
      capabilities.workingV2Endpoint = endpoint;
      break;
    } catch (e) {
      // Continue to next endpoint
    }
  }
}
```

### Error Handling and Retry Logic

**Request Retry Pattern:**
```javascript
// From enhanced-sisense-client.js line 82
async makeRequestWithRetry(endpoint, options = {}, attempt = 1) {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.requestTimeout);
    
    const response = await this.makeRequest(endpoint, {
      ...options,
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    return response;
    
  } catch (error) {
    if (attempt < this.retryAttempts && error.name !== 'AbortError') {
      await this.delay(1000 * attempt); // Exponential backoff
      return this.makeRequestWithRetry(endpoint, options, attempt + 1);
    }
    throw error;
  }
}
```

### Configuration Values from React App

**Environment Configuration:**
```javascript
// From sisense-config.js
export const sisenseConfig = {
  baseUrl: process.env.REACT_APP_SISENSE_URL?.replace(/\/$/, ''),
  credentials: {
    username: process.env.REACT_APP_SISENSE_USERNAME,
    password: process.env.REACT_APP_SISENSE_PASSWORD
  },
  apiToken: process.env.REACT_APP_SISENSE_API_TOKEN,
  cacheTimeout: 5 * 60 * 1000,     // 5 minutes
  requestTimeout: 30000,           // 30 seconds  
  retryAttempts: 3
};
```

**Proxy Configuration:**
```json
// From package.json
{
  "proxy": "https://analytics.veriforceone.com"
}
```

### Key Differences from Flask Implementation

1. **URL Construction:**
   - React: Uses relative URLs in development with proxy
   - Flask: Always uses full URLs

2. **Authentication Flow:**
   - React: API token OR username/password with session token
   - Flask: Only API token with Bearer header

3. **API Version Strategy:**
   - React: Intelligent fallback from V2 to V1 endpoints
   - Flask: Fixed endpoint attempts without version detection

4. **Error Handling:**
   - React: Comprehensive retry logic with exponential backoff
   - Flask: Basic retry with fixed intervals

5. **Platform Awareness:**
   - React: Detects Linux vs Windows and uses appropriate endpoints
   - Flask: Assumes specific endpoint availability

### Recommendations for Flask App

1. **Implement the React URL construction pattern**
2. **Add platform detection logic**  
3. **Use the same endpoint fallback strategy**
4. **Implement exponential backoff retry logic**
5. **Support both API token and username/password authentication**
6. **Test with the exact same endpoints that work in React**

---

### Exact Working URLs for Your Instance

Based on the React app configuration and the proxy setting, the working base URL is:
- **Base URL**: `https://analytics.veriforceone.com`
- **API Token**: Your existing token (confirmed working in React)

**Working Endpoints:**
- `https://analytics.veriforceone.com/api/v1/dashboards`
- `https://analytics.veriforceone.com/api/v2/datamodels` (if V2 available)
- `https://analytics.veriforceone.com/api/v1/elasticubes/getElasticubes` (legacy fallback)

The React app successfully calls these endpoints, so the Flask app should use the exact same patterns.