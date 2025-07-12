#!/usr/bin/env python3
"""
Endpoint Validation Demo

Demonstrates the endpoint validation system and generates sample documentation
based on known endpoint behavior from previous analysis.
"""

import json
from datetime import datetime


def generate_demo_validation_results():
    """Generate demo validation results based on known endpoint behavior."""
    
    # Based on our previous analysis, here are the known working/broken endpoints
    demo_results = {
        "validation_timestamp": datetime.now().isoformat(),
        "total_endpoints": 25,
        "successful": 5,
        "failed": 20,
        "success_rate": 20.0,
        "environment": {
            "base_url": "https://analytics.veriforceone.com",
            "platform": "linux",
            "deployment": "cloud"
        },
        "results": [
            # Working endpoints
            {
                "endpoint": "/api/v1/dashboards",
                "method": "GET",
                "status": "success",
                "status_code": 200,
                "response_time_ms": 1250.5,
                "response_size": 2048,
                "response_headers": {
                    "content-type": "application/json",
                    "server": "nginx/1.18.0"
                },
                "response_data": {
                    "type": "array",
                    "example": [
                        {
                            "oid": "dashboard-123",
                            "title": "Sales Dashboard",
                            "desc": "Sales performance metrics",
                            "owner": "user-456",
                            "created": "2024-01-15T10:30:00Z"
                        }
                    ]
                },
                "tested_at": datetime.now().isoformat()
            },
            {
                "endpoint": "/api/v2/connections",
                "method": "GET", 
                "status": "success",
                "status_code": 200,
                "response_time_ms": 890.2,
                "response_size": 1024,
                "response_headers": {
                    "content-type": "application/json"
                },
                "response_data": {
                    "type": "array",
                    "example": [
                        {
                            "id": "conn-789",
                            "title": "Production Database",
                            "provider": "postgresql"
                        }
                    ]
                },
                "tested_at": datetime.now().isoformat()
            },
            
            # Broken endpoints
            {
                "endpoint": "/api/v2/datamodels",
                "method": "GET",
                "status": "not_found",
                "status_code": 404,
                "response_time_ms": 150.0,
                "response_size": 85,
                "response_headers": {
                    "content-type": "application/json"
                },
                "response_data": {
                    "error": "Not Found"
                },
                "error_message": "Endpoint not found",
                "tested_at": datetime.now().isoformat()
            },
            {
                "endpoint": "/api/v1/elasticubes",
                "method": "GET",
                "status": "not_found", 
                "status_code": 404,
                "response_time_ms": 125.3,
                "response_size": 85,
                "response_headers": {
                    "content-type": "application/json"
                },
                "response_data": {
                    "error": "Not Found"
                },
                "error_message": "Endpoint not found",
                "tested_at": datetime.now().isoformat()
            },
            {
                "endpoint": "/api/v1/authentication/me",
                "method": "GET",
                "status": "not_found",
                "status_code": 404,
                "response_time_ms": 180.1,
                "response_size": 85,
                "response_headers": {
                    "content-type": "application/json"
                },
                "response_data": {
                    "error": "Not Found"
                },
                "error_message": "Endpoint not found",
                "tested_at": datetime.now().isoformat()
            },
            {
                "endpoint": "/api/v1/users/me",
                "method": "GET",
                "status": "failed",
                "status_code": 422,
                "response_time_ms": 95.7,
                "response_size": 120,
                "response_headers": {
                    "content-type": "application/json"
                },
                "response_data": {
                    "error": "Parameter (id) does not match required pattern"
                },
                "error_message": "Parameter validation error",
                "tested_at": datetime.now().isoformat()
            }
        ]
    }
    
    return demo_results


def generate_demo_health_results():
    """Generate demo health check results."""
    
    demo_health = {
        "overall_status": "degraded",
        "checked_at": datetime.now().isoformat(),
        "critical_endpoints": [
            "/api/v1/dashboards",
            "/api/v2/connections", 
            "/api/v1/authentication/me"
        ],
        "recent_results": {
            "/api/v1/dashboards": {
                "endpoint": "/api/v1/dashboards",
                "status": "healthy",
                "response_time_ms": 1250.5,
                "status_code": 200,
                "error_message": "",
                "checked_at": datetime.now().isoformat()
            },
            "/api/v2/connections": {
                "endpoint": "/api/v2/connections",
                "status": "healthy",
                "response_time_ms": 890.2,
                "status_code": 200,
                "error_message": "",
                "checked_at": datetime.now().isoformat()
            },
            "/api/v1/authentication/me": {
                "endpoint": "/api/v1/authentication/me",
                "status": "unhealthy",
                "response_time_ms": 180.1,
                "status_code": 404,
                "error_message": "Endpoint not found",
                "checked_at": datetime.now().isoformat()
            }
        },
        "metrics": {
            "/api/v1/dashboards": {
                "endpoint": "/api/v1/dashboards",
                "total_checks": 10,
                "successful_checks": 10,
                "average_response_time": 1180.5,
                "uptime_percentage": 100.0,
                "last_success": datetime.now().isoformat(),
                "consecutive_failures": 0
            },
            "/api/v2/connections": {
                "endpoint": "/api/v2/connections",
                "total_checks": 10,
                "successful_checks": 9,
                "average_response_time": 920.8,
                "uptime_percentage": 90.0,
                "last_success": datetime.now().isoformat(),
                "consecutive_failures": 0
            }
        },
        "environment": {
            "base_url": "https://analytics.veriforceone.com",
            "platform": "linux"
        }
    }
    
    return demo_health


