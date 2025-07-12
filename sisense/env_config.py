"""
Environment-specific configuration for Sisense API integration.

Handles deployment detection, platform-specific routing, tenant configurations,
and environment-aware API endpoint management matching React app patterns.
"""

import os
import re
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

import requests
from config import Config


class DeploymentType(Enum):
    """Sisense deployment types."""
    CLOUD = "cloud"
    ON_PREMISE = "on_premise"
    UNKNOWN = "unknown"


class PlatformType(Enum):
    """Sisense platform types."""
    LINUX = "linux"
    WINDOWS = "windows"
    UNKNOWN = "unknown"


class APIVersion(Enum):
    """Sisense API versions."""
    V1 = "v1"
    V2 = "v2"
    AUTO = "auto"


@dataclass
class EndpointCapabilities:
    """Endpoint capability information."""
    v1_available: bool = True
    v2_available: bool = True
    v2_datamodels_available: bool = True
    preferred_version: APIVersion = APIVersion.V2
    working_v2_endpoint: Optional[str] = None
    platform_specific_endpoints: Dict[str, str] = None
    tested_at: float = 0.0
    test_results: Dict[str, Any] = None

    def __post_init__(self):
        if self.platform_specific_endpoints is None:
            self.platform_specific_endpoints = {}
        if self.test_results is None:
            self.test_results = {}


@dataclass 
class PlatformCapabilities:
    """Platform-specific capabilities and limitations."""
    platform: PlatformType
    deployment: DeploymentType
    version: str = "unknown"
    supports_v2: bool = True
    supports_live_connections: bool = True
    limitations: List[str] = None
    supported_endpoints: List[str] = None
    detected_at: float = 0.0
    detection_method: str = "unknown"

    def __post_init__(self):
        if self.limitations is None:
            self.limitations = []
        if self.supported_endpoints is None:
            self.supported_endpoints = []


