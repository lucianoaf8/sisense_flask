#!/usr/bin/env python3
"""
API Health Check System for Sisense Integration.

Provides ongoing validation and monitoring of critical API endpoints
with health status reporting and alerting capabilities.
"""

import json
import logging
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import requests

from sisense.config import Config
from sisense.env_config import get_environment_config
from sisense.auth import get_auth_headers


class HealthStatus(Enum):
    """Health check status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    endpoint: str
    status: HealthStatus
    response_time_ms: float
    status_code: int
    error_message: str = ""
    checked_at: str = ""
    
    def __post_init__(self):
        if not self.checked_at:
            self.checked_at = datetime.now().isoformat()


@dataclass
class HealthMetrics:
    """Health metrics for monitoring."""
    endpoint: str
    total_checks: int
    successful_checks: int
    average_response_time: float
    uptime_percentage: float
    last_success: str = ""
    last_failure: str = ""
    consecutive_failures: int = 0


class SisenseHealthChecker:
    """
    Health check system for Sisense API endpoints.
    
    Monitors critical endpoints and provides health status reporting
    for operational monitoring and alerting.
    """

    def __init__(self):
        """Initialize the health checker."""
        self.logger = logging.getLogger(__name__)
        self.env_config = get_environment_config()
        self.base_url = Config.get_sisense_base_url()
        
        # Health check configuration
        self.timeout = 10  # Shorter timeout for health checks
        self.critical_endpoints = self._define_critical_endpoints()
        self.health_history: Dict[str, List[HealthCheckResult]] = {}
        self.metrics: Dict[str, HealthMetrics] = {}
        
        # Health thresholds
        self.healthy_response_time_ms = 2000  # 2 seconds
        self.degraded_response_time_ms = 5000  # 5 seconds
        self.max_consecutive_failures = 3
        
        self.logger.info("Initialized Sisense health checker")

    def _define_critical_endpoints(self) -> List[str]:
        """Define critical endpoints for health monitoring."""
        critical = [
            "/api/v1/dashboards",      # Core dashboard functionality
            "/api/v2/connections",     # Data connections (if available)
            "/api/v1/authentication/me"  # Authentication validation
        ]
        
        # Add platform-specific endpoints
        platform = self.env_config.detect_platform_capabilities()
        
        if platform.supports_v2:
            critical.append("/api/v2/datamodels")
        else:
            critical.append("/api/v1/elasticubes/getElasticubes")
        
        return critical

    def check_endpoint_health(self, endpoint: str) -> HealthCheckResult:
        """
        Check health of a single endpoint.
        
        Args:
            endpoint: API endpoint path to check.
            
        Returns:
            HealthCheckResult: Health check result.
        """
        url = f"{self.base_url}{endpoint}"
        
        # Prepare headers
        headers = {'Content-Type': 'application/json'}
        try:
            auth_headers = get_auth_headers()
            headers.update(auth_headers)
        except Exception as e:
            return HealthCheckResult(
                endpoint=endpoint,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=0,
                status_code=0,
                error_message=f"Authentication failed: {str(e)}"
            )
        
        # Add environment headers
        env_headers = self.env_config.get_platform_headers()
        headers.update(env_headers)
        
        start_time = time.time()
        
        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=self.timeout,
                verify=Config.SSL_VERIFY
            )
            
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            
            # Determine health status
            if response.status_code == 200:
                if response_time_ms <= self.healthy_response_time_ms:
                    status = HealthStatus.HEALTHY
                elif response_time_ms <= self.degraded_response_time_ms:
                    status = HealthStatus.DEGRADED
                else:
                    status = HealthStatus.UNHEALTHY
                error_message = ""
            elif response.status_code == 401:
                status = HealthStatus.UNHEALTHY
                error_message = "Authentication failed"
            elif response.status_code == 404:
                status = HealthStatus.UNHEALTHY
                error_message = "Endpoint not found"
            else:
                status = HealthStatus.DEGRADED
                error_message = f"HTTP {response.status_code}"
            
            return HealthCheckResult(
                endpoint=endpoint,
                status=status,
                response_time_ms=response_time_ms,
                status_code=response.status_code,
                error_message=error_message
            )
            
        except requests.exceptions.Timeout:
            return HealthCheckResult(
                endpoint=endpoint,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=self.timeout * 1000,
                status_code=0,
                error_message=f"Timeout after {self.timeout}s"
            )
            
        except requests.exceptions.RequestException as e:
            return HealthCheckResult(
                endpoint=endpoint,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=0,
                status_code=0,
                error_message=f"Request failed: {str(e)}"
            )

    def check_all_critical_endpoints(self) -> Dict[str, HealthCheckResult]:
        """
        Check health of all critical endpoints.
        
        Returns:
            Dict: Health check results for all critical endpoints.
        """
        results = {}
        
        for endpoint in self.critical_endpoints:
            result = self.check_endpoint_health(endpoint)
            results[endpoint] = result
            
            # Update history
            if endpoint not in self.health_history:
                self.health_history[endpoint] = []
            
            self.health_history[endpoint].append(result)
            
            # Limit history size (keep last 100 checks)
            if len(self.health_history[endpoint]) > 100:
                self.health_history[endpoint] = self.health_history[endpoint][-100:]
            
            # Update metrics
            self._update_metrics(endpoint, result)
            
            # Log result
            if result.status == HealthStatus.HEALTHY:
                self.logger.debug(f"✅ {endpoint} - {result.response_time_ms:.1f}ms")
            elif result.status == HealthStatus.DEGRADED:
                self.logger.warning(f"⚠️  {endpoint} - DEGRADED: {result.response_time_ms:.1f}ms")
            else:
                self.logger.error(f"❌ {endpoint} - UNHEALTHY: {result.error_message}")
        
        return results

    def _update_metrics(self, endpoint: str, result: HealthCheckResult):
        """Update health metrics for an endpoint."""
        if endpoint not in self.metrics:
            self.metrics[endpoint] = HealthMetrics(
                endpoint=endpoint,
                total_checks=0,
                successful_checks=0,
                average_response_time=0,
                uptime_percentage=0,
                consecutive_failures=0
            )
        
        metrics = self.metrics[endpoint]
        metrics.total_checks += 1
        
        if result.status == HealthStatus.HEALTHY:
            metrics.successful_checks += 1
            metrics.last_success = result.checked_at
            metrics.consecutive_failures = 0
        else:
            metrics.last_failure = result.checked_at
            metrics.consecutive_failures += 1
        
        # Update average response time
        history = self.health_history[endpoint]
        response_times = [r.response_time_ms for r in history if r.response_time_ms > 0]
        metrics.average_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Update uptime percentage
        metrics.uptime_percentage = (metrics.successful_checks / metrics.total_checks) * 100

    def get_overall_health_status(self) -> HealthStatus:
        """
        Get overall system health status.
        
        Returns:
            HealthStatus: Overall health status based on critical endpoints.
        """
        if not self.metrics:
            return HealthStatus.UNKNOWN
        
        healthy_count = 0
        degraded_count = 0
        unhealthy_count = 0
        
        for endpoint in self.critical_endpoints:
            if endpoint not in self.health_history or not self.health_history[endpoint]:
                unhealthy_count += 1
                continue
            
            latest_result = self.health_history[endpoint][-1]
            
            if latest_result.status == HealthStatus.HEALTHY:
                healthy_count += 1
            elif latest_result.status == HealthStatus.DEGRADED:
                degraded_count += 1
            else:
                unhealthy_count += 1
        
        total = len(self.critical_endpoints)
        
        # Overall status logic
        if unhealthy_count == 0 and degraded_count == 0:
            return HealthStatus.HEALTHY
        elif unhealthy_count == 0 and degraded_count <= total // 2:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.UNHEALTHY

    def get_health_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive health summary.
        
        Returns:
            Dict: Health summary with status, metrics, and recent results.
        """
        overall_status = self.get_overall_health_status()
        
        # Recent results
        recent_results = {}
        for endpoint in self.critical_endpoints:
            if endpoint in self.health_history and self.health_history[endpoint]:
                recent_results[endpoint] = asdict(self.health_history[endpoint][-1])
        
        # Metrics summary
        metrics_summary = {}
        for endpoint, metrics in self.metrics.items():
            metrics_summary[endpoint] = asdict(metrics)
        
        return {
            "overall_status": overall_status.value,
            "checked_at": datetime.now().isoformat(),
            "critical_endpoints": self.critical_endpoints,
            "recent_results": recent_results,
            "metrics": metrics_summary,
            "environment": {
                "base_url": self.base_url,
                "platform": self.env_config.detect_platform_capabilities().platform.value,
            }
        }

    def get_alerts(self) -> List[Dict[str, Any]]:
        """
        Get active alerts based on health status.
        
        Returns:
            List: Active alerts requiring attention.
        """
        alerts = []
        
        for endpoint, metrics in self.metrics.items():
            # Consecutive failure alert
            if metrics.consecutive_failures >= self.max_consecutive_failures:
                alerts.append({
                    "type": "consecutive_failures",
                    "severity": "critical",
                    "endpoint": endpoint,
                    "message": f"{endpoint} has failed {metrics.consecutive_failures} consecutive times",
                    "last_failure": metrics.last_failure
                })
            
            # Low uptime alert
            if metrics.total_checks >= 10 and metrics.uptime_percentage < 80:
                alerts.append({
                    "type": "low_uptime",
                    "severity": "warning",
                    "endpoint": endpoint,
                    "message": f"{endpoint} uptime is {metrics.uptime_percentage:.1f}% (below 80%)",
                    "uptime_percentage": metrics.uptime_percentage
                })
            
            # Slow response alert
            if metrics.average_response_time > self.degraded_response_time_ms:
                alerts.append({
                    "type": "slow_response",
                    "severity": "warning",
                    "endpoint": endpoint,
                    "message": f"{endpoint} average response time is {metrics.average_response_time:.1f}ms",
                    "average_response_time": metrics.average_response_time
                })
        
        return alerts

    def run_health_check_cycle(self) -> Dict[str, Any]:
        """
        Run a complete health check cycle.
        
        Returns:
            Dict: Complete health check results and summary.
        """
        self.logger.info("Running health check cycle...")
        
        # Check all critical endpoints
        results = self.check_all_critical_endpoints()
        
        # Get summary and alerts
        summary = self.get_health_summary()
        alerts = self.get_alerts()
        
        # Log summary
        overall_status = summary['overall_status']
        if overall_status == "healthy":
            self.logger.info("✅ System health: HEALTHY")
        elif overall_status == "degraded":
            self.logger.warning("⚠️  System health: DEGRADED")
        else:
            self.logger.error("❌ System health: UNHEALTHY")
        
        # Log alerts
        if alerts:
            self.logger.warning(f"🚨 {len(alerts)} active alerts")
            for alert in alerts:
                self.logger.warning(f"  - {alert['severity'].upper()}: {alert['message']}")
        
        return {
            "summary": summary,
            "alerts": alerts,
            "detailed_results": {endpoint: asdict(result) for endpoint, result in results.items()}
        }

    def save_health_report(self, filename: str = None) -> str:
        """
        Save health check report to file.
        
        Args:
            filename: Optional filename. If not provided, generates timestamp-based name.
            
        Returns:
            str: Filename of saved report.
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"health_report_{timestamp}.json"
        
        report = self.run_health_check_cycle()
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"Health report saved to {filename}")
        return filename

    def continuous_monitoring(self, interval_seconds: int = 60, duration_minutes: int = 60):
        """
        Run continuous health monitoring.
        
        Args:
            interval_seconds: Time between health checks.
            duration_minutes: Total monitoring duration.
        """
        self.logger.info(f"Starting continuous monitoring (interval: {interval_seconds}s, duration: {duration_minutes}m)")
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        check_count = 0
        
        while time.time() < end_time:
            check_count += 1
            self.logger.info(f"Health check #{check_count}")
            
            try:
                self.run_health_check_cycle()
            except Exception as e:
                self.logger.error(f"Health check failed: {e}")
            
            # Sleep until next check
            time.sleep(interval_seconds)
        
        self.logger.info(f"Continuous monitoring completed after {check_count} checks")
        
        # Save final report
        return self.save_health_report()


def create_health_endpoint_for_flask():
    """
    Create a Flask endpoint for health checks.
    
    Returns:
        function: Flask route function for health checks.
    """
    def health_check():
        """Flask health check endpoint."""
        checker = SisenseHealthChecker()
        
        try:
            summary = checker.get_health_summary()
            alerts = checker.get_alerts()
            
            # Determine HTTP status code
            overall_status = summary['overall_status']
            if overall_status == "healthy":
                status_code = 200
            elif overall_status == "degraded":
                status_code = 207  # Multi-Status
            else:
                status_code = 503  # Service Unavailable
            
            return {
                "status": overall_status,
                "checked_at": summary['checked_at'],
                "alerts_count": len(alerts),
                "endpoints": summary['recent_results']
            }, status_code
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "checked_at": datetime.now().isoformat()
            }, 500
    
    return health_check


def main():
    """Main function for standalone health checking."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Sisense API Health Checker")
    parser.add_argument("--continuous", action="store_true", help="Run continuous monitoring")
    parser.add_argument("--interval", type=int, default=60, help="Check interval in seconds")
    parser.add_argument("--duration", type=int, default=60, help="Monitoring duration in minutes")
    parser.add_argument("--output", type=str, help="Output filename for health report")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("💚 Sisense API Health Checker")
    print("=" * 40)
    
    # Check configuration
    if not Config.has_valid_authentication():
        print("❌ No valid authentication configured")
        return False
    
    print(f"🎯 Monitoring: {Config.get_sisense_base_url()}")
    
    # Run health checks
    checker = SisenseHealthChecker()
    
    try:
        if args.continuous:
            print(f"🔄 Starting continuous monitoring ({args.interval}s intervals, {args.duration}m duration)")
            filename = checker.continuous_monitoring(args.interval, args.duration)
            print(f"📁 Final report saved to: {filename}")
        else:
            print("🏃 Running single health check...")
            filename = checker.save_health_report(args.output)
            
            # Print summary
            summary = checker.get_health_summary()
            alerts = checker.get_alerts()
            
            print(f"\n📊 Health Status: {summary['overall_status'].upper()}")
            print(f"🔍 Endpoints Checked: {len(summary['critical_endpoints'])}")
            print(f"🚨 Active Alerts: {len(alerts)}")
            print(f"📁 Report Saved: {filename}")
        
        return True
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)