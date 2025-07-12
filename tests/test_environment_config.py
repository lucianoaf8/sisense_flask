#!/usr/bin/env python3
"""
Test script for environment-specific API configuration.

Tests backward compatibility, environment detection, and configuration validation.
"""

import os
import sys
import logging
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from sisense.env_config import get_environment_config, SisenseEnvironmentConfig
from sisense.utils import get_http_client


def setup_test_logging():
    """Setup logging for testing."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def test_backward_compatibility():
    """Test that existing configuration still works."""
    print("\n=== Testing Backward Compatibility ===")
    
    try:
        # Test basic configuration loading
        config_summary = {
            'sisense_url': Config.SISENSE_URL,
            'has_api_token': bool(Config.SISENSE_API_TOKEN),
            'flask_env': Config.FLASK_ENV,
            'demo_mode': Config.DEMO_MODE
        }
        print(f"✅ Basic configuration loaded: {config_summary}")
        
        # Test HTTP client creation
        http_client = get_http_client()
        print(f"✅ HTTP client created: {type(http_client).__name__}")
        
        # Test environment config creation
        env_config = get_environment_config()
        print(f"✅ Environment config created: {type(env_config).__name__}")
        
        return True
        
    except Exception as e:
        print(f"❌ Backward compatibility test failed: {e}")
        return False


def test_environment_detection():
    """Test environment and platform detection."""
    print("\n=== Testing Environment Detection ===")
    
    try:
        env_config = get_environment_config()
        
        # Test environment profile
        profile = env_config.get_environment_profile()
        print(f"Environment Profile:")
        for key, value in profile.items():
            print(f"  {key}: {value}")
        
        # Test platform detection (without making actual API calls in test)
        if not Config.DEMO_MODE:
            platform = env_config.detect_platform_capabilities()
            print(f"\nPlatform Detection:")
            print(f"  Platform: {platform.platform.value}")
            print(f"  Deployment: {platform.deployment.value}")
            print(f"  Supports V2: {platform.supports_v2}")
            print(f"  Detection Method: {platform.detection_method}")
            
            if platform.limitations:
                print(f"  Limitations: {platform.limitations}")
        else:
            print("Skipping platform detection in demo mode")
        
        return True
        
    except Exception as e:
        print(f"❌ Environment detection test failed: {e}")
        return False


def test_endpoint_configuration():
    """Test endpoint URL construction."""
    print("\n=== Testing Endpoint Configuration ===")
    
    try:
        env_config = get_environment_config()
        
        # Test base path handling
        print("Base Path Testing:")
        test_cases = [
            ('dashboards', ''),
            ('dashboards', 'dashboard-123'),
            ('connections', ''),
            ('datamodels', 'model-456/tables')
        ]
        
        for resource_type, suffix in test_cases:
            endpoint = env_config.get_endpoint_url(resource_type, suffix)
            print(f"  {resource_type} + '{suffix}' → {endpoint}")
        
        # Test platform headers
        headers = env_config.get_platform_headers()
        print(f"\nPlatform Headers: {headers}")
        
        return True
        
    except Exception as e:
        print(f"❌ Endpoint configuration test failed: {e}")
        return False


def test_configuration_validation():
    """Test configuration validation and summary."""
    print("\n=== Testing Configuration Validation ===")
    
    try:
        env_config = get_environment_config()
        
        # Test validation
        issues = env_config.validate_environment_configuration()
        if issues:
            print("Configuration Issues:")
            for issue in issues:
                print(f"  ⚠️  {issue}")
        else:
            print("✅ No configuration issues found")
        
        # Test configuration summary
        summary = env_config.get_configuration_summary()
        print(f"\nConfiguration Summary:")
        for section, data in summary.items():
            print(f"  {section.upper()}:")
            if isinstance(data, dict):
                for key, value in data.items():
                    print(f"    {key}: {value}")
            else:
                print(f"    {data}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration validation test failed: {e}")
        return False


def test_environment_overrides():
    """Test environment variable overrides."""
    print("\n=== Testing Environment Overrides ===")
    
    try:
        # Test current override values
        overrides = {
            'SISENSE_PLATFORM_OVERRIDE': Config.SISENSE_PLATFORM_OVERRIDE,
            'SISENSE_API_VERSION_OVERRIDE': Config.SISENSE_API_VERSION_OVERRIDE,
            'SISENSE_BASE_PATH_OVERRIDE': Config.SISENSE_BASE_PATH_OVERRIDE,
            'SISENSE_DISABLE_LIVE_FEATURES': Config.SISENSE_DISABLE_LIVE_FEATURES,
            'SISENSE_DEBUG_MODE': Config.SISENSE_DEBUG_MODE
        }
        
        print("Current Override Values:")
        for key, value in overrides.items():
            print(f"  {key}: {value}")
        
        # Test environment config respects overrides
        env_config = get_environment_config()
        print(f"\nEnvironment Config Override Handling:")
        print(f"  Platform Override: {env_config.platform_override}")
        print(f"  API Version Override: {env_config.api_version_override}")
        print(f"  Base Path Override: {env_config.base_path_override}")
        print(f"  Disable Live Features: {env_config.disable_live_features}")
        print(f"  Debug Mode: {env_config.enable_debug_logging}")
        
        return True
        
    except Exception as e:
        print(f"❌ Environment overrides test failed: {e}")
        return False


def test_url_construction():
    """Test URL construction with different configurations."""
    print("\n=== Testing URL Construction ===")
    
    try:
        http_client = get_http_client()
        
        # Test basic URL construction
        test_endpoints = [
            '/api/v1/dashboards',
            '/api/v2/datamodels', 
            '/api/v1/widgets/widget-123'
        ]
        
        print("URL Construction Tests:")
        for endpoint in test_endpoints:
            url = http_client._build_url(endpoint)
            print(f"  {endpoint} → {url}")
        
        # Test with base path override (simulate)
        original_override = Config.SISENSE_BASE_PATH_OVERRIDE
        
        # Simulate different base path configurations
        base_path_tests = ['', 'app', 'tenant1', 'custom/path']
        
        for base_path in base_path_tests:
            # Temporarily set override for testing
            Config.SISENSE_BASE_PATH_OVERRIDE = base_path
            
            # Create new client to pick up changes
            test_client = get_http_client()
            url = test_client._build_url('/api/v1/dashboards')
            print(f"  Base path '{base_path}' → {url}")
        
        # Restore original setting
        Config.SISENSE_BASE_PATH_OVERRIDE = original_override
        
        return True
        
    except Exception as e:
        print(f"❌ URL construction test failed: {e}")
        return False


def main():
    """Run all environment configuration tests."""
    setup_test_logging()
    
    print("🚀 Starting Environment Configuration Tests")
    print(f"Current environment: {Config.FLASK_ENV}")
    print(f"Demo mode: {Config.DEMO_MODE}")
    
    tests = [
        test_backward_compatibility,
        test_environment_detection,
        test_endpoint_configuration,
        test_configuration_validation,
        test_environment_overrides,
        test_url_construction
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test_func.__name__} crashed: {e}")
    
    print(f"\n=== Test Results ===")
    print(f"Passed: {passed}/{total}")
    print(f"Status: {'✅ PASS' if passed == total else '❌ FAIL'}")
    
    if passed == total:
        print("\n🎉 All environment configuration tests passed!")
        print("The implementation maintains backward compatibility while adding new environment-specific features.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check the output above for details.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)