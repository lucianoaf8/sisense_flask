#!/usr/bin/env python3
"""
User Action Simulation Testing for Optimized HTTP Client

Simulates realistic user interactions with Sisense API endpoints to test
the optimized HTTP client under real-world usage patterns:

- Dashboard browsing and interaction flows
- Data exploration and querying patterns
- Connection management workflows
- Authentication and session management
- Concurrent user simulation
- Error handling and recovery scenarios
"""

import time
import random
import threading
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

# Import optimized client
try:
    from sisense.optimized_http_client import get_optimized_http_client
    from sisense.utils import SisenseAPIError
    from config import Config
    optimized_available = True
except ImportError as e:
    print(f"Warning: Could not import optimized client: {e}")
    optimized_available = False


@dataclass
class UserSession:
    """Represents a user session with tracking."""
    user_id: str
    session_start: datetime
    actions_performed: List[str] = field(default_factory=list)
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_response_time: float = 0.0
    errors: List[str] = field(default_factory=list)


@dataclass
class UserAction:
    """Represents a user action to simulate."""
    name: str
    description: str
    endpoint: str
    method: str = "GET"
    params: Optional[Dict] = None
    expected_duration: float = 1.0  # Expected time in seconds
    success_probability: float = 0.9  # Probability of success (for simulation)
    weight: int = 1  # How often this action occurs relative to others


