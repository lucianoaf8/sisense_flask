#!/usr/bin/env python3
"""
Environment Configuration Demo

This demonstrates the new environment-specific API configuration features
while maintaining backward compatibility with existing Flask Sisense integration.

To run this demo:
1. pip install python-dotenv requests
2. Configure your .env file with Sisense credentials
3. python environment_config_demo.py
"""

import os
import sys

def show_environment_features():
    """Show the new environment-specific features."""
    print("🌍 Environment-Specific API Configuration Features")
    print("=" * 60)
    
    print("\n1. PLATFORM DETECTION")
    print("   ✅ Automatic Linux vs Windows Sisense platform detection")
    print("   ✅ Cloud vs On-premise deployment identification")
    print("   ✅ API version capability testing (V1 vs V2)")
    print("   ✅ Endpoint availability validation")
    
    print("\n2. CONFIGURABLE BASE PATHS")
    print("   ✅ Standard: /api/v1/dashboards")
    print("   ✅ Tenant-specific: /tenant1/api/v1/dashboards") 
    print("   ✅ Custom routing: /app/api/v1/dashboards")
    print("   ✅ Environment variable override: SISENSE_BASE_PATH_OVERRIDE=app")
    
    print("\n3. ENVIRONMENT-AWARE HEADERS")
    print("   ✅ Platform-specific headers (Linux/Windows)")
    print("   ✅ Cloud deployment headers") 
    print("   ✅ Debug headers for development")
    print("   ✅ User-Agent identification")
    
    print("\n4. DEPLOYMENT TYPE HANDLING")
    print("   ✅ Development: Relative URLs with proxy support")
    print("   ✅ Production: Full URLs with optimized caching")
    print("   ✅ Endpoint testing in dev, disabled in production")
    print("   ✅ Environment-specific timeouts and retry logic")
    
    print("\n5. BACKWARD COMPATIBILITY")
    print("   ✅ Existing configuration continues to work")
    print("   ✅ No breaking changes to API calls")
    print("   ✅ Optional environment-specific features")
    print("   ✅ Graceful fallbacks for missing capabilities")

def show_configuration_examples():
    """Show configuration examples."""
    print("\n📝 Configuration Examples")
    print("=" * 60)
    
    print("\n.env Configuration:")
    print("""
# Basic Configuration (existing)
SISENSE_URL=https://your-sisense-server.com
SISENSE_API_TOKEN=your_api_token_here

# Environment-Specific Configuration (new)
SISENSE_PLATFORM_OVERRIDE=auto          # auto, linux, windows
SISENSE_API_VERSION_OVERRIDE=auto       # auto, v1, v2
SISENSE_BASE_PATH_OVERRIDE=              # empty = /api/, app = /app/api/
SISENSE_DISABLE_LIVE_FEATURES=false     # true for Windows/legacy
SISENSE_DEBUG_MODE=false                 # true for additional logging
""")
    
    print("\nCode Usage Examples:")
    print("""
# Existing code continues to work unchanged
from sisense.dashboards import list_dashboards
dashboards = list_dashboards()

# Environment config provides automatic optimization
from sisense.env_config import get_environment_config
env_config = get_environment_config()

# Automatic platform detection
platform = env_config.detect_platform_capabilities()
print(f"Platform: {platform.platform.value}")  # linux, windows, unknown

# Environment-aware endpoint URLs
endpoint = env_config.get_endpoint_url('dashboards', 'dashboard-123')
print(f"Endpoint: {endpoint}")  # /api/v1/dashboards/dashboard-123 or /app/api/v1/dashboards/dashboard-123

# Configuration summary
summary = env_config.get_configuration_summary()
""")

def show_deployment_scenarios():
    """Show different deployment scenarios."""
    print("\n🚀 Deployment Scenarios")
    print("=" * 60)
    
    scenarios = [
        {
            "name": "Cloud Sisense (Linux v2025.2+)",
            "config": {
                "SISENSE_URL": "https://analytics.company.com",
                "SISENSE_PLATFORM_OVERRIDE": "auto",
                "SISENSE_API_VERSION_OVERRIDE": "auto"
            },
            "result": "Uses V2 APIs, Linux endpoints, cloud headers"
        },
        {
            "name": "On-Premise Windows Legacy",
            "config": {
                "SISENSE_URL": "https://sisense.internal.com",
                "SISENSE_PLATFORM_OVERRIDE": "windows",
                "SISENSE_DISABLE_LIVE_FEATURES": "true"
            },
            "result": "Uses V1 APIs, Windows-compatible endpoints"
        },
        {
            "name": "Tenant-Specific Routing",
            "config": {
                "SISENSE_URL": "https://multi-tenant.sisense.com",
                "SISENSE_BASE_PATH_OVERRIDE": "tenant-123"
            },
            "result": "URLs: /tenant-123/api/v1/dashboards"
        },
        {
            "name": "Development Environment",
            "config": {
                "FLASK_ENV": "development",
                "SISENSE_DEBUG_MODE": "true"
            },
            "result": "Relative URLs, debug headers, endpoint testing enabled"
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. {scenario['name']}")
        print("   Configuration:")
        for key, value in scenario['config'].items():
            print(f"     {key}={value}")
        print(f"   Result: {scenario['result']}")

def show_migration_guide():
    """Show migration guide for existing projects."""
    print("\n📋 Migration Guide")
    print("=" * 60)
    
    print("""
For Existing Projects:
1. ✅ No code changes required - existing code continues to work
2. ✅ Add new environment variables to .env for optimization
3. ✅ Test platform detection in development environment
4. ✅ Enable debug mode for troubleshooting if needed

For New Projects:
1. Copy .env.example to .env
2. Configure basic SISENSE_URL and SISENSE_API_TOKEN  
3. Let auto-detection handle platform-specific optimization
4. Override specific settings only if needed

Troubleshooting:
1. Set SISENSE_DEBUG_MODE=true for detailed logging
2. Check configuration summary: env_config.get_configuration_summary()
3. Validate settings: env_config.validate_environment_configuration()
4. Override platform detection if auto-detection fails
""")

def main():
    """Main demo function."""
    print("🎯 Sisense Flask Environment Configuration Demo")
    print("This showcases the new environment-specific API configuration capabilities.")
    
    show_environment_features()
    show_configuration_examples()
    show_deployment_scenarios()
    show_migration_guide()
    
    print("\n🎉 Summary")
    print("=" * 60)
    print("✅ Environment-specific API configuration implemented")
    print("✅ Platform detection (Linux/Windows, Cloud/On-premise)")
    print("✅ Configurable base paths for tenant-specific routing")
    print("✅ Environment-aware headers and deployment handling")
    print("✅ Full backward compatibility maintained")
    print("✅ Graceful fallbacks and comprehensive validation")
    
    print("\nTo get started:")
    print("1. Update your .env file with the new configuration options")
    print("2. Run Config.print_configuration_summary() to see detected settings")
    print("3. Your existing code will automatically benefit from the optimizations!")

if __name__ == "__main__":
    main()