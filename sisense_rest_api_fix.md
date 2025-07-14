# Claude Code Prompt: Comprehensive Sisense REST API Project Fix Implementation

**Following Claude Code Practical Prompting Guide methodology and validation standards**

## Context & Objective

We're implementing a comprehensive fix for a Sisense REST API project that currently has ~20% endpoint success rate. The analysis document identifies specific API endpoint mismatches, authentication issues, and architectural problems that need systematic resolution to achieve ~90% success rate.

**Project Structure Context:**

* Python Flask backend with Sisense API integration
* Frontend JavaScript components
* Configuration management system
* Multiple API modules for different Sisense functionality

**Goal:** Implement all fixes and recommendations from the detailed analysis to resolve endpoint failures and create a robust, production-ready Sisense API integration.

## Complete Implementation Instructions

**IMPORTANT:** Think step-by-step through each phase. Use MCP sequential thinking - only proceed to the next task after completing the current one. Do not modify files until explicitly instructed for each specific task.

### Phase 1: Core Infrastructure - API Detection & Smart Client (Tasks 1-3)

**Task 1: Create Smart API Version Detection System**

First, analyze the current project structure and then create the new detection system:

```
1. Open and examine the current project structure to understand existing files
2. Create `sisense_api_detector.py` in the main project directory
3. Implement the SisenseAPIVersionDetector class with these exact methods:
   - __init__(self, base_url, token)
   - detect_capabilities(self) 
   - _test_endpoint(self, endpoint)
4. Include capability detection for:
   - Authentication patterns (v0_auth, v1_auth, v2_auth)
   - Data model patterns (v0_elasticubes, v1_elasticubes, v2_datamodels)
   - Specific v2 features (connections, datamodels)
5. Use the exact endpoint paths from the analysis document
6. Include proper error handling and timeout settings
```

**Task 2: Create Unified Smart Sisense Client**

```
1. Create `smart_sisense_client.py` in the main project directory
2. Implement the SmartSisenseClient class with these exact methods:
   - __init__(self, base_url, token)
   - authenticate(self)
   - list_data_models(self)
   - execute_query(self, query_type, query_data)
   - get_widget_info(self, widget_id)
   - list_dashboards(self)
   - get_dashboard(self, dashboard_id)
   - _call_api(self, method, endpoint, **kwargs)
3. Integrate the SisenseAPIVersionDetector from Task 1
4. Implement smart routing logic for each method based on detected capabilities
5. Include proper error handling with SisenseAPIError exceptions
6. Use the exact API patterns identified in the analysis document
```

**Task 3: Update Configuration and Dependencies**

```
1. Open and examine the current `requirements.txt` file
2. Add any missing dependencies needed for the new smart client
3. Open the main configuration file (likely `config.py` or similar)
4. Add new configuration variables for API detection and smart routing
5. Update any existing Sisense-related configuration to support the new architecture
6. Ensure backward compatibility with existing configuration
```

### Phase 2: Fix Core API Modules (Tasks 4-7)

**Task 4: Fix Authentication Module**

```
1. Locate and open the current authentication module/file
2. Replace all instances of these incorrect endpoints:
   - '/api/v1/authentication/me' 
   - '/api/v1/users/me'
   - '/api/users/me'
   - '/api/v1/authentication'
3. Implement the correct authentication validation using:
   - '/api/v1/auth/isauth' (primary)
   - '/auth/isauth' (v0 fallback)  
   - '/api/v2/auth/isauth' (v2 if available)
4. Update the validate_authentication() function to use smart routing
5. Ensure proper fallback logic between API versions
6. Update all authentication-related error handling
7. Do not modify any unrelated authentication logic
```

**Task 5: Fix Data Models Module**

```
1. Locate and open the current data models/elasticubes module
2. Replace all instances of these incorrect endpoints:
   - '/api/v2/datamodels' (when used without fallback)
   - '/api/v1/elasticubes' (missing getElasticubes suffix)
   - '/api/elasticubes' (missing getElasticubes suffix)
3. Implement the correct data model endpoints:
   - '/api/v2/datamodels' (try first for Linux)
   - '/api/v1/elasticubes/getElasticubes' (primary fallback)
   - '/elasticubes/getElasticubes' (v0 fallback)
4. Update list_models() function to use smart routing with proper fallbacks
5. Handle the different response formats between v2 and v1/v0 APIs
6. Add proper error messages when data models are not available
7. Do not modify any unrelated data model processing logic
```

**Task 6: Fix Query Execution Module**

```
1. Locate and open the current query execution module
2. Remove all references to these non-existent endpoints:
   - '/api/v1/datasources/{datasource}/sql'
   - '/api/v1/datasources/{datasource}/jaql'
3. Implement the correct unified query endpoint:
   - '/api/v1/query' for all JAQL queries
4. Update execute_jaql() function to use the unified endpoint
5. Update execute_sql() function to either:
   - Convert SQL to JAQL if possible, OR
   - Raise SisenseAPIError with clear message about SQL not being supported
6. Ensure proper JAQL query structure and error handling
7. Do not modify any query result processing logic unless required for endpoint changes
```

**Task 7: Fix Widget Access Module**

```
1. Locate and open the current widget module
2. Remove all references to these non-existent direct widget endpoints:
   - '/api/v1/widgets/{widget_id}'
   - '/api/v1/widgets/{widget_id}/data'
3. Implement widget access through dashboard hierarchy:
   - Use existing dashboard endpoints to find widgets
   - Search through dashboard.widgets arrays to locate specific widgets
4. Update get_widget() function to search across all dashboards
5. Update get_widget_data() function to extract JAQL from widget and execute via unified query endpoint
6. Add proper error handling when widgets are not found
7. Do not modify any widget data processing logic unless required for access method changes
```

