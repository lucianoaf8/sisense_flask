#!/usr/bin/env python3
"""
Endpoint Validation Utility for Sisense API Integration.

Systematically tests all API endpoints to validate functionality,
documents working endpoints, and generates comprehensive API mapping.
"""

import json
import logging
import re
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple
from enum import Enum
import requests
from pathlib import Path

# Import our configuration and utilities
from sisense.config import Config
from sisense.env_config import get_environment_config
from sisense.auth import get_auth_headers


class EndpointStatus(Enum):
    """Endpoint validation status."""
    SUCCESS = "success"
    FAILED = "failed"
    AUTH_ERROR = "auth_error"
    NOT_FOUND = "not_found"
    METHOD_NOT_ALLOWED = "method_not_allowed"
    SERVER_ERROR = "server_error"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class HTTPMethod(Enum):
    """Supported HTTP methods."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


@dataclass
class EndpointTest:
    """Configuration for testing an endpoint."""
    path: str
    method: HTTPMethod = HTTPMethod.GET
    description: str = ""
    requires_auth: bool = True
    test_params: Dict[str, Any] = None
    test_data: Dict[str, Any] = None
    expected_status: List[int] = None
    tags: List[str] = None

    def __post_init__(self):
        if self.test_params is None:
            self.test_params = {}
        if self.test_data is None:
            self.test_data = {}
        if self.expected_status is None:
            self.expected_status = [200]
        if self.tags is None:
            self.tags = []


@dataclass
class ValidationResult:
    """Result of endpoint validation."""
    endpoint: str
    method: str
    status: EndpointStatus
    status_code: int
    response_time_ms: float
    response_size: int
    response_headers: Dict[str, str]
    response_data: Dict[str, Any]
    error_message: str = ""
    tested_at: str = ""
    
    def __post_init__(self):
        if not self.tested_at:
            self.tested_at = datetime.now().isoformat()


class SisenseEndpointValidator:
    """
    Comprehensive endpoint validation utility for Sisense API.
    
    Tests all known endpoints, validates responses, and generates
    comprehensive documentation of the working API surface area.
    """

    def __init__(self):
        """Initialize the endpoint validator."""
        self.logger = logging.getLogger(__name__)
        self.env_config = get_environment_config()
        self.base_url = Config.get_sisense_base_url()
        self.results: List[ValidationResult] = []
        
        # Validation configuration
        self.timeout = 30
        self.max_response_size = 10 * 1024 * 1024  # 10MB
        self.rate_limit_delay = 0.5  # 500ms between requests
        
        # Test endpoint definitions
        self.endpoint_tests = self._define_endpoint_tests()
        
        self.logger.info(f"Initialized endpoint validator for {self.base_url}")

    def _define_endpoint_tests(self) -> List[EndpointTest]:
        """Define all endpoints to test."""
        tests = []
        
        # Authentication endpoints
        tests.extend([
            EndpointTest(
                path="/api/v1/authentication/me",
                description="Get current user information",
                tags=["authentication", "user", "v1"]
            ),
            EndpointTest(
                path="/api/v1/authentication",
                description="Authentication status",
                tags=["authentication", "v1"]
            ),
            EndpointTest(
                path="/api/v1/users/me",
                description="Get current user details",
                tags=["authentication", "user", "v1"]
            ),
            EndpointTest(
                path="/api/users/me",
                description="Get current user (legacy)",
                tags=["authentication", "user", "legacy"]
            ),
        ])
        
        # Dashboard endpoints
        tests.extend([
            EndpointTest(
                path="/api/v1/dashboards",
                description="List all dashboards",
                tags=["dashboards", "v1", "core"]
            ),
            EndpointTest(
                path="/api/dashboards",
                description="List dashboards (legacy)",
                tags=["dashboards", "legacy"]
            ),
        ])
        
        # Data model endpoints
        tests.extend([
            EndpointTest(
                path="/api/v2/datamodels",
                description="List data models (V2)",
                tags=["datamodels", "v2", "modern"]
            ),
            EndpointTest(
                path="/api/v1/elasticubes",
                description="List ElastiCubes (V1)",
                tags=["datamodels", "elasticubes", "v1"]
            ),
            EndpointTest(
                path="/api/elasticubes",
                description="List ElastiCubes (legacy)",
                tags=["datamodels", "elasticubes", "legacy"]
            ),
            EndpointTest(
                path="/api/v1/elasticubes/getElasticubes",
                description="Get ElastiCubes (Windows pattern)",
                tags=["datamodels", "elasticubes", "v1", "windows"]
            ),
        ])
        
        # Connection endpoints
        tests.extend([
            EndpointTest(
                path="/api/v2/connections",
                description="List connections (V2)",
                tags=["connections", "v2", "modern"]
            ),
            EndpointTest(
                path="/api/v1/connection",
                description="List connections (V1)",
                tags=["connections", "v1"]
            ),
            EndpointTest(
                path="/api/connection",
                description="List connections (legacy)",
                tags=["connections", "legacy"]
            ),
        ])
        
        # Widget endpoints
        tests.extend([
            EndpointTest(
                path="/api/v1/widgets",
                description="List widgets",
                tags=["widgets", "v1"]
            ),
            EndpointTest(
                path="/api/widgets",
                description="List widgets (legacy)",
                tags=["widgets", "legacy"]
            ),
        ])
        
        # System/version endpoints
        tests.extend([
            EndpointTest(
                path="/api/version",
                description="Get system version",
                tags=["system", "version"],
                requires_auth=False
            ),
            EndpointTest(
                path="/api/v1/version",
                description="Get system version (V1)",
                tags=["system", "version", "v1"],
                requires_auth=False
            ),
            EndpointTest(
                path="/api/v2/version",
                description="Get system version (V2)",
                tags=["system", "version", "v2"],
                requires_auth=False
            ),
            EndpointTest(
                path="/api/build-info",
                description="Get build information",
                tags=["system", "build"],
                requires_auth=False
            ),
        ])
        
        # Health check endpoints
        tests.extend([
            EndpointTest(
                path="/api/health",
                description="System health check",
                tags=["health", "monitoring"],
                requires_auth=False
            ),
            EndpointTest(
                path="/api/v1/health",
                description="System health check (V1)",
                tags=["health", "monitoring", "v1"],
                requires_auth=False
            ),
            EndpointTest(
                path="/ping",
                description="Simple ping endpoint",
                tags=["health", "ping"],
                requires_auth=False
            ),
        ])
        
        return tests

    def validate_endpoint(self, test: EndpointTest) -> ValidationResult:
        """
        Validate a single endpoint.
        
        Args:
            test: Endpoint test configuration.
            
        Returns:
            ValidationResult: Validation result with details.
        """
        url = f"{self.base_url}{test.path}"
        
        # Prepare headers
        headers = {'Content-Type': 'application/json'}
        if test.requires_auth:
            try:
                auth_headers = get_auth_headers()
                headers.update(auth_headers)
            except Exception as e:
                return ValidationResult(
                    endpoint=test.path,
                    method=test.method.value,
                    status=EndpointStatus.AUTH_ERROR,
                    status_code=0,
                    response_time_ms=0,
                    response_size=0,
                    response_headers={},
                    response_data={},
                    error_message=f"Authentication failed: {str(e)}"
                )
        
        # Add environment-specific headers
        env_headers = self.env_config.get_platform_headers()
        headers.update(env_headers)
        
        self.logger.debug(f"Testing {test.method.value} {url}")
        
        start_time = time.time()
        
        try:
            # Make the request
            response = requests.request(
                method=test.method.value,
                url=url,
                headers=headers,
                params=test.test_params,
                json=test.test_data if test.test_data else None,
                timeout=self.timeout,
                verify=Config.SSL_VERIFY
            )
            
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            
            # Process response
            response_size = len(response.content)
            response_headers = dict(response.headers)
            
            # Parse response data
            try:
                if response.content:
                    response_data = response.json()
                else:
                    response_data = {}
            except json.JSONDecodeError:
                response_data = {
                    "raw_content": response.text[:1000],  # First 1000 chars
                    "content_type": response.headers.get('content-type', 'unknown')
                }
            
            # Determine status
            if response.status_code in test.expected_status:
                status = EndpointStatus.SUCCESS
                error_message = ""
            elif response.status_code == 401:
                status = EndpointStatus.AUTH_ERROR
                error_message = "Unauthorized - check API token"
            elif response.status_code == 404:
                status = EndpointStatus.NOT_FOUND
                error_message = "Endpoint not found"
            elif response.status_code == 405:
                status = EndpointStatus.METHOD_NOT_ALLOWED
                error_message = f"Method {test.method.value} not allowed"
            elif response.status_code >= 500:
                status = EndpointStatus.SERVER_ERROR
                error_message = f"Server error: {response.status_code}"
            else:
                status = EndpointStatus.FAILED
                error_message = f"Unexpected status: {response.status_code}"
            
            return ValidationResult(
                endpoint=test.path,
                method=test.method.value,
                status=status,
                status_code=response.status_code,
                response_time_ms=response_time_ms,
                response_size=response_size,
                response_headers=response_headers,
                response_data=response_data,
                error_message=error_message
            )
            
        except requests.exceptions.Timeout:
            return ValidationResult(
                endpoint=test.path,
                method=test.method.value,
                status=EndpointStatus.TIMEOUT,
                status_code=0,
                response_time_ms=self.timeout * 1000,
                response_size=0,
                response_headers={},
                response_data={},
                error_message=f"Request timeout after {self.timeout}s"
            )
            
        except requests.exceptions.RequestException as e:
            return ValidationResult(
                endpoint=test.path,
                method=test.method.value,
                status=EndpointStatus.FAILED,
                status_code=0,
                response_time_ms=0,
                response_size=0,
                response_headers={},
                response_data={},
                error_message=f"Request failed: {str(e)}"
            )

    def validate_all_endpoints(self) -> Dict[str, Any]:
        """
        Validate all defined endpoints.
        
        Returns:
            Dict: Comprehensive validation results.
        """
        self.logger.info(f"Starting validation of {len(self.endpoint_tests)} endpoints")
        
        self.results = []
        successful = 0
        failed = 0
        
        for i, test in enumerate(self.endpoint_tests, 1):
            self.logger.info(f"Testing endpoint {i}/{len(self.endpoint_tests)}: {test.path}")
            
            result = self.validate_endpoint(test)
            self.results.append(result)
            
            if result.status == EndpointStatus.SUCCESS:
                successful += 1
                self.logger.info(f"✅ {test.path} - {result.status_code} ({result.response_time_ms:.1f}ms)")
            else:
                failed += 1
                self.logger.warning(f"❌ {test.path} - {result.status.value}: {result.error_message}")
            
            # Rate limiting
            if i < len(self.endpoint_tests):
                time.sleep(self.rate_limit_delay)
        
        # Generate summary
        summary = {
            "validation_timestamp": datetime.now().isoformat(),
            "total_endpoints": len(self.endpoint_tests),
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / len(self.endpoint_tests)) * 100,
            "environment": {
                "base_url": self.base_url,
                "platform": self.env_config.detect_platform_capabilities().platform.value,
                "deployment": self.env_config.detect_platform_capabilities().deployment.value,
            },
            "results": [asdict(result) for result in self.results]
        }
        
        self.logger.info(f"Validation complete: {successful}/{len(self.endpoint_tests)} endpoints working ({summary['success_rate']:.1f}%)")
        
        return summary

    def generate_endpoint_mapping(self) -> Dict[str, Any]:
        """Generate mapping of working vs non-working endpoints."""
        if not self.results:
            raise ValueError("No validation results available. Run validate_all_endpoints() first.")
        
        working_endpoints = []
        broken_endpoints = []
        auth_issues = []
        
        for result in self.results:
            endpoint_info = {
                "path": result.endpoint,
                "method": result.method,
                "status_code": result.status_code,
                "response_time_ms": result.response_time_ms,
                "response_size": result.response_size,
                "tested_at": result.tested_at
            }
            
            if result.status == EndpointStatus.SUCCESS:
                endpoint_info["response_schema"] = self._analyze_response_schema(result.response_data)
                working_endpoints.append(endpoint_info)
            elif result.status == EndpointStatus.AUTH_ERROR:
                endpoint_info["error"] = result.error_message
                auth_issues.append(endpoint_info)
            else:
                endpoint_info["error"] = result.error_message
                endpoint_info["status"] = result.status.value
                broken_endpoints.append(endpoint_info)
        
        return {
            "working_endpoints": working_endpoints,
            "broken_endpoints": broken_endpoints,
            "auth_issues": auth_issues,
            "summary": {
                "total": len(self.results),
                "working": len(working_endpoints),
                "broken": len(broken_endpoints),
                "auth_issues": len(auth_issues)
            }
        }

    def _analyze_response_schema(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze response data to generate schema information."""
        def analyze_value(value):
            if isinstance(value, dict):
                return {
                    "type": "object",
                    "properties": {k: analyze_value(v) for k, v in value.items()},
                    "example": value
                }
            elif isinstance(value, list):
                if value:
                    return {
                        "type": "array",
                        "items": analyze_value(value[0]),
                        "example": value[:3]  # First 3 items as example
                    }
                else:
                    return {"type": "array", "items": {"type": "unknown"}, "example": []}
            elif isinstance(value, str):
                return {"type": "string", "example": value}
            elif isinstance(value, int):
                return {"type": "integer", "example": value}
            elif isinstance(value, float):
                return {"type": "number", "example": value}
            elif isinstance(value, bool):
                return {"type": "boolean", "example": value}
            elif value is None:
                return {"type": "null", "example": None}
            else:
                return {"type": "unknown", "example": str(value)}
        
        return analyze_value(response_data)

    def save_validation_results(self, filename: str = "endpoint_validation_results.json"):
        """Save validation results to JSON file."""
        if not self.results:
            raise ValueError("No validation results to save")
        
        summary = self.validate_all_endpoints() if not hasattr(self, '_last_summary') else self._last_summary
        
        with open(filename, 'w') as f:
            json.dump(summary, f, indent=2)
        
        self.logger.info(f"Validation results saved to {filename}")

    def generate_api_documentation(self) -> str:
        """Generate comprehensive API documentation."""
        if not self.results:
            raise ValueError("No validation results available")
        
        mapping = self.generate_endpoint_mapping()
        
        # Generate markdown documentation
        doc = []
        doc.append("# Sisense API Endpoint Validation Results")
        doc.append(f"\nGenerated: {datetime.now().isoformat()}")
        doc.append(f"Base URL: {self.base_url}")
        
        # Summary
        doc.append("\n## Summary")
        summary = mapping['summary']
        doc.append(f"- **Total Endpoints Tested**: {summary['total']}")
        doc.append(f"- **Working Endpoints**: {summary['working']}")
        doc.append(f"- **Broken Endpoints**: {summary['broken']}")
        doc.append(f"- **Authentication Issues**: {summary['auth_issues']}")
        doc.append(f"- **Success Rate**: {(summary['working']/summary['total']*100):.1f}%")
        
        # Working endpoints
        if mapping['working_endpoints']:
            doc.append("\n## ✅ Working Endpoints")
            for endpoint in mapping['working_endpoints']:
                doc.append(f"\n### {endpoint['method']} {endpoint['path']}")
                doc.append(f"- **Status Code**: {endpoint['status_code']}")
                doc.append(f"- **Response Time**: {endpoint['response_time_ms']:.1f}ms")
                doc.append(f"- **Response Size**: {endpoint['response_size']} bytes")
                
                if 'response_schema' in endpoint:
                    doc.append(f"- **Response Schema**: `{endpoint['response_schema'].get('type', 'unknown')}`")
                    if 'example' in endpoint['response_schema']:
                        example = endpoint['response_schema']['example']
                        if isinstance(example, dict) and len(str(example)) > 200:
                            doc.append("- **Response Example**: [Large object - see full results file]")
                        else:
                            doc.append(f"- **Response Example**: `{example}`")
        
        # Broken endpoints
        if mapping['broken_endpoints']:
            doc.append("\n## ❌ Broken Endpoints")
            for endpoint in mapping['broken_endpoints']:
                doc.append(f"\n### {endpoint['method']} {endpoint['path']}")
                doc.append(f"- **Status**: {endpoint.get('status', 'unknown')}")
                doc.append(f"- **Error**: {endpoint['error']}")
                if endpoint['status_code'] > 0:
                    doc.append(f"- **Status Code**: {endpoint['status_code']}")
        
        # Authentication issues
        if mapping['auth_issues']:
            doc.append("\n## 🔐 Authentication Issues")
            for endpoint in mapping['auth_issues']:
                doc.append(f"\n### {endpoint['method']} {endpoint['path']}")
                doc.append(f"- **Error**: {endpoint['error']}")
        
        return "\n".join(doc)

    def save_api_documentation(self, filename: str = "API_ENDPOINTS.md"):
        """Save API documentation to markdown file."""
        doc = self.generate_api_documentation()
        
        with open(filename, 'w') as f:
            f.write(doc)
        
        self.logger.info(f"API documentation saved to {filename}")


