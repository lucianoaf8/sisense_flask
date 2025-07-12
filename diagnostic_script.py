#!/usr/bin/env python3
"""
Sisense API Diagnostic Script
Run this to understand exactly what's failing and why
"""

import os
import sys
import requests
import json
from urllib.parse import urljoin

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def load_env():
    """Load environment variables from .env file"""
    env_file = '.env'
    if not os.path.exists(env_file):
        print("❌ No .env file found!")
        print("Create .env file with:")
        print("SISENSE_URL=https://your-sisense-url.com")
        print("SISENSE_API_TOKEN=your_token_here")
        return None, None
        
    env_vars = {}
    with open(env_file, 'r') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                env_vars[key] = value
                
    base_url = env_vars.get('SISENSE_URL', '').rstrip('/')
    api_token = env_vars.get('SISENSE_API_TOKEN', '')
    
    if not base_url:
        print("❌ SISENSE_URL not found in .env")
        return None, None
        
    if not api_token:
        print("❌ SISENSE_API_TOKEN not found in .env")
        return None, None
        
    return base_url, api_token

def test_connection(base_url, api_token):
    """Test basic connectivity and authentication"""
    print(f"\n🔍 Testing connection to: {base_url}")
    
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    # Test endpoints in order of likelihood to work
    test_endpoints = [
        '/api/v1/dashboards',
        '/api/v2/connections', 
        '/api/v2/datamodels',
        '/api/v1/elasticubes',
        '/api/datamodels',
        '/api/v1/datasources',
        '/api/v1/authentication/me',
        '/api/v1/users/me'
    ]
    
    results = {}
    
    for endpoint in test_endpoints:
        url = urljoin(base_url + '/', endpoint.lstrip('/'))
        print(f"\n📡 Testing: {endpoint}")
        
        try:
            response = requests.get(
                url, 
                headers=headers, 
                timeout=10,
                verify=True  # Change to False if SSL issues
            )
            
            status = response.status_code
            
            if status == 200:
                try:
                    data = response.json()
                    count = len(data) if isinstance(data, list) else len(data.get('data', [])) if isinstance(data, dict) else 'unknown'
                    print(f"✅ {endpoint} → {status} ({count} items)")
                    results[endpoint] = {'status': status, 'success': True, 'data': data}
                except:
                    print(f"✅ {endpoint} → {status} (non-JSON response)")
                    results[endpoint] = {'status': status, 'success': True, 'data': 'non-json'}
            elif status == 401:
                print(f"🔑 {endpoint} → {status} (Authentication Failed)")
                results[endpoint] = {'status': status, 'success': False, 'error': 'auth_failed'}
            elif status == 403:
                print(f"🚫 {endpoint} → {status} (Access Denied)")
                results[endpoint] = {'status': status, 'success': False, 'error': 'access_denied'}
            elif status == 404:
                print(f"❌ {endpoint} → {status} (Not Found)")
                results[endpoint] = {'status': status, 'success': False, 'error': 'not_found'}
            elif status == 422:
                print(f"⚠️  {endpoint} → {status} (Validation Error)")
                results[endpoint] = {'status': status, 'success': False, 'error': 'validation_error'}
            else:
                print(f"⚠️  {endpoint} → {status} ({response.reason})")
                results[endpoint] = {'status': status, 'success': False, 'error': response.reason}
                
        except requests.exceptions.ConnectionError:
            print(f"🔌 {endpoint} → Connection Error (Check URL)")
            results[endpoint] = {'status': 'connection_error', 'success': False, 'error': 'connection_failed'}
        except requests.exceptions.SSLError:
            print(f"🔒 {endpoint} → SSL Error (Try verify=False)")
            results[endpoint] = {'status': 'ssl_error', 'success': False, 'error': 'ssl_failed'}
        except requests.exceptions.Timeout:
            print(f"⏰ {endpoint} → Timeout")
            results[endpoint] = {'status': 'timeout', 'success': False, 'error': 'timeout'}
        except Exception as e:
            print(f"💥 {endpoint} → Error: {e}")
            results[endpoint] = {'status': 'error', 'success': False, 'error': str(e)}
    
    return results

