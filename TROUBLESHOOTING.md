# Troubleshooting Guide

## Common Issues and Solutions

### 1. Authentication Issues

#### Problem: "SISENSE_API_TOKEN is not configured"
**Solution:**
1. Check your `.env` file exists in the project root
2. Verify `SISENSE_API_TOKEN` is set correctly
3. Ensure no extra spaces or quotes around the token
4. Test the token manually with curl:
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" "https://YOUR_SISENSE_URL/api/v1/dashboards"
   ```

#### Problem: Authentication validation returns False
**Solution:**
1. Verify your Sisense URL is correct in `.env`
2. Check if your token has expired
3. Ensure the token has proper permissions
4. Test with a fresh token from Sisense Admin panel

### 2. Endpoint Not Available Errors

#### Problem: "Data models functionality is not available"
**This is expected behavior** - your Sisense instance doesn't expose data model endpoints.
- Use dashboards and widgets for data access instead
- Check `WORKING_ENDPOINTS.md` for available functionality

#### Problem: "SQL functionality is not available"
**This is expected behavior** - your Sisense instance doesn't expose datasource endpoints.
- Extract JAQL queries from existing widgets instead
- Use the dashboard-based approach for data access

### 3. Application Startup Issues

#### Problem: "ModuleNotFoundError: No module named 'dotenv'"
**Solution:**
```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

#### Problem: Flask app won't start
**Solution:**
1. Check virtual environment is activated
2. Verify all dependencies are installed
3. Check for Python version compatibility (3.8+)
4. Look for detailed error messages in the console

### 4. Network and Connectivity Issues

#### Problem: SSL verification errors
**Solution:**
Add to your `.env` file:
```
SSL_VERIFY=false
```
⚠️ Only use this in development environments

#### Problem: Connection timeouts
**Solution:**
Increase timeout in `.env`:
```
REQUEST_TIMEOUT=60
```

#### Problem: Name resolution errors
**Solution:**
1. Check your internet connection
2. Verify the Sisense URL is accessible
3. Try accessing the URL in a browser first

### 5. Frontend Issues

#### Problem: API calls failing from the web interface
**Solution:**
1. Check browser console for detailed errors
2. Verify Flask app is running on the correct port
3. Check if authentication is valid in the web interface
4. Clear browser cache and cookies

#### Problem: No data showing in dashboards
**Solution:**
1. Check if your token has read permissions
2. Verify the Sisense instance has accessible dashboards
3. Check browser network tab for failed requests

### 6. Development Issues

#### Problem: Import errors with sisense modules
**Solution:**
Make sure you're using the correct import paths:
```python
# Correct
from sisense.config import Config
from sisense.auth import get_auth_headers

# Incorrect
from config import Config
from auth import get_auth_headers
```

#### Problem: Tests failing
**Solution:**
1. Run tests from the project root directory
2. Ensure virtual environment is activated
3. Check that all dependencies are installed
4. Update test file paths if needed

## Diagnostic Commands

### Run the diagnostic script
```bash
python diagnostic_script.py
```

### Test authentication manually
```bash
python -c "from sisense.auth import validate_authentication; print(validate_authentication())"
```

### Run comprehensive tests
```bash
python test_complete_integration.py
```

### Check Flask routes
```bash
python -c "from app import create_app; app = create_app(); [print(f'{rule.rule:40} {rule.methods}') for rule in app.url_map.iter_rules()]"
```

## Configuration Requirements

### Minimum .env file
```
SISENSE_URL=https://your-sisense-instance.com
SISENSE_API_TOKEN=your_api_token_here
```

### Full .env file template
```
# Sisense Configuration
SISENSE_URL=https://your-sisense-instance.com
SISENSE_API_TOKEN=your_api_token_here

# Optional settings
DEMO_MODE=false
FLASK_ENV=development
FLASK_DEBUG=true
FLASK_PORT=5000
REQUEST_TIMEOUT=30
SSL_VERIFY=true
LOG_LEVEL=INFO
```

## Getting Help

### Information to provide when asking for help:
1. Error message (full traceback)
2. Your Python version: `python --version`
3. Contents of your `.env` file (without sensitive tokens)
4. Output of diagnostic script
5. Whether you're using a cloud or on-premise Sisense instance

### Useful diagnostic information:
```bash
# Python version
python --version

# Package versions
pip list | grep -E "(flask|requests|python-dotenv)"

# Test basic connectivity
curl -I https://your-sisense-url.com

# Check available endpoints
python diagnostic_script.py
```

## Known Environment Limitations

Based on the diagnostic results for this specific Sisense instance:

### Not Available:
- Data model/elasticube browsing
- Direct SQL query execution
- JAQL query execution
- User profile information

### Available:
- Dashboard management (475 dashboards)
- Widget access (747 widgets)
- Connection monitoring (141 connections)
- Authentication validation

This is a **dashboard-centric** Sisense environment. Focus on dashboard and widget-based functionality rather than direct data querying.