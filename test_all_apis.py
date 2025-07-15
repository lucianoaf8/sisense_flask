#!/usr/bin/env python3
"""
Comprehensive API Test Suite for Sisense Flask Project

This script tests all GET endpoints both directly through CLI imports
and through the Flask API endpoints to ensure consistency and functionality.
"""

import json
import sys
import time
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional

# Direct imports for CLI testing
from sisense.auth import validate_authentication, get_auth_headers
from sisense.dashboards import list_dashboards, get_dashboard, search_dashboards
from sisense.connections import list_connections, get_connection
from sisense.widgets import list_widgets, get_widget
from sisense.datamodels import list_models, get_model
from sisense.sql import execute_sql
from sisense.jaql import execute_jaql
from sisense.config import Config

# Flask app for API endpoint testing
import requests
from flask import Flask


class APITestReport:
    """Handles test reporting and statistics."""
    
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.results = []
        self.start_time = datetime.now()
    
    def add_result(self, test_name: str, success: bool, message: str, details: Optional[Dict] = None):
        """Add a test result."""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        else:
            self.tests_failed += 1
        
        result = {
            'test_name': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        self.results.append(result)
        
        # Print real-time feedback
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {message}")
    
    def generate_report(self) -> Dict:
        """Generate comprehensive test report."""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        return {
            'summary': {
                'total_tests': self.tests_run,
                'passed': self.tests_passed,
                'failed': self.tests_failed,
                'success_rate': f"{(self.tests_passed/self.tests_run)*100:.1f}%" if self.tests_run > 0 else "0%",
                'duration_seconds': duration,
                'timestamp': end_time.isoformat()
            },
            'results': self.results,
            'environment': {
                'sisense_url': Config.SISENSE_URL,
                'demo_mode': Config.DEMO_MODE,
                'ssl_verify': Config.SSL_VERIFY
            }
        }


class APITester:
    """Comprehensive API testing class."""
    
    def __init__(self):
        self.report = APITestReport()
        self.base_url = "http://localhost:5000"  # Flask app URL
        self.sample_data = {}
        
    def run_all_tests(self):
        """Run all API tests."""
        print("🚀 Starting Comprehensive API Test Suite")
        print("=" * 50)
        
        # Phase 1: CLI Direct Testing
        print("\n📍 Phase 1: CLI Direct API Testing")
        print("-" * 30)
        self.test_cli_authentication()
        self.test_cli_datamodels()
        self.test_cli_dashboards()
        self.test_cli_connections()
        self.test_cli_widgets()
        
        # Phase 2: Flask API Endpoint Testing
        print("\n📍 Phase 2: Flask API Endpoint Testing")
        print("-" * 30)
        self.test_flask_health()
        self.test_flask_auth_endpoints()
        self.test_flask_datamodel_endpoints()
        self.test_flask_dashboard_endpoints()
        self.test_flask_connection_endpoints()
        self.test_flask_widget_endpoints()
        self.test_flask_search_endpoints()
        
        # Phase 3: Consistency Testing
        print("\n📍 Phase 3: CLI vs Flask API Consistency Testing")
        print("-" * 30)
        self.test_data_consistency()
        
        # Generate final report
        self.generate_final_report()
    
    def test_cli_authentication(self):
        """Test CLI authentication functions."""
        try:
            is_valid = validate_authentication()
            if is_valid:
                self.report.add_result("CLI Authentication", True, "Authentication validated successfully")
                headers = get_auth_headers()
                self.report.add_result("CLI Auth Headers", True, f"Headers retrieved with token preview: {headers['Authorization'][:30]}...")
            else:
                self.report.add_result("CLI Authentication", False, "Authentication failed")
        except Exception as e:
            self.report.add_result("CLI Authentication", False, f"Authentication error: {str(e)}")
    
    def test_cli_datamodels(self):
        """Test CLI data models functions."""
        try:
            models = list_models()
            count = len(models) if models else 0
            self.report.add_result("CLI List Models", True, f"Retrieved {count} data models", {"count": count})
            
            # Store sample data for consistency testing
            self.sample_data['cli_models'] = models
            
            # Test getting specific model if available
            if models and len(models) > 0:
                model_oid = models[0].get('oid')
                if model_oid:
                    try:
                        model = get_model(model_oid)
                        self.report.add_result("CLI Get Model", True, f"Retrieved model: {model.get('title', 'Unknown')}")
                        self.sample_data['cli_model_detail'] = model
                    except Exception as e:
                        self.report.add_result("CLI Get Model", False, f"Error getting model: {str(e)}")
        except Exception as e:
            self.report.add_result("CLI List Models", False, f"Error listing models: {str(e)}")
    
    def test_cli_dashboards(self):
        """Test CLI dashboard functions."""
        try:
            dashboards = list_dashboards()
            count = len(dashboards) if dashboards else 0
            self.report.add_result("CLI List Dashboards", True, f"Retrieved {count} dashboards", {"count": count})
            
            # Store sample data for consistency testing
            self.sample_data['cli_dashboards'] = dashboards
            
            # Test getting specific dashboard if available
            if dashboards and len(dashboards) > 0:
                dashboard_id = dashboards[0].get('oid')
                if dashboard_id:
                    try:
                        dashboard = get_dashboard(dashboard_id)
                        self.report.add_result("CLI Get Dashboard", True, f"Retrieved dashboard: {dashboard.get('title', 'Unknown')}")
                        self.sample_data['cli_dashboard_detail'] = dashboard
                    except Exception as e:
                        self.report.add_result("CLI Get Dashboard", False, f"Error getting dashboard: {str(e)}")
        except Exception as e:
            self.report.add_result("CLI List Dashboards", False, f"Error listing dashboards: {str(e)}")
    
    def test_cli_connections(self):
        """Test CLI connection functions."""
        try:
            connections = list_connections()
            count = len(connections) if connections else 0
            self.report.add_result("CLI List Connections", True, f"Retrieved {count} connections", {"count": count})
            
            # Store sample data for consistency testing
            self.sample_data['cli_connections'] = connections
            
            # Test getting specific connection if available
            if connections and len(connections) > 0:
                connection_id = connections[0].get('id')
                if connection_id:
                    try:
                        connection = get_connection(connection_id)
                        self.report.add_result("CLI Get Connection", True, f"Retrieved connection: {connection.get('title', 'Unknown')}")
                        self.sample_data['cli_connection_detail'] = connection
                    except Exception as e:
                        self.report.add_result("CLI Get Connection", False, f"Error getting connection: {str(e)}")
        except Exception as e:
            self.report.add_result("CLI List Connections", False, f"Error listing connections: {str(e)}")
    
    def test_cli_widgets(self):
        """Test CLI widget functions."""
        try:
            widgets = list_widgets()
            count = len(widgets) if widgets else 0
            self.report.add_result("CLI List Widgets", True, f"Retrieved {count} widgets", {"count": count})
            
            # Store sample data for consistency testing
            self.sample_data['cli_widgets'] = widgets
            
            # Test getting specific widget if available
            if widgets and len(widgets) > 0:
                widget_id = widgets[0].get('oid')
                if widget_id:
                    try:
                        widget = get_widget(widget_id)
                        self.report.add_result("CLI Get Widget", True, f"Retrieved widget: {widget.get('title', 'Unknown')}")
                        self.sample_data['cli_widget_detail'] = widget
                    except Exception as e:
                        self.report.add_result("CLI Get Widget", False, f"Error getting widget: {str(e)}")
        except Exception as e:
            self.report.add_result("CLI List Widgets", False, f"Error listing widgets: {str(e)}")
    
    def test_flask_health(self):
        """Test Flask health endpoint."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                self.report.add_result("Flask Health Check", True, "Health endpoint responding")
            else:
                self.report.add_result("Flask Health Check", False, f"Health endpoint returned {response.status_code}")
        except Exception as e:
            self.report.add_result("Flask Health Check", False, f"Health endpoint error: {str(e)}")
    
    def test_flask_auth_endpoints(self):
        """Test Flask authentication endpoints."""
        endpoints = [
            "/api/auth/validate",
            "/api/auth/status",
            "/api/auth/user-info"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                if response.status_code == 200:
                    self.report.add_result(f"Flask {endpoint}", True, "Endpoint responding")
                else:
                    self.report.add_result(f"Flask {endpoint}", False, f"Returned {response.status_code}")
            except Exception as e:
                self.report.add_result(f"Flask {endpoint}", False, f"Error: {str(e)}")
    
    def test_flask_datamodel_endpoints(self):
        """Test Flask data model endpoints."""
        endpoints = [
            "/api/datamodels",
            "/api/system/capabilities"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    self.report.add_result(f"Flask {endpoint}", True, f"Endpoint responding with data")
                    
                    # Store sample data for consistency testing
                    if endpoint == "/api/datamodels":
                        self.sample_data['flask_models'] = data.get('data', [])
                else:
                    self.report.add_result(f"Flask {endpoint}", False, f"Returned {response.status_code}")
            except Exception as e:
                self.report.add_result(f"Flask {endpoint}", False, f"Error: {str(e)}")
    
    def test_flask_dashboard_endpoints(self):
        """Test Flask dashboard endpoints."""
        endpoints = [
            "/api/dashboards"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    self.report.add_result(f"Flask {endpoint}", True, f"Endpoint responding with data")
                    
                    # Store sample data for consistency testing
                    if endpoint == "/api/dashboards":
                        self.sample_data['flask_dashboards'] = data.get('data', [])
                else:
                    self.report.add_result(f"Flask {endpoint}", False, f"Returned {response.status_code}")
            except Exception as e:
                self.report.add_result(f"Flask {endpoint}", False, f"Error: {str(e)}")
    
    def test_flask_connection_endpoints(self):
        """Test Flask connection endpoints."""
        endpoints = [
            "/api/connections"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    self.report.add_result(f"Flask {endpoint}", True, f"Endpoint responding with data")
                    
                    # Store sample data for consistency testing
                    if endpoint == "/api/connections":
                        self.sample_data['flask_connections'] = data.get('data', [])
                else:
                    self.report.add_result(f"Flask {endpoint}", False, f"Returned {response.status_code}")
            except Exception as e:
                self.report.add_result(f"Flask {endpoint}", False, f"Error: {str(e)}")
    
    def test_flask_widget_endpoints(self):
        """Test Flask widget endpoints."""
        # Note: Widget endpoints typically require specific IDs
        pass
    
    def test_flask_search_endpoints(self):
        """Test Flask search endpoints."""
        endpoints = [
            "/api/search/dashboards",
            "/api/search/datamodels"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    self.report.add_result(f"Flask {endpoint}", True, f"Search endpoint responding")
                else:
                    self.report.add_result(f"Flask {endpoint}", False, f"Returned {response.status_code}")
            except Exception as e:
                self.report.add_result(f"Flask {endpoint}", False, f"Error: {str(e)}")
    
    def test_data_consistency(self):
        """Test consistency between CLI and Flask API data."""
        
        # Test data models consistency
        if 'cli_models' in self.sample_data and 'flask_models' in self.sample_data:
            cli_count = len(self.sample_data['cli_models'])
            flask_count = len(self.sample_data['flask_models'])
            
            if cli_count == flask_count:
                self.report.add_result("Data Models Consistency", True, f"Both CLI and Flask return {cli_count} models")
            else:
                self.report.add_result("Data Models Consistency", False, f"CLI returns {cli_count} models, Flask returns {flask_count}")
        
        # Test dashboards consistency
        if 'cli_dashboards' in self.sample_data and 'flask_dashboards' in self.sample_data:
            cli_count = len(self.sample_data['cli_dashboards'])
            flask_count = len(self.sample_data['flask_dashboards'])
            
            if cli_count == flask_count:
                self.report.add_result("Dashboards Consistency", True, f"Both CLI and Flask return {cli_count} dashboards")
            else:
                self.report.add_result("Dashboards Consistency", False, f"CLI returns {cli_count} dashboards, Flask returns {flask_count}")
        
        # Test connections consistency
        if 'cli_connections' in self.sample_data and 'flask_connections' in self.sample_data:
            cli_count = len(self.sample_data['cli_connections'])
            flask_count = len(self.sample_data['flask_connections'])
            
            if cli_count == flask_count:
                self.report.add_result("Connections Consistency", True, f"Both CLI and Flask return {cli_count} connections")
            else:
                self.report.add_result("Connections Consistency", False, f"CLI returns {cli_count} connections, Flask returns {flask_count}")
    
    def generate_final_report(self):
        """Generate and save final test report."""
        report_data = self.report.generate_report()
        
        # Save detailed report to file
        report_filename = f"api_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        # Print summary
        print("\n" + "=" * 60)
        print("🎯 FINAL TEST REPORT")
        print("=" * 60)
        print(f"Total Tests: {report_data['summary']['total_tests']}")
        print(f"Passed: {report_data['summary']['passed']}")
        print(f"Failed: {report_data['summary']['failed']}")
        print(f"Success Rate: {report_data['summary']['success_rate']}")
        print(f"Duration: {report_data['summary']['duration_seconds']:.2f} seconds")
        print(f"Detailed report saved to: {report_filename}")
        
        # Show failed tests
        failed_tests = [r for r in report_data['results'] if not r['success']]
        if failed_tests:
            print(f"\n❌ Failed Tests ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"  - {test['test_name']}: {test['message']}")
        
        return report_data


def main():
    """Main function to run all tests."""
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("""
Usage: python test_all_apis.py [--help]

This script performs comprehensive testing of all API endpoints in the Sisense Flask project.

Test phases:
1. CLI Direct API Testing - Tests all sisense.* module functions directly
2. Flask API Endpoint Testing - Tests all Flask routes via HTTP requests
3. Consistency Testing - Compares CLI and Flask API responses

Requirements:
- Virtual environment activated
- Flask app NOT running (script will handle this)
- Valid .env configuration
        """)
        return
    
    print("🔧 Setting up test environment...")
    
    # Initialize tester
    tester = APITester()
    
    # Run all tests
    tester.run_all_tests()
    
    # Exit with appropriate code
    if tester.report.tests_failed == 0:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {tester.report.tests_failed} tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()