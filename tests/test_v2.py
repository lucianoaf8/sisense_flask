#!/usr/bin/env python3
"""
Test script for Sisense Flask Integration v2.0
Verifies the modernized GUI implementation and new features
"""

import os
import sys
import time
import requests
import subprocess
from pathlib import Path

class SisenseFlaskTester:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.project_root = Path(__file__).parent.parent  # Use relative path from test location
        self.test_results = []
        
    def run_all_tests(self):
        """Run all verification tests."""
        print("🚀 Starting Sisense Flask Integration v2.0 Tests")
        print("=" * 60)
        
        # Test 1: File Structure
        self.test_file_structure()
        
        # Test 2: Dependencies
        self.test_dependencies()
        
        # Test 3: Application Startup
        app_process = self.test_app_startup()
        
        if app_process:
            # Wait for app to start
            time.sleep(3)
            
            # Test 4: Basic Routes
            self.test_basic_routes()
            
            # Test 5: API Endpoints
            self.test_api_endpoints()
            
            # Test 6: New Features
            self.test_new_features()
            
            # Stop application
            app_process.terminate()
            app_process.wait()
        
        # Print summary
        self.print_summary()
        
    def test_file_structure(self):
        """Test that all required files exist."""
        print("\n📁 Testing File Structure...")
        
        required_files = [
            "app.py",
            "sisense/config.py",
            "requirements.txt",
            "sisense/__init__.py",
            "sisense/auth.py",
            "sisense/logger.py",
            "templates/base.html",
            "templates/dashboard.html",
            "static/css/styles.css",
            "static/js/app.js",
            "static/js/panels.js",
            "static/js/logger.js"
        ]
        
        missing_files = []
        for file_path in required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
            else:
                print(f"✅ {file_path}")
        
        if missing_files:
            print(f"❌ Missing files: {missing_files}")
            self.test_results.append(("File Structure", False, f"Missing: {missing_files}"))
        else:
            print("✅ All required files present")
            self.test_results.append(("File Structure", True, "All files present"))
    
    def test_dependencies(self):
        """Test that all dependencies are installed."""
        print("\n📦 Testing Dependencies...")
        
        try:
            import flask
            import requests
            import dotenv
            print("✅ Core dependencies installed")
            self.test_results.append(("Dependencies", True, "All dependencies available"))
        except ImportError as e:
            print(f"❌ Missing dependency: {e}")
            self.test_results.append(("Dependencies", False, str(e)))
    
    def test_app_startup(self):
        """Test application startup."""
        print("\n🚀 Testing Application Startup...")
        
        try:
            # Check if app.py can be imported
            app_path = self.project_root / "app.py"
            if not app_path.exists():
                print("❌ app.py not found")
                self.test_results.append(("App Startup", False, "app.py not found"))
                return None
            
            # Try to start the application
            process = subprocess.Popen(
                [sys.executable, "app.py"],
                cwd=str(self.project_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait a moment and check if it's still running
            time.sleep(2)
            if process.poll() is None:
                print("✅ Application started successfully")
                self.test_results.append(("App Startup", True, "Application running"))
                return process
            else:
                stdout, stderr = process.communicate()
                print(f"❌ Application failed to start: {stderr.decode()}")
                self.test_results.append(("App Startup", False, f"Startup failed: {stderr.decode()[:100]}"))
                return None
                
        except Exception as e:
            print(f"❌ Error starting application: {e}")
            self.test_results.append(("App Startup", False, str(e)))
            return None
    
    def test_basic_routes(self):
        """Test basic route accessibility."""
        print("\n🌐 Testing Basic Routes...")
        
        routes = [
            "/",
            "/datamodels", 
            "/dashboards",
            "/connections",
            "/sql",
            "/jaql",
            "/docs"
        ]
        
        failed_routes = []
        for route in routes:
            try:
                response = requests.get(f"{self.base_url}{route}", timeout=5)
                if response.status_code == 200:
                    print(f"✅ {route}")
                else:
                    print(f"❌ {route} - Status: {response.status_code}")
                    failed_routes.append(f"{route} ({response.status_code})")
            except requests.RequestException as e:
                print(f"❌ {route} - Error: {e}")
                failed_routes.append(f"{route} (Error)")
        
        if failed_routes:
            self.test_results.append(("Basic Routes", False, f"Failed: {failed_routes}"))
        else:
            print("✅ All basic routes accessible")
            self.test_results.append(("Basic Routes", True, "All routes accessible"))
    
    def test_api_endpoints(self):
        """Test API endpoints."""
        print("\n🔌 Testing API Endpoints...")
        
        api_endpoints = [
            "/api/auth/validate",
            "/health",
            "/api/logs/recent"
        ]
        
        failed_endpoints = []
        for endpoint in api_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                if response.status_code in [200, 401, 403]:  # These are acceptable
                    print(f"✅ {endpoint}")
                else:
                    print(f"❌ {endpoint} - Status: {response.status_code}")
                    failed_endpoints.append(f"{endpoint} ({response.status_code})")
            except requests.RequestException as e:
                print(f"❌ {endpoint} - Error: {e}")
                failed_endpoints.append(f"{endpoint} (Error)")
        
        if failed_endpoints:
            self.test_results.append(("API Endpoints", False, f"Failed: {failed_endpoints}"))
        else:
            print("✅ All API endpoints responding")
            self.test_results.append(("API Endpoints", True, "All endpoints responding"))
    
    def test_new_features(self):
        """Test new v2.0 features."""
        print("\n🆕 Testing New Features...")
        
        # Test logging endpoints
        try:
            response = requests.get(f"{self.base_url}/api/logs/recent", timeout=5)
            if response.status_code == 200:
                print("✅ Enhanced logging system accessible")
                logs_working = True
            else:
                print("❌ Enhanced logging system not responding")
                logs_working = False
        except:
            print("❌ Enhanced logging system error")
            logs_working = False
        
        # Test if logs directory was created
        logs_dir = self.project_root / "logs"
        if logs_dir.exists():
            print("✅ Logs directory created")
            logs_dir_exists = True
        else:
            print("❌ Logs directory not found")
            logs_dir_exists = False
        
        # Test modernized templates
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            if "Sisense Flask Integration" in response.text and "v2.0" in response.text:
                print("✅ Modernized templates loaded")
                templates_modern = True
            else:
                print("❌ Templates may not be updated")
                templates_modern = False
        except:
            print("❌ Error testing templates")
            templates_modern = False
        
        # Overall new features assessment
        features_working = logs_working and logs_dir_exists and templates_modern
        if features_working:
            self.test_results.append(("New Features", True, "All v2.0 features working"))
        else:
            failed_features = []
            if not logs_working: failed_features.append("logging")
            if not logs_dir_exists: failed_features.append("logs directory")
            if not templates_modern: failed_features.append("templates")
            self.test_results.append(("New Features", False, f"Issues: {failed_features}"))
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for _, success, _ in self.test_results if success)
        total = len(self.test_results)
        
        for test_name, success, details in self.test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status:8} {test_name:20} {details}")
        
        print("-" * 60)
        print(f"OVERALL: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
        
        if passed == total:
            print("\n🎉 All tests passed! Sisense Flask Integration v2.0 is ready!")
        else:
            print(f"\n⚠️  {total - passed} test(s) failed. Please review the issues above.")

def main():
    """Main test execution."""
    tester = SisenseFlaskTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
