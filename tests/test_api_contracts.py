#!/usr/bin/env python3
"""
API Contract Testing for Sisense Integration.

Validates API responses against expected schemas and ensures
consistency across different environments and versions.
"""

import json
import logging
import re
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple
from enum import Enum

from config import Config
from sisense.env_config import get_environment_config
from sisense.auth import get_auth_headers
from sisense.utils import get_http_client


class ContractStatus(Enum):
    """Contract validation status."""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    SKIP = "skip"


@dataclass
class SchemaValidationRule:
    """Schema validation rule definition."""
    field_path: str
    expected_type: str
    required: bool = True
    format_pattern: Optional[str] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    allowed_values: Optional[List[Any]] = None
    description: str = ""


@dataclass
class APIContract:
    """API contract definition."""
    endpoint: str
    method: str = "GET"
    description: str = ""
    expected_status_codes: List[int] = None
    request_schema: Dict[str, Any] = None
    response_schema: List[SchemaValidationRule] = None
    performance_threshold_ms: int = 5000
    tags: List[str] = None

    def __post_init__(self):
        if self.expected_status_codes is None:
            self.expected_status_codes = [200]
        if self.request_schema is None:
            self.request_schema = {}
        if self.response_schema is None:
            self.response_schema = []
        if self.tags is None:
            self.tags = []


@dataclass
class ContractTestResult:
    """Result of contract validation."""
    contract_name: str
    endpoint: str
    status: ContractStatus
    errors: List[str]
    warnings: List[str]
    response_time_ms: float
    status_code: int
    tested_at: str = ""
    
    def __post_init__(self):
        if not self.tested_at:
            self.tested_at = datetime.now().isoformat()