def generate_demo_contract_results():
    """Generate demo contract test results."""
    
    demo_contracts = {
        "test_summary": {
            "total_contracts": 5,
            "passed": 2,
            "failed": 2,
            "warnings": 1,
            "skipped": 0,
            "success_rate": 40.0,
            "average_response_time_ms": 855.3
        },
        "test_timestamp": datetime.now().isoformat(),
        "environment": {
            "base_url": "https://analytics.veriforceone.com",
            "platform": "linux"
        },
        "detailed_results": {
            "dashboard_list": {
                "contract_name": "dashboard_list",
                "endpoint": "/api/v1/dashboards",
                "status": "pass",
                "errors": [],
                "warnings": [],
                "response_time_ms": 1250.5,
                "status_code": 200,
                "tested_at": datetime.now().isoformat()
            },
            "connections_v2": {
                "contract_name": "connections_v2",
                "endpoint": "/api/v2/connections",
                "status": "warning",
                "errors": [],
                "warnings": ["Response time 890ms exceeds recommended 500ms threshold"],
                "response_time_ms": 890.2,
                "status_code": 200,
                "tested_at": datetime.now().isoformat()
            },
            "auth_me": {
                "contract_name": "auth_me",
                "endpoint": "/api/v1/authentication/me",
                "status": "fail",
                "errors": ["Endpoint not found"],
                "warnings": [],
                "response_time_ms": 0,
                "status_code": 404,
                "tested_at": datetime.now().isoformat()
            }
        }
    }
    
    return demo_contracts


def generate_api_documentation():
    """Generate comprehensive API documentation."""
    
    validation_results = generate_demo_validation_results()
    
    doc = []
    doc.append("# Sisense API Endpoint Validation Results")
    doc.append(f"\nGenerated: {datetime.now().isoformat()}")
    doc.append(f"Base URL: {validation_results['environment']['base_url']}")
    doc.append(f"Platform: {validation_results['environment']['platform']}")
    doc.append(f"Deployment: {validation_results['environment']['deployment']}")
    
    # Summary
    doc.append("\n## Summary")
    doc.append(f"- **Total Endpoints Tested**: {validation_results['total_endpoints']}")
    doc.append(f"- **Working Endpoints**: {validation_results['successful']}")
    doc.append(f"- **Broken Endpoints**: {validation_results['failed']}")
    doc.append(f"- **Success Rate**: {validation_results['success_rate']:.1f}%")
    
    # Working endpoints
    working_endpoints = [r for r in validation_results['results'] if r['status'] == 'success']
    doc.append("\n## ✅ Working Endpoints")
    
    for endpoint in working_endpoints:
        doc.append(f"\n### {endpoint['method']} {endpoint['endpoint']}")
        doc.append(f"- **Status Code**: {endpoint['status_code']}")
        doc.append(f"- **Response Time**: {endpoint['response_time_ms']:.1f}ms")
        doc.append(f"- **Response Size**: {endpoint['response_size']} bytes")
        
        if 'response_data' in endpoint and 'example' in endpoint['response_data']:
            doc.append(f"- **Response Schema**: `{endpoint['response_data'].get('type', 'unknown')}`")
            example = endpoint['response_data']['example']
            if isinstance(example, list) and example:
                doc.append("- **Response Example**:")
                doc.append(f"  ```json")
                doc.append(f"  {json.dumps(example[0], indent=2)}")
                doc.append(f"  ```")
    
    # Broken endpoints
    broken_endpoints = [r for r in validation_results['results'] if r['status'] != 'success']
    doc.append("\n## ❌ Broken Endpoints")
    
    for endpoint in broken_endpoints:
        doc.append(f"\n### {endpoint['method']} {endpoint['endpoint']}")
        doc.append(f"- **Status**: {endpoint['status']}")
        doc.append(f"- **Status Code**: {endpoint['status_code']}")
        if 'error_message' in endpoint:
            doc.append(f"- **Error**: {endpoint['error_message']}")
    
    # Environment-specific recommendations
    doc.append("\n## 🔧 Environment-Specific Recommendations")
    doc.append("\nBased on the validation results for this Linux cloud deployment:")
    doc.append("\n1. **Working Core Functionality**:")
    doc.append("   - ✅ Dashboard listing via `/api/v1/dashboards`")
    doc.append("   - ✅ Connection management via `/api/v2/connections`")
    doc.append("\n2. **Authentication Issues**:")
    doc.append("   - ❌ `/api/v1/authentication/me` not available")
    doc.append("   - ❌ `/api/v1/users/me` parameter validation issues")
    doc.append("   - 💡 Consider using `/api/v1/dashboards` for auth validation")
    doc.append("\n3. **Data Model Access**:")
    doc.append("   - ❌ `/api/v2/datamodels` not available")
    doc.append("   - ❌ `/api/v1/elasticubes` not available")
    doc.append("   - 💡 This deployment may use different data model endpoints")
    doc.append("\n4. **Platform Optimization**:")
    doc.append("   - ✅ V2 connections API is available and working")
    doc.append("   - ⚠️  V1 APIs are primary working pattern")
    doc.append("   - 🔧 Configure `SISENSE_PLATFORM_OVERRIDE=linux` for optimization")
    
    # Usage recommendations
    doc.append("\n## 📋 Usage Recommendations")
    doc.append("\n### Reliable Endpoints (Safe to Use)")
    doc.append("```python")
    doc.append("# Core dashboard functionality")
    doc.append("dashboards = client.get('/api/v1/dashboards')")
    doc.append("")
    doc.append("# Connection management") 
    doc.append("connections = client.get('/api/v2/connections')")
    doc.append("```")
    doc.append("\n### Endpoints to Avoid")
    doc.append("```python")
    doc.append("# These endpoints return 404 in this environment")
    doc.append("# client.get('/api/v2/datamodels')  # 404")
    doc.append("# client.get('/api/v1/elasticubes')  # 404")
    doc.append("# client.get('/api/v1/authentication/me')  # 404")
    doc.append("```")
    doc.append("\n### Environment Configuration")
    doc.append("```bash")
    doc.append("# Optimize for this environment")
    doc.append("SISENSE_PLATFORM_OVERRIDE=linux")
    doc.append("SISENSE_API_VERSION_OVERRIDE=auto")
    doc.append("SISENSE_DISABLE_LIVE_FEATURES=false")
    doc.append("```")
    
    return "\n".join(doc)


