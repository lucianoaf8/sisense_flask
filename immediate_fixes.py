# IMMEDIATE FIXES - Start Here
# Run these commands and make these changes to get your API working

# =============================================================================
# 1. FIRST - Test your current setup manually
# =============================================================================

# Test authentication with your current token
curl -H "Authorization: Bearer YOUR_ACTUAL_TOKEN" \
     -H "Content-Type: application/json" \
     "https://YOUR_SISENSE_URL/api/v1/dashboards"

# Test datamodels endpoint (this might be your main issue)  
curl -H "Authorization: Bearer YOUR_ACTUAL_TOKEN" \
     "https://YOUR_SISENSE_URL/api/v2/datamodels"

# If datamodels fails, try alternatives:
curl -H "Authorization: Bearer YOUR_ACTUAL_TOKEN" \
     "https://YOUR_SISENSE_URL/api/v1/elasticubes"

# =============================================================================
# 2. CRITICAL FIX - sisense/auth.py - Simplify authentication
# =============================================================================

"""
Replace the entire auth.py with this simplified version:
"""

import logging
import requests
from typing import Dict
from config import Config
from sisense.utils import SisenseAPIError

logger = logging.getLogger(__name__)

def get_auth_headers() -> Dict[str, str]:
    """Get authentication headers with API token."""
    if Config.DEMO_MODE:
        return {"Authorization": "Bearer demo-token", "Content-Type": "application/json"}
    
    if not Config.SISENSE_API_TOKEN:
        raise SisenseAPIError("SISENSE_API_TOKEN is not configured")
    
    return {
        'Authorization': f'Bearer {Config.SISENSE_API_TOKEN}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

def validate_authentication() -> bool:
    """Validate authentication using working endpoint."""
    try:
        headers = get_auth_headers()
        base_url = Config.get_sisense_base_url()
        
        # Use the one endpoint we know works
        response = requests.get(
            f"{base_url}/api/v1/dashboards",
            headers=headers,
            timeout=Config.REQUEST_TIMEOUT,
            verify=Config.SSL_VERIFY
        )
        
        return response.status_code == 200
        
    except Exception as e:
        logger.error(f"Authentication validation failed: {e}")
        return False

# =============================================================================
# 3. CRITICAL FIX - sisense/datamodels.py - Fix endpoints
# =============================================================================

"""
Replace the datamodels.py endpoint URLs with these corrections:
"""

def list_datamodels(model_type: str = None) -> List[Dict]:
    """List all data models - FIXED ENDPOINT"""
    try:
        # CORRECT endpoint per documentation
        endpoint = '/api/v2/datamodels'
        headers = get_auth_headers()
        
        params = {}
        if model_type:
            params['type'] = model_type
            
        response = http_client.get(endpoint, headers=headers, params=params)
        
        if response.status_code == 404:
            # If v2 doesn't work, try the alternative documented endpoint
            endpoint = '/api/v1/elasticubes'
            response = http_client.get(endpoint, headers=headers, params=params)
            
        if response.status_code != 200:
            raise SisenseAPIError(f"Failed to list datamodels: {response.status_code}")
            
        return response.json()
        
    except Exception as e:
        logger.error(f"Error listing datamodels: {e}")
        raise

def get_datamodel(model_oid: str) -> Dict:
    """Get specific data model - FIXED ENDPOINT"""
    try:
        # CORRECT endpoint per documentation  
        endpoint = f'/api/v2/datamodels/{model_oid}'
        headers = get_auth_headers()
        
        response = http_client.get(endpoint, headers=headers)
        
        if response.status_code == 404:
            # Try alternative if v2 fails
            endpoint = f'/api/v1/elasticubes/{model_oid}'
            response = http_client.get(endpoint, headers=headers)
            
        if response.status_code != 200:
            raise SisenseAPIError(f"Failed to get datamodel {model_oid}: {response.status_code}")
            
        return response.json()
        
    except Exception as e:
        logger.error(f"Error getting datamodel {model_oid}: {e}")
        raise

def export_schema(model_oid: str = None, **kwargs) -> Dict:
    """Export data model schema - FIXED ENDPOINT"""
    try:
        # CORRECT endpoint per documentation
        endpoint = '/api/v2/datamodel-exports/schema'
        headers = get_auth_headers()
        
        params = {}
        if model_oid:
            params['datamodelId'] = model_oid  # CORRECT parameter name
            
        response = http_client.get(endpoint, headers=headers, params=params)
        
        if response.status_code != 200:
            raise SisenseAPIError(f"Failed to export schema: {response.status_code}")
            
        return response.json()
        
    except Exception as e:
        logger.error(f"Error exporting schema: {e}")
        raise

# =============================================================================
# 4. CRITICAL FIX - sisense/sql.py - Fix datasource endpoints
# =============================================================================

def execute_sql(datasource: str, query: str, **kwargs) -> Dict:
    """Execute SQL query - FIXED ENDPOINT"""
    try:
        # CORRECT endpoint per documentation
        endpoint = f'/api/v1/datasources/{datasource}/sql'
        headers = get_auth_headers()
        
        # CORRECT payload structure per documentation
        payload = {
            "query": query,
            "limit": kwargs.get('limit', 1000),
            "offset": kwargs.get('offset', 0),
            "timeout": kwargs.get('timeout', 30)
        }
        
        response = http_client.post(endpoint, headers=headers, json=payload)
        
        if response.status_code != 200:
            raise SisenseAPIError(f"SQL query failed: {response.status_code}")
            
        return response.json()
        
    except Exception as e:
        logger.error(f"Error executing SQL: {e}")
        raise

# =============================================================================
# 5. CRITICAL FIX - sisense/jaql.py - Fix JAQL endpoints  
# =============================================================================

def execute_jaql(datasource: str, jaql_query: Dict, **kwargs) -> Dict:
    """Execute JAQL query - FIXED ENDPOINT"""
    try:
        # CORRECT endpoint per documentation
        endpoint = f'/api/v1/datasources/{datasource}/jaql'
        headers = get_auth_headers()
        
        # CORRECT payload structure per documentation
        payload = {
            "jaql": jaql_query,
            "format": kwargs.get('format', 'json'),
            "timeout": kwargs.get('timeout', 30)
        }
        
        response = http_client.post(endpoint, headers=headers, json=payload)
        
        if response.status_code != 200:
            raise SisenseAPIError(f"JAQL query failed: {response.status_code}")
            
        return response.json()
        
    except Exception as e:
        logger.error(f"Error executing JAQL: {e}")
        raise

def get_jaql_metadata(datasource: str) -> Dict:
    """Get JAQL metadata - FIXED ENDPOINT"""
    try:
        # CORRECT endpoint per documentation
        endpoint = f'/api/v1/datasources/{datasource}/jaql/metadata'
        headers = get_auth_headers()
        
        response = http_client.get(endpoint, headers=headers)
        
        if response.status_code != 200:
            raise SisenseAPIError(f"Failed to get JAQL metadata: {response.status_code}")
            
        return response.json()
        
    except Exception as e:
        logger.error(f"Error getting JAQL metadata: {e}")
        raise

# =============================================================================
# 6. IMMEDIATE TEST SCRIPT - Run this to validate fixes
# =============================================================================

"""
Create this as test_immediate_fixes.py and run it:
"""

import sys
sys.path.append('.')

from sisense.auth import validate_authentication, get_auth_headers
from sisense.datamodels import list_datamodels
from sisense.dashboards import list_dashboards
from sisense.connections import list_connections

def test_authentication():
    """Test if authentication works"""
    print("Testing authentication...")
    try:
        if validate_authentication():
            print("✅ Authentication successful")
            return True
        else:
            print("❌ Authentication failed")
            return False
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return False

def test_endpoints():
    """Test each major endpoint"""
    results = {}
    
    # Test dashboards (should work)
    try:
        dashboards = list_dashboards()
        print(f"✅ Dashboards: Found {len(dashboards)} dashboards")
        results['dashboards'] = True
    except Exception as e:
        print(f"❌ Dashboards failed: {e}")
        results['dashboards'] = False
    
    # Test connections (should work)  
    try:
        connections = list_connections()
        print(f"✅ Connections: Found {len(connections)} connections")
        results['connections'] = True
    except Exception as e:
        print(f"❌ Connections failed: {e}")
        results['connections'] = False
        
    # Test datamodels (main issue)
    try:
        models = list_datamodels()
        print(f"✅ Data Models: Found {len(models)} models")
        results['datamodels'] = True
    except Exception as e:
        print(f"❌ Data Models failed: {e}")
        results['datamodels'] = False
        
    return results

if __name__ == '__main__':
    print("🔧 Testing immediate fixes...")
    print("=" * 50)
    
    # Test auth first
    if not test_authentication():
        print("Fix authentication first!")
        sys.exit(1)
        
    # Test endpoints
    results = test_endpoints()
    
    print("\n📊 Results Summary:")
    for endpoint, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {endpoint}")
        
    if all(results.values()):
        print("\n🎉 All endpoints working!")
    else:
        print("\n⚠️  Some endpoints still need fixes")

# =============================================================================
# 7. ENVIRONMENT VALIDATION - Check your .env file
# =============================================================================

"""
Ensure your .env file has these exact settings:
"""

# Required
SISENSE_URL=https://your-sisense-url.com
SISENSE_API_TOKEN=your_actual_api_token_here

# Optional but recommended
SISENSE_SSL_VERIFY=True
SISENSE_REQUEST_TIMEOUT=30
SISENSE_REQUEST_RETRIES=3

# =============================================================================
# 8. DELETE/RENAME CONFLICTING FILES
# =============================================================================

# Move enhanced_auth.py out of the way
# mv sisense/enhanced_auth.py sisense/enhanced_auth.py.backup

# Comment out any imports of enhanced_auth in other files

# =============================================================================
# 9. VALIDATION COMMANDS
# =============================================================================

# After making changes, run:
python test_immediate_fixes.py

# Then test the Flask app:
python app.py

# Test specific endpoints in browser:
# http://localhost:5000/api/datamodels
# http://localhost:5000/api/dashboards  
# http://localhost:5000/api/connections