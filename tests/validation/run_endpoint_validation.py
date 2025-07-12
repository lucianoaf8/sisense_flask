#!/usr/bin/env python3
"""
Run endpoint validation and generate comprehensive API documentation.

This script runs the endpoint validator against the configured Sisense instance
and generates comprehensive documentation of working vs non-working endpoints.
"""

import json
import logging
import sys
from datetime import datetime

# Import our validation utilities
from config import Config
from endpoint_validator import SisenseEndpointValidator
from api_health import SisenseHealthChecker  
from test_api_contracts import SisenseAPIContractTester


def setup_logging():
    """Setup comprehensive logging for validation."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(f'endpoint_validation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        ]
    )


def check_configuration():
    """Check if the environment is properly configured for validation."""
    print("🔧 Configuration Check")
    print("=" * 30)
    
    # Check basic configuration
    print(f"Sisense URL: {Config.SISENSE_URL}")
    print(f"Demo Mode: {Config.DEMO_MODE}")
    print(f"Flask Environment: {Config.FLASK_ENV}")
    
    # Check authentication
    auth_type = Config.get_authentication_type()
    print(f"Authentication Type: {auth_type}")
    
    if auth_type == 'none':
        print("❌ No valid authentication configured")
        print("Please set SISENSE_API_TOKEN or SISENSE_USERNAME/SISENSE_PASSWORD")
        return False
    elif auth_type == 'api_token':
        token_preview = Config.SISENSE_API_TOKEN[:10] + "..." if len(Config.SISENSE_API_TOKEN) > 10 else Config.SISENSE_API_TOKEN
        print(f"✅ API Token configured: {token_preview}")
    else:
        print(f"✅ Username/Password configured: {Config.SISENSE_USERNAME}")
    
    # Check environment validation
    issues = Config.validate_environment_configuration()
    if issues:
        print(f"⚠️  Configuration Issues ({len(issues)}):")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✅ Configuration validation passed")
    
    return True


def run_endpoint_validation():
    """Run comprehensive endpoint validation."""
    print("\n🔍 Endpoint Validation")
    print("=" * 30)
    
    validator = SisenseEndpointValidator()
    
    try:
        # Run validation
        print("Starting endpoint validation...")
        summary = validator.validate_all_endpoints()
        
        # Save results
        validator.save_validation_results("endpoint_validation_results.json")
        validator.save_api_documentation("API_ENDPOINTS.md")
        
        # Print summary
        print(f"\n📊 Validation Summary:")
        print(f"✅ Successful: {summary['successful']}")
        print(f"❌ Failed: {summary['failed']}")
        print(f"📈 Success Rate: {summary['success_rate']:.1f}%")
        
        return summary
        
    except Exception as e:
        print(f"❌ Endpoint validation failed: {e}")
        return None


def run_health_checks():
    """Run health check validation."""
    print("\n💚 Health Check Validation")
    print("=" * 30)
    
    health_checker = SisenseHealthChecker()
    
    try:
        # Run health checks
        print("Running health checks...")
        report = health_checker.run_health_check_cycle()
        
        # Save report
        filename = health_checker.save_health_report("health_check_results.json")
        
        # Print summary
        summary = report['summary']
        alerts = report['alerts']
        
        print(f"\n📊 Health Summary:")
        print(f"Overall Status: {summary['overall_status'].upper()}")
        print(f"Endpoints Checked: {len(summary['critical_endpoints'])}")
        print(f"Active Alerts: {len(alerts)}")
        
        if alerts:
            print("\n🚨 Active Alerts:")
            for alert in alerts:
                print(f"  - {alert['severity'].upper()}: {alert['message']}")
        
        return report
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return None


def run_contract_testing():
    """Run API contract testing."""
    print("\n📋 Contract Testing")
    print("=" * 30)
    
    contract_tester = SisenseAPIContractTester()
    
    try:
        # Run contract tests
        print("Running contract tests...")
        results = contract_tester.test_all_contracts()
        
        # Save report
        filename = contract_tester.save_contract_report(results, "contract_test_results.json")
        
        # Generate summary
        report = contract_tester.generate_contract_report(results)
        summary = report['test_summary']
        
        print(f"\n📊 Contract Summary:")
        print(f"✅ Passed: {summary['passed']}")
        print(f"❌ Failed: {summary['failed']}")
        print(f"⚠️  Warnings: {summary['warnings']}")
        print(f"⏭️  Skipped: {summary['skipped']}")
        print(f"📈 Success Rate: {summary['success_rate']:.1f}%")
        print(f"⏱️  Avg Response Time: {summary['average_response_time_ms']:.1f}ms")
        
        return report
        
    except Exception as e:
        print(f"❌ Contract testing failed: {e}")
        return None


def generate_comprehensive_report(validation_summary, health_report, contract_report):
    """Generate comprehensive validation report."""
    print("\n📄 Generating Comprehensive Report")
    print("=" * 40)
    
    # Combine all results
    comprehensive_report = {
        "validation_timestamp": datetime.now().isoformat(),
        "environment": {
            "base_url": Config.get_sisense_base_url(),
            "authentication_type": Config.get_authentication_type(),
            "flask_env": Config.FLASK_ENV,
            "demo_mode": Config.DEMO_MODE
        },
        "endpoint_validation": validation_summary,
        "health_checks": health_report,
        "contract_testing": contract_report
    }
    
    # Save comprehensive report
    filename = f"comprehensive_api_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(comprehensive_report, f, indent=2)
    
    print(f"📁 Comprehensive report saved: {filename}")
    
    # Generate summary
    print(f"\n🎯 Overall Validation Results:")
    
    if validation_summary:
        print(f"📊 Endpoint Validation: {validation_summary['success_rate']:.1f}% success rate")
    
    if health_report:
        print(f"💚 Health Status: {health_report['summary']['overall_status'].upper()}")
    
    if contract_report:
        print(f"📋 Contract Tests: {contract_report['test_summary']['success_rate']:.1f}% success rate")
    
    return comprehensive_report


def main():
    """Main validation runner."""
    setup_logging()
    
    print("🚀 Sisense API Comprehensive Validation")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Check configuration
    if not check_configuration():
        print("\n❌ Configuration check failed. Please fix configuration issues before proceeding.")
        return False
    
    # Run all validations
    validation_summary = None
    health_report = None
    contract_report = None
    
    if not Config.DEMO_MODE:
        # Run endpoint validation
        validation_summary = run_endpoint_validation()
        
        # Run health checks
        health_report = run_health_checks()
        
        # Run contract testing
        contract_report = run_contract_testing()
    else:
        print("\n⚠️  Running in DEMO MODE - API validation skipped")
        print("Set DEMO_MODE=false and configure authentication to run full validation")
    
    # Generate comprehensive report
    if validation_summary or health_report or contract_report:
        comprehensive_report = generate_comprehensive_report(
            validation_summary, health_report, contract_report
        )
        
        # Determine overall success
        success_count = 0
        total_count = 0
        
        if validation_summary:
            success_count += validation_summary['successful']
            total_count += validation_summary['total_endpoints']
        
        if health_report:
            overall_health = health_report['summary']['overall_status']
            if overall_health in ['healthy', 'degraded']:
                success_count += 1
            total_count += 1
        
        if contract_report:
            contract_success = contract_report['test_summary']['passed']
            contract_total = contract_report['test_summary']['total_contracts']
            success_count += contract_success
            total_count += contract_total
        
        overall_success_rate = (success_count / total_count) * 100 if total_count > 0 else 0
        
        print(f"\n🎉 Validation Complete!")
        print(f"📈 Overall Success Rate: {overall_success_rate:.1f}%")
        print(f"📁 Files Generated:")
        print(f"  - endpoint_validation_results.json")
        print(f"  - API_ENDPOINTS.md")
        print(f"  - health_check_results.json")
        print(f"  - contract_test_results.json")
        print(f"  - comprehensive_api_validation_*.json")
        
        return overall_success_rate >= 70  # Consider successful if >= 70%
    else:
        print("\n⚠️  No validation results generated")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)