def main():
    """Main function to run endpoint validation."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🔍 Sisense API Endpoint Validator")
    print("=" * 50)
    
    # Check configuration
    if Config.DEMO_MODE:
        print("⚠️  Running in DEMO MODE - validation will be limited")
    
    if not Config.has_valid_authentication():
        print("❌ No valid authentication configured")
        print("Please configure SISENSE_API_TOKEN or SISENSE_USERNAME/SISENSE_PASSWORD")
        return False
    
    print(f"🎯 Testing endpoints for: {Config.get_sisense_base_url()}")
    
    # Run validation
    validator = SisenseEndpointValidator()
    
    try:
        # Validate all endpoints
        summary = validator.validate_all_endpoints()
        
        # Generate and save results
        validator.save_validation_results()
        validator.save_api_documentation()
        
        # Print summary
        print(f"\n📊 Validation Results:")
        print(f"✅ Working: {summary['successful']}")
        print(f"❌ Failed: {summary['failed']}")
        print(f"📈 Success Rate: {summary['success_rate']:.1f}%")
        
        print(f"\n📁 Files Generated:")
        print(f"- endpoint_validation_results.json")
        print(f"- API_ENDPOINTS.md")
        
        return summary['success_rate'] > 50  # Consider successful if >50% endpoints work
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return False


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)