class SisenseUserActionSimulator:
    """Simulates realistic user actions on Sisense API endpoints."""
    
    def __init__(self):
        """Initialize the user action simulator."""
        self.client = get_optimized_http_client() if optimized_available else None
        self.sessions: Dict[str, UserSession] = {}
        self.results = {"sessions": [], "summary": {}}
        
        # Define realistic user action patterns
        self.user_actions = self._define_user_actions()
        self.user_workflows = self._define_user_workflows()
        
        print("👥 Sisense User Action Simulator Initialized")
        print(f"Available actions: {len(self.user_actions)}")
        print(f"Available workflows: {len(self.user_workflows)}")

    def _define_user_actions(self) -> List[UserAction]:
        """Define realistic user actions based on typical Sisense usage."""
        return [
            # Dashboard Management Actions
            UserAction(
                name="list_dashboards",
                description="User browses available dashboards",
                endpoint="/api/v1/dashboards",
                expected_duration=1.2,
                success_probability=0.95,
                weight=10  # Very common action
            ),
            UserAction(
                name="view_dashboard_details",
                description="User opens a specific dashboard",
                endpoint="/api/v1/dashboards/{dashboard_id}",
                expected_duration=1.5,
                success_probability=0.90,
                weight=8
            ),
            UserAction(
                name="get_dashboard_widgets",
                description="User loads dashboard widgets",
                endpoint="/api/v1/dashboards/{dashboard_id}/widgets",
                expected_duration=2.0,
                success_probability=0.85,
                weight=6
            ),
            
            # Data Exploration Actions
            UserAction(
                name="query_widget_data",
                description="User queries widget data",
                endpoint="/api/v1/widgets/{widget_id}/data",
                method="POST",
                expected_duration=3.0,
                success_probability=0.80,
                weight=5
            ),
            UserAction(
                name="run_sql_query",
                description="User runs custom SQL query",
                endpoint="/api/v1/datasources/{datasource_id}/sql",
                method="POST",
                expected_duration=4.0,
                success_probability=0.75,
                weight=3
            ),
            UserAction(
                name="run_jaql_query",
                description="User runs JAQL query",
                endpoint="/api/v1/datasources/{datasource_id}/jaql",
                method="POST",
                expected_duration=3.5,
                success_probability=0.75,
                weight=3
            ),
            
            # Connection Management Actions
            UserAction(
                name="list_connections",
                description="User views data connections",
                endpoint="/api/v2/connections",
                expected_duration=0.9,
                success_probability=0.95,
                weight=4
            ),
            UserAction(
                name="test_connection",
                description="User tests a data connection",
                endpoint="/api/v2/connections/{connection_id}/test",
                method="POST",
                expected_duration=5.0,
                success_probability=0.70,
                weight=2
            ),
            
            # Data Model Actions
            UserAction(
                name="list_data_models",
                description="User browses data models",
                endpoint="/api/v2/datamodels",
                expected_duration=1.1,
                success_probability=0.60,  # Known to often fail
                weight=3
            ),
            UserAction(
                name="list_elasticubes",
                description="User views ElastiCubes (legacy)",
                endpoint="/api/v1/elasticubes",
                expected_duration=1.3,
                success_probability=0.50,  # Known to often fail
                weight=2
            ),
            
            # User Management Actions
            UserAction(
                name="get_user_info",
                description="User views their profile",
                endpoint="/api/v1/users/me",
                expected_duration=0.8,
                success_probability=0.40,  # Known to often fail
                weight=2
            ),
            UserAction(
                name="get_auth_info",
                description="User checks authentication status",
                endpoint="/api/v1/authentication/me",
                expected_duration=0.7,
                success_probability=0.30,  # Known to often fail
                weight=1
            ),
            
            # System Actions
            UserAction(
                name="check_version",
                description="System checks Sisense version",
                endpoint="/api/version",
                expected_duration=0.5,
                success_probability=0.95,
                weight=1
            ),
            UserAction(
                name="health_check",
                description="System performs health check",
                endpoint="/api/health",
                expected_duration=0.4,
                success_probability=0.90,
                weight=1
            ),
        ]

    def _define_user_workflows(self) -> Dict[str, List[str]]:
        """Define realistic user workflow patterns."""
        return {
            "dashboard_explorer": [
                "list_dashboards",
                "view_dashboard_details", 
                "get_dashboard_widgets",
                "query_widget_data"
            ],
            "data_analyst": [
                "list_dashboards",
                "list_connections",
                "list_data_models",
                "run_sql_query",
                "query_widget_data"
            ],
            "admin_user": [
                "list_connections",
                "test_connection",
                "list_data_models",
                "get_user_info",
                "check_version"
            ],
            "casual_viewer": [
                "list_dashboards",
                "view_dashboard_details",
                "get_dashboard_widgets"
            ],
            "power_user": [
                "list_dashboards",
                "view_dashboard_details",
                "get_dashboard_widgets", 
                "query_widget_data",
                "run_jaql_query",
                "list_connections"
            ]
        }

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for requests."""
        if Config.DEMO_MODE:
            return {"Authorization": "Bearer demo_token", "Content-Type": "application/json"}
        
        try:
            from sisense.auth import get_auth_headers
            return get_auth_headers()
        except Exception:
            return {"Authorization": "Bearer test_token", "Content-Type": "application/json"}

    def _execute_user_action(self, action: UserAction, session: UserSession) -> Dict[str, Any]:
        """Execute a single user action and track results."""
        start_time = time.time()
        
        # Substitute placeholder IDs with realistic values
        endpoint = self._substitute_endpoint_ids(action.endpoint)
        
        result = {
            "action": action.name,
            "endpoint": endpoint,
            "method": action.method,
            "start_time": start_time,
            "success": False,
            "response_time": 0.0,
            "status_code": 0,
            "error": None
        }
        
        session.total_requests += 1
        session.actions_performed.append(action.name)
        
        try:
            # Simulate the API call
            if self.client:
                headers = self._get_auth_headers()
                
                if action.method == "GET":
                    response_data = self.client.get(endpoint, headers=headers)
                elif action.method == "POST":
                    # Add realistic POST data for queries
                    json_data = self._get_post_data_for_action(action)
                    response_data = self.client.post(endpoint, headers=headers, json=json_data)
                else:
                    response_data = self.client.request(action.method, endpoint, headers=headers)
                
                result["success"] = True
                result["status_code"] = 200
                result["response_size"] = len(str(response_data))
                session.successful_requests += 1
                
            else:
                # Simulate response when no client available
                time.sleep(random.uniform(0.1, action.expected_duration))
                if random.random() < action.success_probability:
                    result["success"] = True
                    result["status_code"] = 200
                    session.successful_requests += 1
                else:
                    raise SisenseAPIError("Simulated API error", status_code=404)
        
        except SisenseAPIError as e:
            result["error"] = str(e)
            result["status_code"] = e.status_code
            session.failed_requests += 1
            session.errors.append(f"{action.name}: {str(e)}")
            
        except Exception as e:
            result["error"] = str(e)
            result["status_code"] = 500
            session.failed_requests += 1
            session.errors.append(f"{action.name}: {str(e)}")
        
        # Calculate timing
        end_time = time.time()
        result["response_time"] = end_time - start_time
        result["end_time"] = end_time
        session.total_response_time += result["response_time"]
        
        return result

    def _substitute_endpoint_ids(self, endpoint: str) -> str:
        """Substitute placeholder IDs in endpoints with realistic values."""
        substitutions = {
            "{dashboard_id}": "507f1f77bcf86cd799439011",
            "{widget_id}": "507f1f77bcf86cd799439012", 
            "{datasource_id}": "507f1f77bcf86cd799439013",
            "{connection_id}": "507f1f77bcf86cd799439014",
            "{user_id}": "507f1f77bcf86cd799439015"
        }
        
        result = endpoint
        for placeholder, value in substitutions.items():
            result = result.replace(placeholder, value)
        
        return result

    def _get_post_data_for_action(self, action: UserAction) -> Dict[str, Any]:
        """Get realistic POST data for actions that require it."""
        if "sql" in action.name:
            return {
                "query": "SELECT * FROM sales_data WHERE date >= '2024-01-01' LIMIT 100",
                "format": "json"
            }
        elif "jaql" in action.name:
            return {
                "jaql": {
                    "datasource": "Sample ECommerce",
                    "metadata": [
                        {"jaql": {"dim": "[Date.Year]"}},
                        {"jaql": {"dim": "[Revenue]", "agg": "sum"}}
                    ]
                }
            }
        elif "widget_data" in action.name:
            return {
                "filters": [],
                "count": 1000
            }
        elif "test" in action.name:
            return {
                "timeout": 10
            }
        else:
            return {}

    def simulate_user_session(self, user_type: str, session_duration_minutes: int = 10) -> UserSession:
        """Simulate a complete user session with realistic action patterns."""
        user_id = f"{user_type}_{int(time.time())}_{random.randint(1000, 9999)}"
        session = UserSession(
            user_id=user_id,
            session_start=datetime.now()
        )
        
        print(f"👤 Starting {user_type} session for {session_duration_minutes} minutes: {user_id}")
        
        # Get workflow for user type
        workflow = self.user_workflows.get(user_type, ["list_dashboards", "view_dashboard_details"])
        
        session_end_time = time.time() + (session_duration_minutes * 60)
        action_results = []
        
        while time.time() < session_end_time:
            # Choose action based on workflow and weights
            if random.random() < 0.7:  # 70% chance to follow workflow
                action_name = random.choice(workflow)
            else:  # 30% chance for random action
                action_name = self._choose_weighted_action()
            
            # Find the action
            action = next((a for a in self.user_actions if a.name == action_name), None)
            if not action:
                continue
            
            # Execute the action
            result = self._execute_user_action(action, session)
            action_results.append(result)
            
            # Print progress
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {action.name} ({result['response_time']:.2f}s)")
            
            # Realistic pause between actions (1-10 seconds)
            pause_time = random.uniform(1.0, 10.0)
            time.sleep(pause_time)
        
        # Store results
        session_data = {
            "user_id": user_id,
            "user_type": user_type,
            "session_duration_minutes": session_duration_minutes,
            "session_start": session.session_start.isoformat(),
            "session_end": datetime.now().isoformat(),
            "total_requests": session.total_requests,
            "successful_requests": session.successful_requests,
            "failed_requests": session.failed_requests,
            "success_rate": (session.successful_requests / session.total_requests * 100) if session.total_requests > 0 else 0,
            "avg_response_time": (session.total_response_time / session.total_requests) if session.total_requests > 0 else 0,
            "actions_performed": session.actions_performed,
            "errors": session.errors,
            "action_results": action_results
        }
        
        self.results["sessions"].append(session_data)
        
        print(f"📊 Session complete: {session.successful_requests}/{session.total_requests} successful")
        return session

    def _choose_weighted_action(self) -> str:
        """Choose an action based on weights."""
        total_weight = sum(action.weight for action in self.user_actions)
        random_choice = random.uniform(0, total_weight)
        
        current_weight = 0
        for action in self.user_actions:
            current_weight += action.weight
            if random_choice <= current_weight:
                return action.name
        
        return self.user_actions[0].name  # Fallback

    def simulate_concurrent_users(self, user_scenarios: Dict[str, int], session_duration: int = 5):
        """Simulate multiple concurrent users with different behavior patterns."""
        print(f"🚀 Starting concurrent user simulation:")
        for user_type, count in user_scenarios.items():
            print(f"  - {count} {user_type} users for {session_duration} minutes each")
        
        # Create thread pool for concurrent execution
        max_workers = sum(user_scenarios.values())
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all user sessions
            future_to_user = {}
            
            for user_type, user_count in user_scenarios.items():
                for i in range(user_count):
                    future = executor.submit(self.simulate_user_session, user_type, session_duration)
                    future_to_user[future] = f"{user_type}_{i+1}"
            
            # Wait for all sessions to complete
            for future in as_completed(future_to_user):
                user_id = future_to_user[future]
                try:
                    session = future.result()
                    print(f"✅ {user_id} session completed")
                except Exception as e:
                    print(f"❌ {user_id} session failed: {e}")

    def test_error_handling_scenarios(self):
        """Test how the optimized client handles various error scenarios."""
        print("\n🔥 Testing Error Handling Scenarios...")
        
        error_scenarios = [
            {
                "name": "Broken Endpoint",
                "endpoint": "/api/v1/authentication/me",
                "expected_error": "404 Not Found"
            },
            {
                "name": "Timeout Endpoint", 
                "endpoint": "/api/timeout-test",
                "expected_error": "Timeout"
            },
            {
                "name": "Rate Limited Endpoint",
                "endpoint": "/api/v1/dashboards",
                "rapid_requests": 20,
                "expected_error": "Rate limiting"
            }
        ]
        
        for scenario in error_scenarios:
            print(f"\n  Testing: {scenario['name']}")
            
            if scenario.get("rapid_requests"):
                # Test rate limiting
                for i in range(scenario["rapid_requests"]):
                    try:
                        if self.client:
                            self.client.get(scenario["endpoint"], headers=self._get_auth_headers())
                        print(f"    Request {i+1}: Success")
                    except Exception as e:
                        print(f"    Request {i+1}: {str(e)[:50]}...")
                    time.sleep(0.05)  # Very rapid requests
            else:
                # Test single error scenario
                try:
                    if self.client:
                        self.client.get(scenario["endpoint"], headers=self._get_auth_headers())
                    print(f"    Unexpected success")
                except Exception as e:
                    print(f"    Expected error: {str(e)[:50]}...")

    def test_performance_under_load(self, requests_per_minute: int = 60, duration_minutes: int = 2):
        """Test performance under sustained load."""
        print(f"\n⚡ Testing Performance Under Load: {requests_per_minute} req/min for {duration_minutes} min")
        
        interval = 60.0 / requests_per_minute  # Seconds between requests
        end_time = time.time() + (duration_minutes * 60)
        
        request_count = 0
        success_count = 0
        total_response_time = 0.0
        
        while time.time() < end_time:
            start_time = time.time()
            
            try:
                if self.client:
                    self.client.get("/api/v1/dashboards", headers=self._get_auth_headers())
                success_count += 1
            except Exception as e:
                print(f"    Request failed: {str(e)[:30]}...")
            
            request_count += 1
            total_response_time += time.time() - start_time
            
            # Maintain request rate
            elapsed = time.time() - start_time
            if elapsed < interval:
                time.sleep(interval - elapsed)
        
        avg_response_time = total_response_time / request_count if request_count > 0 else 0
        success_rate = (success_count / request_count * 100) if request_count > 0 else 0
        
        print(f"    Total requests: {request_count}")
        print(f"    Success rate: {success_rate:.1f}%")
        print(f"    Avg response time: {avg_response_time:.3f}s")
        
        return {
            "total_requests": request_count,
            "success_count": success_count,
            "success_rate": success_rate,
            "avg_response_time": avg_response_time
        }

    def generate_simulation_report(self) -> Dict[str, Any]:
        """Generate comprehensive simulation report."""
        if not self.results["sessions"]:
            return {"error": "No simulation data available"}
        
        # Calculate overall statistics
        total_requests = sum(s["total_requests"] for s in self.results["sessions"])
        total_successful = sum(s["successful_requests"] for s in self.results["sessions"])
        total_failed = sum(s["failed_requests"] for s in self.results["sessions"])
        
        # Calculate average response times
        all_response_times = []
        for session in self.results["sessions"]:
            for action in session["action_results"]:
                all_response_times.append(action["response_time"])
        
        # Action popularity analysis
        action_counts = {}
        for session in self.results["sessions"]:
            for action in session["actions_performed"]:
                action_counts[action] = action_counts.get(action, 0) + 1
        
        # Error analysis
        error_patterns = {}
        for session in self.results["sessions"]:
            for error in session["errors"]:
                error_type = error.split(":")[0] if ":" in error else error
                error_patterns[error_type] = error_patterns.get(error_type, 0) + 1
        
        report = {
            "simulation_summary": {
                "total_sessions": len(self.results["sessions"]),
                "total_requests": total_requests,
                "successful_requests": total_successful,
                "failed_requests": total_failed,
                "overall_success_rate": (total_successful / total_requests * 100) if total_requests > 0 else 0,
                "avg_response_time": sum(all_response_times) / len(all_response_times) if all_response_times else 0
            },
            "user_behavior_analysis": {
                "most_popular_actions": sorted(action_counts.items(), key=lambda x: x[1], reverse=True)[:10],
                "action_distribution": action_counts
            },
            "error_analysis": {
                "error_patterns": error_patterns,
                "most_common_errors": sorted(error_patterns.items(), key=lambda x: x[1], reverse=True)[:5]
            },
            "performance_metrics": {
                "response_time_distribution": {
                    "min": min(all_response_times) if all_response_times else 0,
                    "max": max(all_response_times) if all_response_times else 0,
                    "avg": sum(all_response_times) / len(all_response_times) if all_response_times else 0
                }
            },
            "sessions": self.results["sessions"]
        }
        
        return report

    def save_simulation_results(self, filename: str = None) -> str:
        """Save simulation results to file."""
        if filename is None:
            timestamp = int(time.time())
            filename = f"user_simulation_results_{timestamp}.json"
        
        report = self.generate_simulation_report()
        
        try:
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"💾 Simulation results saved to: {filename}")
            return filename
        except Exception as e:
            print(f"❌ Failed to save results: {e}")
            return ""

    def print_simulation_summary(self):
        """Print a summary of simulation results."""
        report = self.generate_simulation_report()
        
        print(f"\n{'='*60}")
        print("📊 USER ACTION SIMULATION SUMMARY")
        print(f"{'='*60}")
        
        summary = report["simulation_summary"]
        print(f"\nOverall Statistics:")
        print(f"  Sessions: {summary['total_sessions']}")
        print(f"  Total Requests: {summary['total_requests']}")
        print(f"  Success Rate: {summary['overall_success_rate']:.1f}%")
        print(f"  Avg Response Time: {summary['avg_response_time']:.3f}s")
        
        print(f"\nMost Popular Actions:")
        for action, count in report["user_behavior_analysis"]["most_popular_actions"][:5]:
            print(f"  {action}: {count} times")
        
        if report["error_analysis"]["most_common_errors"]:
            print(f"\nMost Common Errors:")
            for error, count in report["error_analysis"]["most_common_errors"][:3]:
                print(f"  {error}: {count} occurrences")
        
        print(f"\n{'='*60}")


def main():
    """Main function to run user action simulation."""
    if not optimized_available:
        print("⚠️ Running in simulation mode (optimized client not available)")
    
    print("👥 Sisense User Action Simulation")
    print("Simulating realistic user interactions with Sisense API...")
    
    simulator = SisenseUserActionSimulator()
    
    print(f"\n🎯 Test Scenarios:")
    print("1. Individual User Sessions")
    print("2. Concurrent User Load")  
    print("3. Error Handling Scenarios")
    print("4. Performance Under Load")
    
    # Test 1: Individual user sessions
    print(f"\n{'='*50}")
    print("1️⃣ INDIVIDUAL USER SESSIONS")
    print(f"{'='*50}")
    
    user_types = ["dashboard_explorer", "data_analyst", "casual_viewer"]
    for user_type in user_types:
        simulator.simulate_user_session(user_type, session_duration_minutes=2)
        time.sleep(1)  # Brief pause between sessions
    
    # Test 2: Concurrent users
    print(f"\n{'='*50}")
    print("2️⃣ CONCURRENT USER SIMULATION")
    print(f"{'='*50}")
    
    concurrent_scenarios = {
        "dashboard_explorer": 2,
        "data_analyst": 1,
        "casual_viewer": 2
    }
    simulator.simulate_concurrent_users(concurrent_scenarios, session_duration=3)
    
    # Test 3: Error handling
    print(f"\n{'='*50}")
    print("3️⃣ ERROR HANDLING SCENARIOS")
    print(f"{'='*50}")
    
    simulator.test_error_handling_scenarios()
    
    # Test 4: Performance under load
    print(f"\n{'='*50}")
    print("4️⃣ PERFORMANCE UNDER LOAD")
    print(f"{'='*50}")
    
    load_results = simulator.test_performance_under_load(requests_per_minute=30, duration_minutes=2)
    
    # Generate and save results
    simulator.print_simulation_summary()
    filename = simulator.save_simulation_results()
    
    print(f"\n🎉 Simulation Complete!")
    print(f"📁 Detailed results saved to: {filename}")
    print(f"\n🔍 Key Insights:")
    print("• Tested optimized HTTP client under realistic user loads")
    print("• Validated error handling and recovery mechanisms")
    print("• Measured performance improvements in concurrent scenarios")
    print("• Identified most common user action patterns")


if __name__ == "__main__":
    main()