class SisenseEnvironmentConfig:
    """
    Environment-specific configuration for Sisense API integration.
    
    Handles platform detection, deployment type identification, and environment-aware
    API configuration matching React app patterns.
    """

    def __init__(self):
        """Initialize environment configuration."""
        self.logger = logging.getLogger(__name__)
        self._capabilities: Optional[EndpointCapabilities] = None
        self._platform: Optional[PlatformCapabilities] = None
        self._environment_profile: Optional[Dict[str, Any]] = None
        
        # Environment overrides (matching React patterns)
        self.platform_override = os.getenv('SISENSE_PLATFORM_OVERRIDE', 'auto').lower()
        self.api_version_override = os.getenv('SISENSE_API_VERSION_OVERRIDE', 'auto').lower()
        self.base_path_override = os.getenv('SISENSE_BASE_PATH_OVERRIDE', '')
        self.disable_live_features = os.getenv('SISENSE_DISABLE_LIVE_FEATURES', 'false').lower() == 'true'
        
        # Environment-specific settings
        self.environment_name = Config.FLASK_ENV
        self.is_development = self.environment_name == 'development'
        self.enable_debug_logging = self.is_development or os.getenv('SISENSE_DEBUG_MODE', 'false').lower() == 'true'
        
        # Cache settings (environment-aware)
        self.capability_cache_duration = 300 if self.is_development else 3600  # 5 min dev, 1 hour prod
        self.platform_cache_duration = 600 if self.is_development else 7200   # 10 min dev, 2 hours prod
        
        self.logger.info(f"Initialized Sisense environment config for {self.environment_name}")

    def get_environment_profile(self) -> Dict[str, Any]:
        """
        Get environment-specific configuration profile.
        
        Returns:
            Dict: Environment configuration profile.
        """
        if self._environment_profile is None:
            self._environment_profile = self._create_environment_profile()
        
        return self._environment_profile

    def _create_environment_profile(self) -> Dict[str, Any]:
        """Create environment-specific configuration profile."""
        base_profile = {
            'name': self.environment_name,
            'is_development': self.is_development,
            'debug_logging': self.enable_debug_logging,
            'base_url': Config.get_sisense_base_url(),
            'request_timeout': Config.REQUEST_TIMEOUT,
            'retry_attempts': Config.REQUEST_RETRIES,
            'ssl_verify': Config.SSL_VERIFY,
        }

        # Environment-specific overrides
        if self.is_development:
            base_profile.update({
                'cache_timeout': 60,  # 1 minute for dev
                'log_level': 'DEBUG',
                'request_timeout': 60,  # Longer timeout for debugging
                'enable_platform_detection': True,
                'enable_endpoint_testing': True,
            })
        else:
            base_profile.update({
                'cache_timeout': 600,  # 10 minutes for production
                'log_level': 'INFO',
                'request_timeout': 30,
                'enable_platform_detection': True,
                'enable_endpoint_testing': False,  # Skip testing in production
            })

        return base_profile

    def detect_platform_capabilities(self, force_refresh: bool = False) -> PlatformCapabilities:
        """
        Detect Sisense platform capabilities (Linux vs Windows, cloud vs on-premise).
        
        Args:
            force_refresh: Force re-detection even if cached.
            
        Returns:
            PlatformCapabilities: Detected platform information.
        """
        # Return cached if available and not expired
        if (self._platform and not force_refresh and 
            time.time() - self._platform.detected_at < self.platform_cache_duration):
            return self._platform

        self.logger.info("Detecting Sisense platform capabilities...")
        
        # Initialize platform info
        platform = PlatformCapabilities(
            platform=PlatformType.UNKNOWN,
            deployment=DeploymentType.UNKNOWN,
            detected_at=time.time()
        )

        try:
            # Check for manual override
            if self.platform_override in ('linux', 'windows'):
                platform.platform = PlatformType.LINUX if self.platform_override == 'linux' else PlatformType.WINDOWS
                platform.detection_method = "manual_override"
                self.logger.info(f"Using manual platform override: {platform.platform.value}")
            else:
                platform = self._detect_platform_by_endpoints(platform)

            # Detect deployment type
            platform = self._detect_deployment_type(platform)
            
            # Set platform-specific capabilities
            self._set_platform_capabilities(platform)
            
            self._platform = platform
            self.logger.info(f"Platform detection complete: {platform.platform.value} {platform.deployment.value}")
            
        except Exception as e:
            self.logger.error(f"Platform detection failed: {e}")
            # Set safe defaults
            platform.platform = PlatformType.LINUX
            platform.deployment = DeploymentType.ON_PREMISE
            platform.detection_method = "fallback_default"
            self._platform = platform

        return self._platform

    def _detect_platform_by_endpoints(self, platform: PlatformCapabilities) -> PlatformCapabilities:
        """Detect platform by testing endpoint availability."""
        platform.detection_method = "endpoint_testing"
        
        # Test Linux-specific V2 endpoints
        linux_endpoints = [
            '/api/v2/datamodels',
            '/api/v2/connections'
        ]
        
        # Test Windows-legacy endpoints
        windows_endpoints = [
            '/api/v1/elasticubes/getElasticubes',
            '/api/v1/connection'
        ]
        
        linux_score = 0
        windows_score = 0
        
        # Test Linux endpoints
        for endpoint in linux_endpoints:
            if self._test_endpoint_availability(endpoint):
                linux_score += 2  # V2 endpoints are strong Linux indicators
                platform.supported_endpoints.append(endpoint)
        
        # Test Windows endpoints  
        for endpoint in windows_endpoints:
            if self._test_endpoint_availability(endpoint):
                windows_score += 1  # V1 endpoints are available on both but more common on Windows
                platform.supported_endpoints.append(endpoint)
        
        # Determine platform based on scores
        if linux_score > windows_score:
            platform.platform = PlatformType.LINUX
            platform.supports_v2 = True
            self.logger.info("Linux platform detected via V2 endpoint availability")
        elif windows_score > 0 and linux_score == 0:
            platform.platform = PlatformType.WINDOWS  
            platform.supports_v2 = False
            platform.limitations.append("V2 Data Models API not available")
            self.logger.info("Windows platform detected via legacy endpoint pattern")
        else:
            platform.platform = PlatformType.UNKNOWN
            self.logger.warn("Could not determine platform via endpoint testing")

        return platform

    def _detect_deployment_type(self, platform: PlatformCapabilities) -> PlatformCapabilities:
        """Detect deployment type (cloud vs on-premise)."""
        base_url = Config.get_sisense_base_url().lower()
        
        # Cloud indicators
        cloud_patterns = [
            r'\.sisense\.com',
            r'\.sisensecloud\.com',
            r'cloud\.sisense\.', 
            r'analytics\..*\.com',
            r'bi\..*\.com',
            r'sisense\..*\.cloud'
        ]
        
        # Check for cloud patterns
        for pattern in cloud_patterns:
            if re.search(pattern, base_url):
                platform.deployment = DeploymentType.CLOUD
                self.logger.info(f"Cloud deployment detected via URL pattern: {pattern}")
                return platform
        
        # Check for localhost/private IP (on-premise indicators)
        if any(indicator in base_url for indicator in ['localhost', '127.0.0.1', '192.168.', '10.', '172.']):
            platform.deployment = DeploymentType.ON_PREMISE
            self.logger.info("On-premise deployment detected via private network indicators")
        else:
            # Default to on-premise for custom domains
            platform.deployment = DeploymentType.ON_PREMISE
            self.logger.info("On-premise deployment assumed for custom domain")

        return platform

    def _set_platform_capabilities(self, platform: PlatformCapabilities):
        """Set platform-specific capabilities and limitations."""
        if platform.platform == PlatformType.WINDOWS:
            platform.limitations.extend([
                "V2 Data Models API not available",
                "Limited live connection discovery", 
                "Some advanced features may not be supported"
            ])
            platform.supported_endpoints.extend([
                '/api/v1/elasticubes/getElasticubes',
                '/api/v1/connection',
                '/api/v1/dashboards',
                '/api/v1/widgets'
            ])
        elif platform.platform == PlatformType.LINUX:
            platform.supported_endpoints.extend([
                '/api/v1/elasticubes/getElasticubes',
                '/api/v2/datamodels',
                '/api/v1/connection',
                '/api/v2/connections',
                '/api/datasources',
                '/api/v1/datasources', 
                '/api/v1/dashboards',
                '/api/v1/widgets'
            ])

    def detect_endpoint_capabilities(self, force_refresh: bool = False) -> EndpointCapabilities:
        """
        Detect API endpoint capabilities and availability.
        
        Args:
            force_refresh: Force re-detection even if cached.
            
        Returns:
            EndpointCapabilities: Detected endpoint capabilities.
        """
        # Return cached if available and not expired
        if (self._capabilities and not force_refresh and
            time.time() - self._capabilities.tested_at < self.capability_cache_duration):
            return self._capabilities

        self.logger.info("Detecting API endpoint capabilities...")
        
        capabilities = EndpointCapabilities(
            tested_at=time.time()
        )

        try:
            # Test V1 API availability
            v1_endpoints = ['/api/v1/dashboards', '/api/v1/elasticubes/getElasticubes']
            capabilities.v1_available = any(self._test_endpoint_availability(ep) for ep in v1_endpoints)
            
            # Test V2 API availability  
            v2_endpoints = ['/api/v2/datamodels', '/api/v2/connections']
            capabilities.v2_available = any(self._test_endpoint_availability(ep) for ep in v2_endpoints)
            
            # Test specific V2 datamodels endpoint
            capabilities.v2_datamodels_available = self._test_endpoint_availability('/api/v2/datamodels')
            
            # Set working V2 endpoint
            for endpoint in ['/api/v2/datamodels', '/api/v2/connections', '/api/v2/elasticubes']:
                if self._test_endpoint_availability(endpoint):
                    capabilities.working_v2_endpoint = endpoint
                    break
            
            # Determine preferred version
            if capabilities.v2_available and not self.disable_live_features:
                capabilities.preferred_version = APIVersion.V2
            else:
                capabilities.preferred_version = APIVersion.V1

            # Set platform-specific endpoint mappings
            capabilities.platform_specific_endpoints = self._get_platform_endpoint_mappings(capabilities)
            
            self._capabilities = capabilities
            self.logger.info(f"Endpoint capabilities detected: V1={capabilities.v1_available}, V2={capabilities.v2_available}")
            
        except Exception as e:
            self.logger.error(f"Endpoint capability detection failed: {e}")
            # Set safe defaults
            capabilities.v1_available = True
            capabilities.v2_available = False
            capabilities.preferred_version = APIVersion.V1
            self._capabilities = capabilities

        return self._capabilities

    def _get_platform_endpoint_mappings(self, capabilities: EndpointCapabilities) -> Dict[str, str]:
        """Get platform-specific endpoint mappings."""
        # Base mappings (Linux/modern deployments)
        mappings = {
            'connections': '/api/v2/connections',
            'datamodels': '/api/v2/datamodels',
            'dashboards': '/api/v1/dashboards', 
            'widgets': '/api/v1/widgets',
            'authentication': '/api/v1/authentication/login',
            'user_info': '/api/v1/authentication/me'
        }

        # Fallback for Windows/legacy deployments
        if not capabilities.v2_available:
            mappings.update({
                'connections': '/api/v1/connection',
                'datamodels': '/api/v1/elasticubes/getElasticubes'
            })

        return mappings

    def _test_endpoint_availability(self, endpoint: str, timeout: int = 10) -> bool:
        """Test if an API endpoint is available."""
        if not self.get_environment_profile().get('enable_endpoint_testing', True):
            # Skip testing in production unless explicitly enabled
            return True

        try:
            url = f"{Config.get_sisense_base_url()}{endpoint}"
            
            # Use basic auth headers for testing
            headers = {'Content-Type': 'application/json'}
            if Config.SISENSE_API_TOKEN:
                headers['Authorization'] = f'Bearer {Config.SISENSE_API_TOKEN}'
            
            response = requests.get(
                url,
                headers=headers,
                timeout=timeout,
                verify=Config.SSL_VERIFY
            )
            
            # Consider 200, 401, 403 as "available" (endpoint exists)
            # 404, 500 as "not available" 
            available = response.status_code in [200, 401, 403]
            self.logger.debug(f"Endpoint {endpoint}: {response.status_code} ({'available' if available else 'not available'})")
            return available
            
        except Exception as e:
            self.logger.debug(f"Endpoint {endpoint} test failed: {e}")
            return False

    def get_api_base_path(self, api_version: str = "v1") -> str:
        """
        Get the base path for API requests with environment-specific handling.
        
        Args:
            api_version: API version (v1, v2).
            
        Returns:
            str: Base API path (e.g., '/api/v1/', '/app/api/v1/').
        """
        # Check for manual override
        if self.base_path_override:
            base_path = self.base_path_override.strip('/')
            return f"/{base_path}/api/{api_version}/"
        
        # Default to standard path
        return f"/api/{api_version}/"

    def get_endpoint_url(self, resource_type: str, endpoint_suffix: str = "") -> str:
        """
        Get full endpoint URL for a resource type with environment-aware routing.
        
        Args:
            resource_type: Type of resource (connections, datamodels, etc.).
            endpoint_suffix: Additional path suffix.
            
        Returns:
            str: Full endpoint URL.
        """
        capabilities = self.detect_endpoint_capabilities()
        endpoint = capabilities.platform_specific_endpoints.get(resource_type)
        
        if not endpoint:
            # Fallback to default pattern
            api_version = "v2" if capabilities.v2_available else "v1"
            endpoint = f"/api/{api_version}/{resource_type}"
        
        # Add suffix if provided
        if endpoint_suffix:
            endpoint = f"{endpoint.rstrip('/')}/{endpoint_suffix.lstrip('/')}"
        
        return endpoint

    def get_platform_headers(self) -> Dict[str, str]:
        """
        Get platform-specific headers for API requests.
        
        Returns:
            Dict: Platform-specific headers.
        """
        headers = {}
        
        # Add deployment-specific headers
        platform = self.detect_platform_capabilities()
        
        if platform.deployment == DeploymentType.CLOUD:
            # Cloud deployments might need specific headers
            headers.update({
                'X-Sisense-Environment': 'cloud',
                'User-Agent': f'SisenseFlaskClient/1.0 ({platform.platform.value})'
            })
        
        # Add debug headers in development
        if self.is_development and self.enable_debug_logging:
            headers.update({
                'X-Debug-Mode': 'true',
                'X-Environment': self.environment_name
            })
        
        return headers

    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get comprehensive configuration summary for debugging."""
        try:
            platform = self.detect_platform_capabilities()
            capabilities = self.detect_endpoint_capabilities()
            profile = self.get_environment_profile()
            
            return {
                'environment': {
                    'name': profile['name'],
                    'is_development': profile['is_development'],
                    'debug_logging': profile['debug_logging'],
                    'base_url': profile['base_url']
                },
                'platform': {
                    'type': platform.platform.value,
                    'deployment': platform.deployment.value,
                    'supports_v2': platform.supports_v2,
                    'detection_method': platform.detection_method,
                    'limitations': platform.limitations
                },
                'capabilities': {
                    'v1_available': capabilities.v1_available,
                    'v2_available': capabilities.v2_available,
                    'preferred_version': capabilities.preferred_version.value,
                    'working_v2_endpoint': capabilities.working_v2_endpoint,
                    'endpoint_mappings': capabilities.platform_specific_endpoints
                },
                'overrides': {
                    'platform_override': self.platform_override,
                    'api_version_override': self.api_version_override,
                    'base_path_override': self.base_path_override,
                    'disable_live_features': self.disable_live_features
                }
            }
        except Exception as e:
            return {'error': f'Failed to generate configuration summary: {e}'}

    def validate_environment_configuration(self) -> List[str]:
        """
        Validate environment configuration and return any issues.
        
        Returns:
            List[str]: List of configuration issues or warnings.
        """
        issues = []
        
        try:
            # Test basic connectivity
            if not self._test_endpoint_availability('/api/v1/dashboards'):
                issues.append("Cannot connect to Sisense API - check URL and authentication")
            
            # Validate platform detection
            platform = self.detect_platform_capabilities()
            if platform.platform == PlatformType.UNKNOWN:
                issues.append("Could not detect Sisense platform type - may affect API compatibility")
            
            # Validate capabilities
            capabilities = self.detect_endpoint_capabilities()
            if not capabilities.v1_available and not capabilities.v2_available:
                issues.append("No working API endpoints detected - check Sisense version and configuration")
            
            # Environment-specific validations
            if self.is_development:
                if not self.enable_debug_logging:
                    issues.append("Debug logging is disabled in development environment")
            else:
                if Config.FLASK_DEBUG:
                    issues.append("Flask debug mode is enabled in production environment")
            
        except Exception as e:
            issues.append(f"Environment validation failed: {e}")
        
        return issues


# Global environment configuration instance
_env_config = None


def get_environment_config() -> SisenseEnvironmentConfig:
    """
    Get singleton environment configuration instance.
    
    Returns:
        SisenseEnvironmentConfig: Environment configuration instance.
    """
    global _env_config
    if _env_config is None:
        _env_config = SisenseEnvironmentConfig()
    return _env_config