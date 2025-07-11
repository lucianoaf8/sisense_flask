# Sisense Flask Integration

A production-grade Flask application providing REST API and web interface for Sisense v1/v2 API integration.

## 🚀 Features

- **REST API Integration**: Complete implementation of Sisense v1/v2 REST API endpoints
- **Web Interface**: Modern, responsive UI for data exploration and querying
- **API Token Authentication**: Secure authentication using Sisense API tokens
- **Query Tools**: SQL and JAQL query interfaces with validation
- **Data Exploration**: Browse data models, dashboards, widgets, and connections
- **Production Ready**: Error handling, logging, retry logic, and configuration management

## 📋 Prerequisites

- Python 3.8+
- Sisense instance with API access
- Sisense API token

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd sisense_flask
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   ```

3. **Activate the virtual environment:**
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your Sisense configuration:
   ```
   SISENSE_URL=https://your-sisense-instance.com
   SISENSE_API_TOKEN=your_api_token_here
   ```

## 🏃 Running the Application

```bash
python app.py
```

The application will start on `http://localhost:5000`

### Available Interfaces:

- **Web UI**: http://localhost:5000
- **API Documentation**: http://localhost:5000/docs
- **Health Check**: http://localhost:5000/health

## 📁 Project Structure

```
sisense_flask/
├── app.py                    # Main Flask application
├── config.py                 # Configuration management
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (not in git)
├── .env.example             # Example environment file
├── .gitignore               # Git ignore rules
├── sisense/                 # Core Sisense integration modules
│   ├── __init__.py
│   ├── auth.py              # Authentication handling
│   ├── connections.py       # Connection management (v2)
│   ├── dashboards.py        # Dashboard operations (v1)
│   ├── datamodels.py        # Data model operations (v2)
│   ├── jaql.py              # JAQL query execution
│   ├── sql.py               # SQL query execution
│   ├── utils.py             # HTTP client and utilities
│   └── widgets.py           # Widget operations (v1)
├── static/                  # Static assets
│   ├── css/styles.css       # Application styles
│   └── js/app.js            # Client-side JavaScript
└── templates/               # HTML templates
    ├── base.html            # Base template
    ├── dashboard.html       # Main dashboard
    ├── data_models.html     # Data models interface
    ├── dashboards.html      # Dashboards browser
    ├── connections.html     # Connections manager
    ├── sql_query.html       # SQL query interface
    ├── jaql_query.html      # JAQL query interface
    └── api_docs.html        # API documentation
```

## 🔌 API Endpoints

### Authentication
- `POST /api/auth/login` - Verify API token configuration
- `GET /api/auth/validate` - Validate authentication status

### Data Models (v2)
- `GET /api/datamodels` - List all data models
- `GET /api/datamodels/{model_oid}` - Get specific data model
- `GET /api/datamodels/{model_oid}/tables` - Get model tables
- `GET /api/datamodels/{model_oid}/columns` - Get model columns
- `GET /api/datamodels/export/schema` - Export model schema

### Connections (v2)
- `GET /api/connections` - List all connections
- `GET /api/connections/{connection_id}` - Get specific connection
- `POST /api/connections/{connection_id}/test` - Test connection

### Dashboards (v1)
- `GET /api/dashboards` - List all dashboards
- `GET /api/dashboards/{dashboard_id}` - Get specific dashboard
- `GET /api/dashboards/{dashboard_id}/widgets` - Get dashboard widgets
- `GET /api/dashboards/{dashboard_id}/summary` - Get dashboard summary

### Widgets (v1)
- `GET /api/widgets/{widget_id}` - Get specific widget
- `GET /api/widgets/{widget_id}/jaql` - Get widget JAQL
- `GET /api/widgets/{widget_id}/data` - Get widget data
- `GET /api/widgets/{widget_id}/summary` - Get widget summary

### Query Execution
- `GET /api/datasources/{datasource}/sql` - Execute SQL query
- `POST /api/datasources/{datasource}/sql/validate` - Validate SQL query
- `POST /api/datasources/{datasource}/jaql` - Execute JAQL query
- `GET /api/datasources/{datasource}/jaql/metadata` - Get JAQL metadata

### Search
- `GET /api/search/dashboards?q={query}` - Search dashboards
- `GET /api/search/datamodels?q={query}` - Search data models

## 🔧 Configuration

All configuration is managed through environment variables in the `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `SISENSE_URL` | Sisense instance URL | Required |
| `SISENSE_API_TOKEN` | Sisense API token | Required |
| `FLASK_ENV` | Flask environment | production |
| `FLASK_DEBUG` | Debug mode | false |
| `FLASK_PORT` | Application port | 5000 |
| `LOG_LEVEL` | Logging level | INFO |
| `SSL_VERIFY` | SSL verification | true |
| `REQUEST_TIMEOUT` | Request timeout (seconds) | 30 |
| `REQUEST_RETRIES` | Number of retries | 3 |

## 🔒 Security

- **API Token**: Store your Sisense API token securely in the `.env` file
- **HTTPS**: Always use HTTPS in production
- **Environment Variables**: Never commit `.env` to version control
- **SSL Verification**: Enabled by default, can be configured via `SSL_VERIFY`

## 🧪 Testing

Run the application in development mode:

```bash
FLASK_ENV=development FLASK_DEBUG=true python app.py
```

## 📝 Logging

Logs are written to:
- Console output (stdout)
- `sisense_flask.log` file

Configure logging level via `LOG_LEVEL` environment variable.

## 🚨 Error Handling

The application includes comprehensive error handling:
- Automatic retry with exponential backoff
- Detailed error messages and logging
- Graceful degradation for failed requests
- User-friendly error pages in the web interface

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
- Check the [API Documentation](http://localhost:5000/docs)
- Review Sisense official documentation
- Open an issue in the repository

## 🔗 Resources

- [Sisense REST API Documentation](https://docs.sisense.com/main/SisenseLinux/rest-apis.htm)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Python Requests Library](https://docs.python-requests.org/)

---

Built with ❤️ using Flask and Sisense REST API