class SisenseAPIContractTester:
    """
    API contract testing system for Sisense integration.
    
    Validates API responses against expected schemas and ensures
    API consistency across environments and versions.
    """

    def __init__(self):
        """Initialize the contract tester."""
        self.logger = logging.getLogger(__name__)
        self.env_config = get_environment_config()
        self.http_client = get_http_client()
        
        # Contract definitions
        self.contracts = self._define_api_contracts()
        
        self.logger.info(f"Initialized API contract tester with {len(self.contracts)} contracts")

    def _define_api_contracts(self) -> Dict[str, APIContract]:
        """Define API contracts for validation."""
        contracts = {}
        
        # Dashboard list contract
        contracts["dashboard_list"] = APIContract(
            endpoint="/api/v1/dashboards",
            description="List dashboards endpoint contract",
            expected_status_codes=[200],
            response_schema=[
                SchemaValidationRule(
                    field_path="$[*].oid",
                    expected_type="string",
                    required=True,
                    min_length=1,
                    description="Dashboard unique identifier"
                ),
                SchemaValidationRule(
                    field_path="$[*].title",
                    expected_type="string",
                    required=True,
                    min_length=1,
                    description="Dashboard title"
                ),
                SchemaValidationRule(
                    field_path="$[*].owner",
                    expected_type="string",
                    required=False,
                    description="Dashboard owner"
                ),
                SchemaValidationRule(
                    field_path="$[*].created",
                    expected_type="string",
                    required=False,
                    format_pattern=r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',
                    description="Creation timestamp"
                )
            ],
            performance_threshold_ms=3000,
            tags=["core", "dashboards", "v1"]
        )
        
        # Authentication contract
        contracts["auth_me"] = APIContract(
            endpoint="/api/v1/authentication/me",
            description="Current user authentication contract",
            expected_status_codes=[200, 401],
            response_schema=[
                SchemaValidationRule(
                    field_path="$.userName",
                    expected_type="string",
                    required=True,
                    description="Username"
                ),
                SchemaValidationRule(
                    field_path="$.userId",
                    expected_type="string",
                    required=False,
                    description="User ID"
                ),
                SchemaValidationRule(
                    field_path="$.email",
                    expected_type="string",
                    required=False,
                    format_pattern=r'^[^@]+@[^@]+\.[^@]+$',
                    description="User email address"
                )
            ],
            performance_threshold_ms=2000,
            tags=["authentication", "user", "v1"]
        )
        
        # Connections contract (V2)
        contracts["connections_v2"] = APIContract(
            endpoint="/api/v2/connections",
            description="List connections (V2) contract",
            expected_status_codes=[200, 404],  # 404 if not available
            response_schema=[
                SchemaValidationRule(
                    field_path="$[*].id",
                    expected_type="string",
                    required=True,
                    description="Connection ID"
                ),
                SchemaValidationRule(
                    field_path="$[*].title",
                    expected_type="string",
                    required=True,
                    description="Connection title"
                ),
                SchemaValidationRule(
                    field_path="$[*].provider",
                    expected_type="string",
                    required=False,
                    description="Connection provider"
                )
            ],
            performance_threshold_ms=3000,
            tags=["connections", "v2", "modern"]
        )
        
        # Data models contract (V2)
        contracts["datamodels_v2"] = APIContract(
            endpoint="/api/v2/datamodels",
            description="List data models (V2) contract",
            expected_status_codes=[200, 404],  # 404 if not available
            response_schema=[
                SchemaValidationRule(
                    field_path="$[*].oid",
                    expected_type="string",
                    required=True,
                    description="Data model OID"
                ),
                SchemaValidationRule(
                    field_path="$[*].title",
                    expected_type="string",
                    required=True,
                    description="Data model title"
                ),
                SchemaValidationRule(
                    field_path="$[*].type",
                    expected_type="string",
                    required=False,
                    allowed_values=["live", "extract"],
                    description="Data model type"
                )
            ],
            performance_threshold_ms=4000,
            tags=["datamodels", "v2", "modern"]
        )
        
        # ElastiCubes contract (V1/Windows)
        contracts["elasticubes_v1"] = APIContract(
            endpoint="/api/v1/elasticubes/getElasticubes",
            description="Get ElastiCubes (V1/Windows) contract",
            expected_status_codes=[200, 404],  # 404 if not available
            response_schema=[
                SchemaValidationRule(
                    field_path="$[*].title",
                    expected_type="string",
                    required=True,
                    description="ElastiCube title"
                ),
                SchemaValidationRule(
                    field_path="$[*].oid",
                    expected_type="string",
                    required=False,
                    description="ElastiCube OID"
                )
            ],
            performance_threshold_ms=4000,
            tags=["datamodels", "elasticubes", "v1", "windows"]
        )
        
        return contracts

    def validate_field_value(self, value: Any, rule: SchemaValidationRule) -> List[str]:
        """
        Validate a field value against a schema rule.
        
        Args:
            value: The value to validate.
            rule: The validation rule.
            
        Returns:
            List[str]: List of validation errors.
        """
        errors = []
        
        # Check if field is required
        if rule.required and value is None:
            errors.append(f"Required field '{rule.field_path}' is missing")
            return errors
        
        if value is None:
            return errors  # Optional field is None - OK
        
        # Type validation
        expected_type = rule.expected_type.lower()
        
        if expected_type == "string" and not isinstance(value, str):
            errors.append(f"Field '{rule.field_path}' expected string, got {type(value).__name__}")
        elif expected_type == "integer" and not isinstance(value, int):
            errors.append(f"Field '{rule.field_path}' expected integer, got {type(value).__name__}")
        elif expected_type == "number" and not isinstance(value, (int, float)):
            errors.append(f"Field '{rule.field_path}' expected number, got {type(value).__name__}")
        elif expected_type == "boolean" and not isinstance(value, bool):
            errors.append(f"Field '{rule.field_path}' expected boolean, got {type(value).__name__}")
        elif expected_type == "array" and not isinstance(value, list):
            errors.append(f"Field '{rule.field_path}' expected array, got {type(value).__name__}")
        elif expected_type == "object" and not isinstance(value, dict):
            errors.append(f"Field '{rule.field_path}' expected object, got {type(value).__name__}")
        
        # String-specific validations
        if isinstance(value, str):
            if rule.min_length is not None and len(value) < rule.min_length:
                errors.append(f"Field '{rule.field_path}' length {len(value)} < minimum {rule.min_length}")
            
            if rule.max_length is not None and len(value) > rule.max_length:
                errors.append(f"Field '{rule.field_path}' length {len(value)} > maximum {rule.max_length}")
            
            if rule.format_pattern and not re.match(rule.format_pattern, value):
                errors.append(f"Field '{rule.field_path}' does not match pattern {rule.format_pattern}")
        
        # Allowed values validation
        if rule.allowed_values is not None and value not in rule.allowed_values:
            errors.append(f"Field '{rule.field_path}' value '{value}' not in allowed values {rule.allowed_values}")
        
        return errors

    def extract_field_by_path(self, data: Any, path: str) -> List[Any]:
        """
        Extract field values by JSONPath-like path.
        
        Args:
            data: Data to extract from.
            path: Path expression (simplified JSONPath).
            
        Returns:
            List[Any]: List of matching values.
        """
        if path == "$":
            return [data]
        
        # Handle array wildcard: $[*].field
        if path.startswith("$[*]."):
            field_name = path[5:]  # Remove "$[*]."
            if isinstance(data, list):
                values = []
                for item in data:
                    if isinstance(item, dict) and field_name in item:
                        values.append(item[field_name])
                return values
            return []
        
        # Handle simple field access: $.field
        if path.startswith("$."):
            field_name = path[2:]  # Remove "$."
            if isinstance(data, dict) and field_name in data:
                return [data[field_name]]
            return []
        
        return []

    def validate_response_schema(self, response_data: Dict[str, Any], schema_rules: List[SchemaValidationRule]) -> Tuple[List[str], List[str]]:
        """
        Validate response data against schema rules.
        
        Args:
            response_data: Response data to validate.
            schema_rules: List of schema validation rules.
            
        Returns:
            Tuple[List[str], List[str]]: (errors, warnings)
        """
        errors = []
        warnings = []
        
        for rule in schema_rules:
            values = self.extract_field_by_path(response_data, rule.field_path)
            
            if not values and rule.required:
                errors.append(f"Required field path '{rule.field_path}' not found in response")
                continue
            
            # Validate each value found
            for value in values:
                field_errors = self.validate_field_value(value, rule)
                errors.extend(field_errors)
        
        return errors, warnings

    def test_api_contract(self, contract_name: str, contract: APIContract) -> ContractTestResult:
        """
        Test a single API contract.
        
        Args:
            contract_name: Name of the contract.
            contract: Contract definition.
            
        Returns:
            ContractTestResult: Test result.
        """
        self.logger.debug(f"Testing contract: {contract_name}")
        
        errors = []
        warnings = []
        
        try:
            # Make API request
            start_time = time.time()
            
            response_data = self.http_client.get(
                endpoint=contract.endpoint,
                headers=get_auth_headers()
            )
            
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            
            # We don't have direct access to status code through our abstraction
            # Assume 200 if we got data back without exception
            status_code = 200
            
            # Performance validation
            if response_time_ms > contract.performance_threshold_ms:
                warnings.append(f"Response time {response_time_ms:.1f}ms exceeds threshold {contract.performance_threshold_ms}ms")
            
            # Schema validation
            if contract.response_schema:
                schema_errors, schema_warnings = self.validate_response_schema(response_data, contract.response_schema)
                errors.extend(schema_errors)
                warnings.extend(schema_warnings)
            
            # Determine overall status
            if errors:
                status = ContractStatus.FAIL
            elif warnings:
                status = ContractStatus.WARNING
            else:
                status = ContractStatus.PASS
            
            return ContractTestResult(
                contract_name=contract_name,
                endpoint=contract.endpoint,
                status=status,
                errors=errors,
                warnings=warnings,
                response_time_ms=response_time_ms,
                status_code=status_code
            )
            
        except Exception as e:
            error_message = str(e)
            
            # Check if this is an expected failure (e.g., 404 for optional endpoints)
            if "404" in error_message and 404 in contract.expected_status_codes:
                return ContractTestResult(
                    contract_name=contract_name,
                    endpoint=contract.endpoint,
                    status=ContractStatus.SKIP,
                    errors=[],
                    warnings=[f"Endpoint not available (404) - this is expected for some environments"],
                    response_time_ms=0,
                    status_code=404
                )
            
            return ContractTestResult(
                contract_name=contract_name,
                endpoint=contract.endpoint,
                status=ContractStatus.FAIL,
                errors=[f"Request failed: {error_message}"],
                warnings=[],
                response_time_ms=0,
                status_code=0
            )

    def test_all_contracts(self, tags_filter: Optional[List[str]] = None) -> Dict[str, ContractTestResult]:
        """
        Test all API contracts.
        
        Args:
            tags_filter: Optional list of tags to filter contracts.
            
        Returns:
            Dict[str, ContractTestResult]: Test results for all contracts.
        """
        results = {}
        
        # Filter contracts by tags if provided
        contracts_to_test = self.contracts
        if tags_filter:
            contracts_to_test = {
                name: contract for name, contract in self.contracts.items()
                if any(tag in contract.tags for tag in tags_filter)
            }
        
        self.logger.info(f"Testing {len(contracts_to_test)} API contracts")
        
        for contract_name, contract in contracts_to_test.items():
            result = self.test_api_contract(contract_name, contract)
            results[contract_name] = result
            
            # Log result
            if result.status == ContractStatus.PASS:
                self.logger.info(f"✅ {contract_name} - PASS ({result.response_time_ms:.1f}ms)")
            elif result.status == ContractStatus.WARNING:
                self.logger.warning(f"⚠️  {contract_name} - WARNING: {', '.join(result.warnings)}")
            elif result.status == ContractStatus.SKIP:
                self.logger.info(f"⏭️  {contract_name} - SKIP: {', '.join(result.warnings)}")
            else:
                self.logger.error(f"❌ {contract_name} - FAIL: {', '.join(result.errors)}")
        
        return results

    def generate_contract_report(self, results: Dict[str, ContractTestResult]) -> Dict[str, Any]:
        """
        Generate comprehensive contract test report.
        
        Args:
            results: Contract test results.
            
        Returns:
            Dict: Comprehensive test report.
        """
        # Statistics
        total = len(results)
        passed = sum(1 for r in results.values() if r.status == ContractStatus.PASS)
        failed = sum(1 for r in results.values() if r.status == ContractStatus.FAIL)
        warnings = sum(1 for r in results.values() if r.status == ContractStatus.WARNING)
        skipped = sum(1 for r in results.values() if r.status == ContractStatus.SKIP)
        
        # Performance statistics
        response_times = [r.response_time_ms for r in results.values() if r.response_time_ms > 0]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Detailed results
        detailed_results = {}
        for name, result in results.items():
            detailed_results[name] = asdict(result)
        
        return {
            "test_summary": {
                "total_contracts": total,
                "passed": passed,
                "failed": failed,
                "warnings": warnings,
                "skipped": skipped,
                "success_rate": (passed / total) * 100 if total > 0 else 0,
                "average_response_time_ms": avg_response_time
            },
            "test_timestamp": datetime.now().isoformat(),
            "environment": {
                "base_url": Config.get_sisense_base_url(),
                "platform": self.env_config.detect_platform_capabilities().platform.value,
            },
            "detailed_results": detailed_results
        }

    def save_contract_report(self, results: Dict[str, ContractTestResult], filename: str = None) -> str:
        """
        Save contract test report to file.
        
        Args:
            results: Contract test results.
            filename: Optional filename.
            
        Returns:
            str: Filename of saved report.
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"api_contract_report_{timestamp}.json"
        
        report = self.generate_contract_report(results)
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"Contract test report saved to {filename}")
        return filename


def main():
    """Main function for contract testing."""
    import argparse
    import time
    
    parser = argparse.ArgumentParser(description="Sisense API Contract Tester")
    parser.add_argument("--tags", nargs="+", help="Filter contracts by tags")
    parser.add_argument("--output", type=str, help="Output filename for test report")
    parser.add_argument("--continuous", action="store_true", help="Run continuous contract testing")
    parser.add_argument("--interval", type=int, default=300, help="Continuous testing interval in seconds")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("📋 Sisense API Contract Tester")
    print("=" * 40)
    
    # Check configuration
    if not Config.has_valid_authentication():
        print("❌ No valid authentication configured")
        return False
    
    print(f"🎯 Testing contracts for: {Config.get_sisense_base_url()}")
    
    # Run contract tests
    tester = SisenseAPIContractTester()
    
    try:
        if args.continuous:
            print(f"🔄 Starting continuous contract testing (interval: {args.interval}s)")
            test_count = 0
            
            while True:
                test_count += 1
                print(f"\n📋 Contract test run #{test_count}")
                
                results = tester.test_all_contracts(tags_filter=args.tags)
                report = tester.generate_contract_report(results)
                
                # Print summary
                summary = report['test_summary']
                print(f"✅ Passed: {summary['passed']}")
                print(f"❌ Failed: {summary['failed']}")
                print(f"⚠️  Warnings: {summary['warnings']}")
                print(f"⏭️  Skipped: {summary['skipped']}")
                print(f"📈 Success Rate: {summary['success_rate']:.1f}%")
                
                time.sleep(args.interval)
        else:
            print("🏃 Running contract tests...")
            results = tester.test_all_contracts(tags_filter=args.tags)
            
            # Save report
            filename = tester.save_contract_report(results, args.output)
            
            # Print summary
            report = tester.generate_contract_report(results)
            summary = report['test_summary']
            
            print(f"\n📊 Contract Test Results:")
            print(f"✅ Passed: {summary['passed']}")
            print(f"❌ Failed: {summary['failed']}")
            print(f"⚠️  Warnings: {summary['warnings']}")
            print(f"⏭️  Skipped: {summary['skipped']}")
            print(f"📈 Success Rate: {summary['success_rate']:.1f}%")
            print(f"⏱️  Average Response Time: {summary['average_response_time_ms']:.1f}ms")
            print(f"📁 Report Saved: {filename}")
        
        return True
        
    except Exception as e:
        print(f"❌ Contract testing failed: {e}")
        return False


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)