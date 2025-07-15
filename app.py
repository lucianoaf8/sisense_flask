"""
Main Flask application for Sisense API integration.

Production-grade Flask application providing REST API endpoints
for interacting with Sisense v1/v2 APIs with proper error handling,
authentication, and response formatting.
"""

import logging
import time
import webbrowser
import threading
from datetime import datetime
from flask import Flask, request, jsonify, make_response, render_template, flash, redirect, url_for, send_file
from werkzeug.exceptions import HTTPException
import traceback

from sisense.config import Config
from sisense import (
    auth, datamodels, connections, dashboards, 
    widgets, sql, jaql, utils, logger as sisense_logger_module
)
from smart_sisense_client import SmartSisenseClient


def create_app():
    """
    Create and configure Flask application.
    
    Returns:
        Flask: Configured Flask application.
    """
    app = Flask(__name__)
    
    # Configure logging
    utils.setup_logging()
    app_logger = logging.getLogger(__name__)
    
    # Initialize enhanced logging system
    sisense_logger = sisense_logger_module.get_logger()
    sisense_logger.log_system_event("Application starting", "INFO", {"version": "2.0"})
    
    # Validate configuration
    try:
        Config.validate_required_settings()
        app_logger.info("Configuration validated successfully")
    except ValueError as e:
        app_logger.error(f"Configuration validation failed: {e}")
        raise
    
    # Initialize smart Sisense client
    smart_client = None
    if not Config.DEMO_MODE:
        try:
            smart_client = SmartSisenseClient(Config.SISENSE_URL, Config.SISENSE_API_TOKEN)
            app_logger.info("Smart Sisense client initialized successfully")
        except Exception as e:
            app_logger.warning(f"Smart client initialization failed, using fallback mode: {e}")
    else:
        app_logger.info("Running in demo mode - smart client disabled")
    
    # Global error handlers
    @app.errorhandler(utils.SisenseAPIError)
    def handle_sisense_api_error(error):
        """Handle Sisense API errors."""
        app_logger.error(f"Sisense API error: {error}")
        return jsonify({
            'error': 'sisense_api_error',
            'message': str(error),
            'status_code': error.status_code or 500,
            'details': error.response_data
        }), error.status_code or 500
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Handle HTTP exceptions."""
        app_logger.error(f"HTTP error: {error}")
        return jsonify({
            'error': 'http_error',
            'message': error.description,
            'status_code': error.code
        }), error.code
    
    @app.errorhandler(Exception)
    def handle_generic_error(error):
        """Handle unexpected errors."""
        app_logger.error(f"Unexpected error: {error}")
        app_logger.error(traceback.format_exc())
        return jsonify({
            'error': 'internal_error',
            'message': 'An unexpected error occurred',
            'status_code': 500
        }), 500
    
    # Health check endpoint
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint."""
        try:
            is_valid = auth.validate_authentication()
            return jsonify({
                'overall_status': 'healthy' if is_valid else 'unhealthy',
                'authentication_valid': is_valid,
                'timestamp': time.time(),
                'sisense_url': Config.SISENSE_URL
            })
        except Exception as e:
            app_logger.error(f"Health check failed: {e}")
            return jsonify({
                'overall_status': 'unhealthy',
                'error': str(e),
                'timestamp': time.time()
            }), 500
    
    # Authentication endpoints
    @app.route('/api/auth/login', methods=['POST'])
    def login():
        """Get JWT token for authentication."""
        try:
            token = auth.login()
            return jsonify({
                'access_token': token,
                'token_type': 'Bearer'
            })
        except Exception as e:
            app_logger.error(f"Login failed: {e}")
            raise
    
    @app.route('/api/auth/validate', methods=['GET'])
    def validate_auth():
        """Authentication validation using smart routing."""
        try:
            if smart_client:
                # Use smart client authentication
                is_valid = smart_client.authenticate()
                capabilities = smart_client.get_capabilities()
                return jsonify({
                    'valid': is_valid,
                    'message': 'Authentication is valid' if is_valid else 'Authentication failed',
                    'auth_pattern': capabilities.get('auth_pattern'),
                    'timestamp': time.time()
                })
            else:
                # Fallback to regular auth
                is_valid = auth.validate_authentication()
                return jsonify({
                    'valid': is_valid,
                    'message': 'Authentication is valid' if is_valid else 'Authentication failed',
                    'auth_pattern': 'fallback',
                    'timestamp': time.time()
                })
        except Exception as e:
            app_logger.error(f"Auth validation failed: {e}")
            return jsonify({
                'valid': False,
                'message': str(e),
                'timestamp': time.time()
            }), 500
    
    @app.route('/api/auth/status', methods=['GET'])
    def auth_status():
        """Get authentication status."""
        try:
            is_valid = auth.validate_authentication()
            return jsonify({
                'authenticated': is_valid,
                'auth_method': 'api_token',
                'sisense_url': Config.SISENSE_URL,
                'timestamp': time.time()
            })
        except Exception as e:
            app_logger.error(f"Auth status failed: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/auth/user-info', methods=['GET'])
    def user_info():
        """Get current user information."""
        try:
            # With API token authentication, we don't have user info
            # Return a placeholder response
            return jsonify({
                'user': {
                    'authenticated': auth.validate_authentication(),
                    'auth_method': 'api_token'
                },
                'timestamp': time.time()
            })
        except Exception as e:
            app_logger.error(f"User info failed: {e}")
            return jsonify({'error': str(e)}), 500
    
    
    @app.route('/api/test-endpoints', methods=['GET'])
    def test_endpoints():
        """Test various API endpoints for functionality."""
        try:
            # Test basic endpoints we know work
            results = {
                'dashboards': False,
                'connections': False
            }
            
            try:
                dashboards_list = dashboards.list_dashboards()
                results['dashboards'] = len(dashboards_list) > 0
            except:
                pass
                
            try:
                connections_list = connections.list_connections()
                results['connections'] = len(connections_list) > 0
            except:
                pass
                
            return jsonify(results)
        except Exception as e:
            app_logger.error(f"Endpoint testing failed: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/system/capabilities', methods=['GET'])
    def system_capabilities():
        """Get detected API capabilities and patterns."""
        try:
            if smart_client:
                capabilities = smart_client.get_capabilities()
                summary = smart_client.get_capability_summary()
                return jsonify({
                    'capabilities': capabilities,
                    'summary': summary,
                    'smart_client_enabled': True,
                    'timestamp': time.time()
                })
            else:
                return jsonify({
                    'capabilities': {},
                    'summary': 'Smart client not available (demo mode or initialization failed)',
                    'smart_client_enabled': False,
                    'timestamp': time.time()
                })
        except Exception as e:
            app_logger.error(f"Capabilities endpoint failed: {e}")
            return jsonify({
                'error': str(e),
                'smart_client_enabled': False,
                'timestamp': time.time()
            }), 500
    
    # Data models endpoints (v2)
    @app.route('/api/datamodels', methods=['GET'])
    def list_datamodels():
        """List all data models using smart routing."""
        try:
            model_type = request.args.get('type')
            
            if smart_client:
                # Use smart client with capability detection
                models = smart_client.list_data_models(model_type)
                capabilities = smart_client.get_capabilities()
                
                # Add information about model types available
                model_types = {}
                for model in models:
                    model_type_found = model.get('type', 'unknown')
                    if model_type_found not in model_types:
                        model_types[model_type_found] = 0
                    model_types[model_type_found] += 1
                
                response_data = {
                    'data': models,
                    'count': len(models),
                    'type_filter': model_type,
                    'api_pattern': capabilities.get('data_model_pattern'),
                    'available_types': model_types,
                    'capabilities': capabilities
                }
                
                # Add warning if filtering for live models but none found
                if model_type == 'live' and len(models) == 0:
                    response_data['warning'] = 'No live models found. This environment appears to only have ElastiCubes (extract-based models).'
                
                return jsonify(response_data)
            else:
                # Fallback to regular module
                models = datamodels.list_models(model_type)
                return jsonify({
                    'data': models,
                    'count': len(models),
                    'type_filter': model_type,
                    'api_pattern': 'fallback'
                })
        except Exception as e:
            app_logger.error(f"Failed to list data models: {e}")
            raise
    
    @app.route('/api/datamodels/<model_oid>', methods=['GET'])
    def get_datamodel(model_oid):
        """Get specific data model by OID."""
        try:
            model = datamodels.get_model(model_oid)
            return jsonify(model)
        except Exception as e:
            app_logger.error(f"Failed to get data model {model_oid}: {e}")
            raise
    
    @app.route('/api/datamodels/<model_oid>/tables', methods=['GET'])
    def get_datamodel_tables(model_oid):
        """Get tables for a data model."""
        try:
            tables = datamodels.get_model_tables(model_oid)
            return jsonify({
                'data': tables,
                'count': len(tables),
                'model_oid': model_oid
            })
        except Exception as e:
            app_logger.error(f"Failed to get tables for model {model_oid}: {e}")
            raise
    
    @app.route('/api/datamodels/<model_oid>/columns', methods=['GET'])
    def get_datamodel_columns(model_oid):
        """Get columns for a data model."""
        try:
            table_name = request.args.get('table')
            columns = datamodels.get_model_columns(model_oid, table_name)
            return jsonify({
                'data': columns,
                'count': len(columns),
                'model_oid': model_oid,
                'table_filter': table_name
            })
        except Exception as e:
            app_logger.error(f"Failed to get columns for model {model_oid}: {e}")
            raise
    
    @app.route('/api/datamodels/export/schema', methods=['GET'])
    def export_datamodel_schema():
        """Export data model schema."""
        try:
            model_oid = request.args.get('model')
            unmasked = request.args.get('unmasked', 'false').lower() == 'true'
            include_relationships = request.args.get('relationships', 'true').lower() == 'true'
            include_tables = request.args.get('tables', 'true').lower() == 'true'
            include_columns = request.args.get('columns', 'true').lower() == 'true'
            
            schema = datamodels.export_schema(
                model_oid=model_oid,
                unmasked=unmasked,
                include_relationships=include_relationships,
                include_tables=include_tables,
                include_columns=include_columns
            )
            return jsonify(schema)
        except Exception as e:
            app_logger.error(f"Failed to export schema: {e}")
            raise
    
    # Connections endpoints (v2)
    @app.route('/api/connections', methods=['GET'])
    def api_list_connections():
        """List all connections."""
        try:
            connection_type = request.args.get('type')
            include_credentials = request.args.get('credentials', 'false').lower() == 'true'
            
            from sisense import connections as connection_module
            connection_list = connection_module.list_connections(connection_type, include_credentials)
            return jsonify({
                'data': connection_list,
                'count': len(connection_list),
                'type_filter': connection_type
            })
        except Exception as e:
            app_logger.error(f"Failed to list connections: {e}")
            raise
    
    @app.route('/api/connections/<connection_id>', methods=['GET'])
    def api_get_connection(connection_id):
        """Get specific connection by ID."""
        try:
            include_credentials = request.args.get('credentials', 'false').lower() == 'true'
            from sisense import connections as connection_module
            connection = connection_module.get_connection(connection_id, include_credentials)
            return jsonify(connection)
        except Exception as e:
            app_logger.error(f"Failed to get connection {connection_id}: {e}")
            raise
    
    @app.route('/api/connections/<connection_id>/test', methods=['POST'])
    def test_connection(connection_id):
        """Test connection."""
        try:
            test_result = connections.test_connection(connection_id)
            return jsonify(test_result)
        except Exception as e:
            app_logger.error(f"Failed to test connection {connection_id}: {e}")
            raise
    
    # Dashboards endpoints (v1)
    @app.route('/api/dashboards', methods=['GET'])
    def api_list_dashboards():
        """List all dashboards."""
        try:
            owner = request.args.get('owner')
            shared = request.args.get('shared')
            if shared:
                shared = shared.lower() == 'true'
            fields = request.args.getlist('fields')
            
            from sisense import dashboards as dashboard_module
            dashboard_list = dashboard_module.list_dashboards(owner, shared, fields)
            return jsonify({
                'data': dashboard_list,
                'count': len(dashboard_list),
                'owner_filter': owner,
                'shared_filter': shared
            })
        except Exception as e:
            app_logger.error(f"Failed to list dashboards: {e}")
            raise
    
    @app.route('/api/dashboards/<dashboard_id>', methods=['GET'])
    def api_get_dashboard(dashboard_id):
        """Get specific dashboard by ID."""
        try:
            fields = request.args.getlist('fields')
            from sisense import dashboards as dashboard_module
            dashboard = dashboard_module.get_dashboard(dashboard_id, fields)
            return jsonify(dashboard)
        except Exception as e:
            app_logger.error(f"Failed to get dashboard {dashboard_id}: {e}")
            raise
    
    @app.route('/api/dashboards/<dashboard_id>/widgets', methods=['GET'])
    def get_dashboard_widgets(dashboard_id):
        """Get widgets for a dashboard."""
        try:
            widget_list = dashboards.get_dashboard_widgets(dashboard_id)
            return jsonify({
                'data': widget_list,
                'count': len(widget_list),
                'dashboard_id': dashboard_id
            })
        except Exception as e:
            app_logger.error(f"Failed to get widgets for dashboard {dashboard_id}: {e}")
            raise
    
    @app.route('/api/dashboards/<dashboard_id>/summary', methods=['GET'])
    def get_dashboard_summary(dashboard_id):
        """Get dashboard summary."""
        try:
            summary = dashboards.get_dashboard_summary(dashboard_id)
            return jsonify(summary)
        except Exception as e:
            app_logger.error(f"Failed to get dashboard summary {dashboard_id}: {e}")
            raise
    
    # Widgets endpoints (v1)
    @app.route('/api/widgets/<widget_id>', methods=['GET'])
    def get_widget(widget_id):
        """Get specific widget by ID."""
        try:
            fields = request.args.getlist('fields')
            widget = widgets.get_widget(widget_id, fields)
            return jsonify(widget)
        except Exception as e:
            app_logger.error(f"Failed to get widget {widget_id}: {e}")
            raise
    
    @app.route('/api/widgets/<widget_id>/jaql', methods=['GET'])
    def get_widget_jaql(widget_id):
        """Get JAQL query for a widget."""
        try:
            widget_jaql = widgets.get_widget_jaql(widget_id)
            return jsonify(widget_jaql)
        except Exception as e:
            app_logger.error(f"Failed to get JAQL for widget {widget_id}: {e}")
            raise
    
    @app.route('/api/widgets/<widget_id>/data', methods=['GET', 'POST'])
    def get_widget_data(widget_id):
        """Get data for a widget."""
        try:
            filters = None
            if request.method == 'POST':
                filters = request.json.get('filters') if request.json else None
            
            widget_data = widgets.get_widget_data(widget_id, filters)
            return jsonify(widget_data)
        except Exception as e:
            app_logger.error(f"Failed to get data for widget {widget_id}: {e}")
            raise
    
    @app.route('/api/widgets/<widget_id>/summary', methods=['GET'])
    def get_widget_summary(widget_id):
        """Get widget summary."""
        try:
            summary = widgets.get_widget_summary(widget_id)
            return jsonify(summary)
        except Exception as e:
            app_logger.error(f"Failed to get widget summary {widget_id}: {e}")
            raise
    
    # Export endpoints (missing in original implementation)
    @app.route('/api/dashboards/<dashboard_id>/export/<export_type>', methods=['GET'])
    def export_dashboard(dashboard_id, export_type):
        """Get dashboard export URL."""
        try:
            export_url = dashboards.get_dashboard_export_url(dashboard_id, export_type)
            return jsonify({'export_url': export_url, 'dashboard_id': dashboard_id, 'export_type': export_type})
        except Exception as e:
            app_logger.error(f"Failed to get dashboard export URL {dashboard_id}: {e}")
            raise
    
    @app.route('/api/widgets/<widget_id>/export/<export_type>', methods=['GET'])
    def export_widget(widget_id, export_type):
        """Get widget export URL."""
        try:
            export_url = widgets.get_widget_export_url(widget_id, export_type)
            return jsonify({'export_url': export_url, 'widget_id': widget_id, 'export_type': export_type})
        except Exception as e:
            app_logger.error(f"Failed to get widget export URL {widget_id}: {e}")
            raise
    
    # SQL endpoints
    @app.route('/api/datasources/<datasource>/sql', methods=['GET'])
    def execute_sql_query(datasource):
        """Execute SQL query on datasource."""
        try:
            query = request.args.get('query')
            if not query:
                return jsonify({'error': 'query parameter is required'}), 400
            
            limit = request.args.get('limit', type=int)
            offset = request.args.get('offset', type=int)
            timeout = request.args.get('timeout', type=int)
            
            result = sql.execute_sql(datasource, query, limit, offset, timeout)
            return jsonify(result)
        except Exception as e:
            app_logger.error(f"Failed to execute SQL query on {datasource}: {e}")
            raise
    
    @app.route('/api/datasources/<datasource>/sql/validate', methods=['POST'])
    def validate_sql_query(datasource):
        """Validate SQL query."""
        try:
            if not request.json or 'query' not in request.json:
                return jsonify({'error': 'query is required in request body'}), 400
            
            query = request.json['query']
            validation_result = sql.validate_sql_query(query)
            return jsonify(validation_result)
        except Exception as e:
            app_logger.error(f"Failed to validate SQL query: {e}")
            raise
    
    # JAQL endpoints
    @app.route('/api/datasources/<datasource>/jaql', methods=['POST'])
    def execute_jaql_query(datasource):
        """Execute JAQL query on datasource."""
        try:
            if not request.json or 'jaql' not in request.json:
                return jsonify({'error': 'jaql is required in request body'}), 400
            
            jaql_query = request.json['jaql']
            format_type = request.json.get('format', 'json')
            timeout = request.json.get('timeout')
            
            result = jaql.execute_jaql(datasource, jaql_query, format_type, timeout)
            return jsonify(result)
        except Exception as e:
            app_logger.error(f"Failed to execute JAQL query on {datasource}: {e}")
            raise
    
    @app.route('/api/datasources/<datasource>/jaql/metadata', methods=['GET'])
    def get_jaql_metadata(datasource):
        """Get JAQL metadata for datasource."""
        try:
            table_name = request.args.get('table')
            metadata = jaql.get_jaql_metadata(datasource, table_name)
            return jsonify(metadata)
        except Exception as e:
            app_logger.error(f"Failed to get JAQL metadata for {datasource}: {e}")
            raise
    
    @app.route('/api/datasources/<datasource>/catalog', methods=['GET'])
    def get_datasource_catalog(datasource):
        """Get complete catalog for datasource."""
        try:
            catalog = jaql.get_datasource_catalog(datasource)
            return jsonify(catalog)
        except Exception as e:
            app_logger.error(f"Failed to get catalog for {datasource}: {e}")
            raise
    
    # Search endpoints
    @app.route('/api/search/dashboards', methods=['GET'])
    def search_dashboards():
        """Search dashboards."""
        try:
            search_term = request.args.get('q')
            if not search_term:
                return jsonify({'error': 'q parameter is required'}), 400
            
            results = dashboards.search_dashboards(search_term)
            return jsonify({
                'data': results,
                'count': len(results),
                'search_term': search_term
            })
        except Exception as e:
            app_logger.error(f"Failed to search dashboards: {e}")
            raise
    
    @app.route('/api/search/datamodels', methods=['GET'])
    def search_datamodels():
        """Search data models."""
        try:
            search_term = request.args.get('q')
            if not search_term:
                return jsonify({'error': 'q parameter is required'}), 400
            
            results = datamodels.search_models(search_term)
            return jsonify({
                'data': results,
                'count': len(results),
                'search_term': search_term
            })
        except Exception as e:
            app_logger.error(f"Failed to search data models: {e}")
            raise
    
    # Logging endpoints
    @app.route('/api/logs/recent', methods=['GET'])
    def get_recent_logs():
        """Get recent logs from buffer."""
        try:
            limit = request.args.get('limit', 100, type=int)
            sisense_logger = sisense_logger_module.get_logger()
            logs = sisense_logger.get_recent_logs(limit)
            return jsonify({
                'logs': logs,
                'count': len(logs)
            })
        except Exception as e:
            app_logger.error(f"Failed to get recent logs: {e}")
            return jsonify({'error': 'Failed to get logs'}), 500
    
    @app.route('/api/logs/add', methods=['POST'])
    def add_log_entry():
        """Add log entry from frontend."""
        try:
            data = request.json
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            log_type = data.get('type', 'frontend')
            message = data.get('message', '')
            metadata = data.get('metadata', {})
            
            sisense_logger = sisense_logger_module.get_logger()
            
            if log_type == 'api_call':
                sisense_logger.log_api_call(
                    method=metadata.get('method', 'UNKNOWN'),
                    endpoint=metadata.get('endpoint', ''),
                    payload=metadata.get('payload'),
                    response_status=metadata.get('responseStatus'),
                    response_time=metadata.get('responseTime')
                )
            elif log_type == 'user_action':
                sisense_logger.log_user_action(
                    action=metadata.get('action', message),
                    details=metadata.get('details')
                )
            elif log_type == 'system_event':
                sisense_logger.log_system_event(
                    event=metadata.get('event', message),
                    level=metadata.get('level', 'INFO'),
                    details=metadata.get('details')
                )
            else:
                # Generic log entry
                sisense_logger.log_system_event(message, 'INFO', metadata)
            
            return jsonify({'status': 'success'})
        except Exception as e:
            app_logger.error(f"Failed to add log entry: {e}")
            return jsonify({'error': 'Failed to add log entry'}), 500
    
    @app.route('/api/logs/download', methods=['GET'])
    def download_logs():
        """Download log files."""
        try:
            sisense_logger = sisense_logger_module.get_logger()
            
            # Get current log file
            if hasattr(sisense_logger, 'current_log_file'):
                import os
                if os.path.exists(sisense_logger.current_log_file):
                    return send_file(
                        sisense_logger.current_log_file,
                        as_attachment=True,
                        download_name=f"sisense_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                    )
            
            return jsonify({'error': 'Log file not found'}), 404
        except Exception as e:
            app_logger.error(f"Failed to download logs: {e}")
            return jsonify({'error': 'Failed to download logs'}), 500
    
    @app.route('/api/logs/files', methods=['GET'])
    def list_log_files():
        """List available log files."""
        try:
            sisense_logger = sisense_logger_module.get_logger()
            log_files = sisense_logger.get_log_files()
            return jsonify({
                'files': log_files,
                'count': len(log_files)
            })
        except Exception as e:
            app_logger.error(f"Failed to list log files: {e}")
            return jsonify({'error': 'Failed to list log files'}), 500
    
    # Web UI Routes
    @app.route('/')
    def dashboard():
        """Main dashboard page."""
        return render_template('dashboard.html', 
                             sisense_url=Config.get_sisense_base_url())
    
    @app.route('/datamodels')
    def data_models():
        """Data models page."""
        return render_template('data_models.html')
    
    @app.route('/dashboards')
    def dashboards():
        """Dashboards page."""
        return render_template('dashboards.html')
    
    @app.route('/connections')
    def connections():
        """Connections page."""
        return render_template('connections.html')
    
    @app.route('/sql')
    def query_sql():
        """SQL query page."""
        return render_template('sql_query.html')
    
    @app.route('/jaql')
    def query_jaql():
        """JAQL query page."""
        return render_template('jaql_query.html')
    
    @app.route('/docs')
    def api_docs():
        """API documentation page."""
        return render_template('api_docs.html', 
                             base_url=request.host_url.rstrip('/'))
    
    @app.route('/query-editor')
    def query_editor():
        """Advanced query editor page."""
        return render_template('advanced_query_editor.html')
    
    @app.route('/connection-status')
    def connection_status():
        """Enhanced connection status page."""
        return render_template('enhanced_connection_status.html',
                             sisense_url=Config.get_sisense_base_url())
    
    # Individual item detail routes
    @app.route('/dashboard/<dashboard_id>')
    def dashboard_detail(dashboard_id):
        """Individual dashboard detail page."""
        try:
            dashboard = dashboards.get_dashboard(dashboard_id)
            return render_template('dashboard_detail.html', 
                                 dashboard=dashboard)
        except Exception as e:
            flash(f'Error loading dashboard: {str(e)}', 'error')
            return redirect(url_for('dashboards'))
    
    @app.route('/datamodel/<model_oid>')
    def datamodel_detail(model_oid):
        """Individual data model detail page."""
        try:
            model = datamodels.get_model(model_oid)
            return render_template('datamodel_detail.html', 
                                 model=model)
        except Exception as e:
            flash(f'Error loading data model: {str(e)}', 'error')
            return redirect(url_for('data_models'))
    
    @app.route('/widget/<widget_id>')
    def widget_detail(widget_id):
        """Individual widget detail page."""
        try:
            widget = widgets.get_widget(widget_id)
            return render_template('widget_detail.html', 
                                 widget=widget)
        except Exception as e:
            flash(f'Error loading widget: {str(e)}', 'error')
            return redirect(url_for('dashboards'))

    app_logger.info("Flask application configured successfully")
    return app


# Create application instance
app = create_app()


def open_browser():
    """Open browser to the application URL after a short delay."""
    def open_url():
        time.sleep(1.5)  # Wait for server to start
        webbrowser.open(f'http://localhost:{Config.FLASK_PORT}')
    
    threading.Thread(target=open_url, daemon=True).start()


if __name__ == '__main__':
    # Open browser automatically in development mode
    if Config.FLASK_DEBUG:
        open_browser()
    
    # Run development server
    app.run(
        host='0.0.0.0',
        port=Config.FLASK_PORT,
        debug=Config.FLASK_DEBUG
    )