### Phase 3: Update Flask Application Layer (Tasks 8-10)

**Task 8: Update Main Flask Application**

```
1. Open the main Flask application file (likely `app.py` or `main.py`)
2. Import the new SmartSisenseClient class
3. Replace the existing Sisense client initialization with SmartSisenseClient
4. Update the following route handlers to use smart client methods:
   - Authentication validation routes
   - Data models listing routes  
   - Query execution routes
   - Widget access routes
5. Add new route for '/api/system/capabilities' to expose API capabilities
6. Update all route error handling to use the new client's error patterns
7. Ensure all existing route signatures remain the same for backward compatibility
8. Do not modify any unrelated Flask routes or middleware
```

**Task 9: Update API Response Handlers**

```
1. Locate all API response processing functions in the Flask app
2. Update responses to include new fields:
   - 'api_pattern' field showing which API version was used
   - 'capabilities' information where relevant
3. Update error responses to use the new SisenseAPIError patterns
4. Ensure backward compatibility for existing response consumers
5. Add proper status codes for new error scenarios (API not available, etc.)
6. Do not modify any unrelated response processing logic
```

**Task 10: Add System Capabilities Endpoint**

```
1. Add new Flask route: '/api/system/capabilities'
2. This route should return the detected API capabilities from SmartSisenseClient
3. Include information about:
   - Available API versions
   - Supported authentication patterns
   - Supported data model patterns
   - Individual feature availability
4. Add proper error handling if capability detection fails
5. Use GET method and return JSON response
```

### Phase 4: Frontend Integration Updates (Tasks 11-12)

**Task 11: Update JavaScript API Manager**

```
1. Open the main JavaScript file (likely in `static/js/app.js` or similar)
2. Locate the existing Sisense API interaction code
3. Create or update the SisenseAPIManager class with these methods:
   - initialize() - to get API capabilities
   - loadDataModels() - updated to handle new response format
   - validateAuth() - updated to use new auth patterns
   - executeQuery() - updated for unified query endpoint
4. Update all API calls to handle the new response formats including 'api_pattern' fields
5. Add proper error handling for new error scenarios (API not available, etc.)
6. Update success messages to show which API pattern was used
7. Do not modify any unrelated JavaScript functionality
```

**Task 12: Update Frontend Error Handling**

```
1. Locate all JavaScript error handling for Sisense API calls
2. Update error handling to recognize new error types:
   - SisenseAPIError with specific messages
   - API version not available errors
   - Feature not supported errors
3. Update user-facing error messages to be more descriptive
4. Add informational messages about API capabilities when relevant
5. Ensure graceful degradation when features are not available
6. Do not modify any unrelated error handling code
```

### Phase 5: Testing & Validation (Tasks 13-15)

**Task 13: Create Comprehensive Test Suite**

```
1. Create or update test files for the new smart client functionality
2. Write tests for SisenseAPIVersionDetector:
   - Test capability detection with different API responses
   - Test endpoint availability checking
   - Test fallback logic
3. Write tests for SmartSisenseClient:
   - Test smart routing for each method
   - Test proper fallback between API versions
   - Test error handling for unsupported features
4. Write integration tests for the Flask routes
5. Use mocking to simulate different Sisense API environments
6. Do not modify any existing tests unless they need updates for the new functionality
```

**Task 14: Run Complete Test Suite**

```
1. Execute all existing tests to ensure no regressions
2. Execute all new tests for the smart client functionality
3. If any tests fail, analyze the failures and make targeted fixes
4. Do not proceed until all tests pass
5. Generate a test report showing before/after endpoint success rates
```

**Task 15: Integration Testing**

```
1. Test the complete application with a real Sisense instance
2. Verify that API capability detection works correctly
3. Verify that smart routing selects the correct endpoints
4. Test all major user workflows:
   - Authentication validation
   - Data model listing
   - Query execution (JAQL)
   - Widget access via dashboards
5. Document any remaining limitations or unsupported features
6. Create a summary of the actual endpoint success rate improvement
```

### Phase 6: Documentation & Finalization (Tasks 16-17)

**Task 16: Update Documentation**

```
1. Create or update README.md with new architecture information
2. Document the smart client capabilities and API version detection
3. Update any existing API documentation to reflect the correct endpoints
4. Add troubleshooting guide for different Sisense environments
5. Document known limitations (e.g., direct SQL not supported)
6. Include configuration examples for different deployment types
```

**Task 17: Final Code Review & Cleanup**

```
1. Review all modified files for code quality and consistency
2. Remove any commented-out old code that's no longer needed
3. Ensure all imports are properly organized
4. Verify that all error messages are user-friendly and informative
5. Check that all new code follows the existing project's coding standards
6. Create a summary of all changes made and files modified
```

## Validation Criteria Met

**Clarity (5/5):** Each task has explicit file paths, function names, and specific endpoints to change
**Specificity (5/5):** Exact API endpoints, response formats, and implementation details provided
**Completeness (5/5):** All context, error scenarios, and integration requirements included
**Compliance (5/5):** Follows Claude Code safety practices with explicit constraints and review phases
**Effectiveness (5/5):** Structured to achieve the documented goal of ~90% endpoint success rate

## Safety Constraints & Important Notes

* **NEVER** use `--dangerously-skip-permissions` - always allow file edits when prompted
* **DO NOT** modify any unrelated code outside the specified scope for each task
* **ALWAYS** maintain backward compatibility unless explicitly changing interfaces
* **REVIEW** all changes in each phase before proceeding to the next
* **TEST** thoroughly after each phase to catch issues early
* **COMMIT** changes after each major phase with descriptive commit messages

Think step-by-step through each task. Plan the implementation approach for each task before coding. Run tests after each phase. Only proceed to the next task after completing the current one successfully.