def main():
    """Generate demo validation results and documentation."""
    print("📊 Sisense API Endpoint Validation Demo")
    print("=" * 50)
    print("This demo shows what the endpoint validation system would produce")
    print("when run against a live Sisense instance.")
    
    # Generate demo results
    validation_results = generate_demo_validation_results()
    health_results = generate_demo_health_results()
    contract_results = generate_demo_contract_results()
    
    # Save demo results
    with open("demo_endpoint_validation_results.json", 'w') as f:
        json.dump(validation_results, f, indent=2)
    
    with open("demo_health_check_results.json", 'w') as f:
        json.dump(health_results, f, indent=2)
    
    with open("demo_contract_test_results.json", 'w') as f:
        json.dump(contract_results, f, indent=2)
    
    # Generate comprehensive report
    comprehensive_report = {
        "validation_timestamp": datetime.now().isoformat(),
        "demo_mode": True,
        "environment": {
            "base_url": "https://analytics.veriforceone.com",
            "platform": "linux",
            "deployment": "cloud"
        },
        "endpoint_validation": validation_results,
        "health_checks": health_results,
        "contract_testing": contract_results,
        "summary": {
            "endpoints_working": validation_results['successful'],
            "endpoints_total": validation_results['total_endpoints'],
            "health_status": health_results['overall_status'],
            "contract_success_rate": contract_results['test_summary']['success_rate']
        }
    }
    
    with open("demo_comprehensive_api_validation.json", 'w') as f:
        json.dump(comprehensive_report, f, indent=2)
    
    # Generate API documentation
    api_docs = generate_api_documentation()
    with open("DEMO_API_ENDPOINTS.md", 'w') as f:
        f.write(api_docs)
    
    # Print summary
    print(f"\n📊 Demo Validation Results:")
    print(f"✅ Working Endpoints: {validation_results['successful']}")
    print(f"❌ Broken Endpoints: {validation_results['failed']}")
    print(f"📈 Success Rate: {validation_results['success_rate']:.1f}%")
    print(f"💚 Health Status: {health_results['overall_status'].upper()}")
    print(f"📋 Contract Success Rate: {contract_results['test_summary']['success_rate']:.1f}%")
    
    print(f"\n📁 Demo Files Generated:")
    print(f"- demo_endpoint_validation_results.json")
    print(f"- demo_health_check_results.json") 
    print(f"- demo_contract_test_results.json")
    print(f"- demo_comprehensive_api_validation.json")
    print(f"- DEMO_API_ENDPOINTS.md")
    
    print(f"\n🎯 Key Findings (Based on Previous Analysis):")
    print(f"- Dashboard endpoints (/api/v1/dashboards) are working reliably")
    print(f"- Connection endpoints (/api/v2/connections) are available")
    print(f"- Authentication endpoints are problematic (404/422 errors)")
    print(f"- Data model endpoints are not available in this deployment")
    print(f"- Platform appears to be Linux with V2 API partial support")
    
    print(f"\n💡 Recommendations:")
    print(f"- Use /api/v1/dashboards for core functionality")
    print(f"- Use /api/v2/connections for connection management")
    print(f"- Avoid authentication/me endpoints (use alternative validation)")
    print(f"- Configure environment-specific overrides for optimization")


if __name__ == "__main__":
    main()