def analyze_results(results):
    """Analyze test results and provide recommendations"""
    print("\n" + "="*60)
    print("📊 DIAGNOSTIC ANALYSIS")
    print("="*60)
    
    working_endpoints = [ep for ep, result in results.items() if result['success']]
    failing_endpoints = [ep for ep, result in results.items() if not result['success']]
    
    print(f"\n✅ Working endpoints ({len(working_endpoints)}):")
    for endpoint in working_endpoints:
        result = results[endpoint]
        print(f"   • {endpoint} → {result['status']}")
    
    print(f"\n❌ Failing endpoints ({len(failing_endpoints)}):")
    error_groups = {}
    for endpoint in failing_endpoints:
        result = results[endpoint]
        error = result.get('error', 'unknown')
        if error not in error_groups:
            error_groups[error] = []
        error_groups[error].append(endpoint)
    
    for error, endpoints in error_groups.items():
        print(f"\n   {error.upper()}:")
        for endpoint in endpoints:
            status = results[endpoint]['status']
            print(f"     • {endpoint} → {status}")
    
    # Provide specific recommendations
    print(f"\n🎯 RECOMMENDATIONS:")
    
    if not working_endpoints:
        print("   🚨 CRITICAL: No endpoints working!")
        print("   1. Verify SISENSE_URL is correct")
        print("   2. Verify SISENSE_API_TOKEN is valid")
        print("   3. Check network connectivity")
        print("   4. Try with verify=False if SSL issues")
    else:
        print(f"   ✅ Good news: {len(working_endpoints)} endpoints working")
        
        if '/api/v1/dashboards' in working_endpoints:
            print("   • Dashboards API working - authentication is OK")
            
        if '/api/v2/connections' in working_endpoints:
            print("   • Connections API working - v2 endpoints available")
            
        if '/api/v2/datamodels' not in working_endpoints:
            if '/api/v1/elasticubes' in working_endpoints:
                print("   • Use /api/v1/elasticubes instead of /api/v2/datamodels")
            else:
                print("   ⚠️  No data model endpoint working - check Sisense version")
    
    # Authentication analysis
    auth_failures = [ep for ep, result in results.items() 
                    if result.get('error') == 'auth_failed']
    if auth_failures:
        print(f"\n🔑 Authentication issues detected:")
        print("   • Check your API token is valid")
        print("   • Verify token has required permissions")
        
    # Version analysis
    if '/api/v2/datamodels' not in working_endpoints and '/api/v1/elasticubes' in working_endpoints:
        print(f"\n📋 Your Sisense appears to be older version:")
        print("   • Update datamodels.py to use /api/v1/elasticubes")
        print("   • Some v2 endpoints may not be available")

def main():
    """Main diagnostic function"""
    print("🔧 Sisense API Diagnostic Tool")
    print("="*50)
    
    # Load configuration
    base_url, api_token = load_env()
    if not base_url or not api_token:
        return
        
    print(f"🔗 Base URL: {base_url}")
    print(f"🔑 Token: {api_token[:10]}...{api_token[-5:] if len(api_token) > 15 else api_token}")
    
    # Test endpoints
    results = test_connection(base_url, api_token)
    
    # Analyze and provide recommendations
    analyze_results(results)
    
    # Save results for reference
    with open('diagnostic_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 Results saved to diagnostic_results.json")
    
    print(f"\n🎯 NEXT STEPS:")
    print("1. Fix any critical authentication issues")
    print("2. Update your code to use only working endpoints")  
    print("3. Remove fallback logic for non-working endpoints")
    print("4. Run your application tests again")

if __name__ == '__main__':
    main()