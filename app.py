"""
Main Flask application for Sisense API integration.

Production-grade Flask application providing REST API endpoints
for interacting with Sisense v1/v2 APIs with proper error handling,
authentication, and response formatting.
"""

import logging
from flask import Flask, request, jsonify, make_response, render_template, flash, redirect, url_for
from werkzeug.exceptions import HTTPException
import traceback

from config import Config
from sisense import (
    auth, datamodels, connections, dashboards, 
    widgets, sql, jaql, utils
)


def create_app():
    """
    Create and configure Flask application.
    
    Returns:
        Flask: Configured Flask application.
    """
    app = Flask(__name__)
    
    # Configure logging
    utils.setup_logging()
    logger = logging.getLogger(__name__)
    
    # Validate configuration
    try:
        Config.validate_required_settings()
        logger.info("Configuration validated successfully")
    except ValueError as e:
        logger.error(f"Configuration validation failed: {e}")
        raise
    
    # Global error handlers
    @app.errorhandler(utils.SisenseAPIError)
    def handle_sisense_api_error(error):
        """Handle Sisense API errors."""
        logger.error(f"Sisense API error: {error}")
        return jsonify({
            'error': 'sisense_api_error',
            'message': str(error),
            'status_code': error.status_code or 500,
            'details': error.response_data
        }), error.status_code or 500
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Handle HTTP exceptions."""
        logger.error(f"HTTP error: {error}")
        return jsonify({
            'error': 'http_error',
            'message': error.description,
            'status_code': error.code
        }), error.code
    
    @app.errorhandler(Exception)
    def handle_generic_error(error):
        """Handle unexpected errors."""
        logger.error(f"Unexpected error: {error}")
        logger.error(traceback.format_exc())
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
            # Test authentication
            auth_valid = auth.validate_authentication()
            
            return jsonify({
                'status': 'healthy',
                'authentication': 'valid' if auth_valid else 'invalid',
                'sisense_url': Config.get_sisense_base_url(),
                'timestamp': utils.time.time()
            })
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return jsonify({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': utils.time.time()
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
            logger.error(f"Login failed: {e}")
            raise
    
    @app.route('/api/auth/validate', methods=['GET'])
    def validate_auth():
        """Validate current authentication."""
        try:
            is_valid = auth.validate_authentication()
            return jsonify({
                'valid': is_valid,
                'timestamp': utils.time.time()
            })
        except Exception as e:
            logger.error(f"Auth validation failed: {e}")
            raise
    
    # Data models endpoints (v2)
    @app.route('/api/datamodels', methods=['GET'])
    def list_datamodels():
        """List all data models."""
        try:
            model_type = request.args.get('type')
            models = datamodels.list_models(model_type)
            return jsonify({
                'data': models,
                'count': len(models),
                'type_filter': model_type
            })
        except Exception as e:
            logger.error(f"Failed to list data models: {e}")
            raise
    
    @app.route('/api/datamodels/<model_oid>', methods=['GET'])
    def get_datamodel(model_oid):
        """Get specific data model by OID."""
        try:
            model = datamodels.get_model(model_oid)
            return jsonify(model)
        except Exception as e:
            logger.error(f"Failed to get data model {model_oid}: {e}")
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
            logger.error(f"Failed to get tables for model {model_oid}: {e}")
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
            logger.error(f"Failed to get columns for model {model_oid}: {e}")
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
            logger.error(f"Failed to export schema: {e}")
            raise
    
    # Connections endpoints (v2)
    @app.route('/api/connections', methods=['GET'])
    def list_connections():
        """List all connections."""
        try:
            connection_type = request.args.get('type')
            include_credentials = request.args.get('credentials', 'false').lower() == 'true'
            
            connection_list = connections.list_connections(connection_type, include_credentials)
            return jsonify({
                'data': connection_list,
                'count': len(connection_list),
                'type_filter': connection_type
            })
        except Exception as e:
            logger.error(f"Failed to list connections: {e}")
            raise
    
    @app.route('/api/connections/<connection_id>', methods=['GET'])
    def get_connection(connection_id):
        """Get specific connection by ID."""
        try:
            include_credentials = request.args.get('credentials', 'false').lower() == 'true'
            connection = connections.get_connection(connection_id, include_credentials)
            return jsonify(connection)
        except Exception as e:
            logger.error(f"Failed to get connection {connection_id}: {e}")
            raise
    
    @app.route('/api/connections/<connection_id>/test', methods=['POST'])
    def test_connection(connection_id):
        """Test connection."""
        try:
            test_result = connections.test_connection(connection_id)
            return jsonify(test_result)
        except Exception as e:
            logger.error(f"Failed to test connection {connection_id}: {e}")
            raise
    
    # Dashboards endpoints (v1)
    @app.route('/api/dashboards', methods=['GET'])
    def list_dashboards():
        """List all dashboards."""
        try:
            owner = request.args.get('owner')
            shared = request.args.get('shared')
            if shared:
                shared = shared.lower() == 'true'
            fields = request.args.getlist('fields')
            
            dashboard_list = dashboards.list_dashboards(owner, shared, fields)
            return jsonify({
                'data': dashboard_list,
                'count': len(dashboard_list),
                'owner_filter': owner,
                'shared_filter': shared
            })
        except Exception as e:
            logger.error(f"Failed to list dashboards: {e}")
            raise
    
    @app.route('/api/dashboards/<dashboard_id>', methods=['GET'])
    def get_dashboard(dashboard_id):
        """Get specific dashboard by ID."""
        try:
            fields = request.args.getlist('fields')
            dashboard = dashboards.get_dashboard(dashboard_id, fields)
            return jsonify(dashboard)
        except Exception as e:
            logger.error(f"Failed to get dashboard {dashboard_id}: {e}")
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
            logger.error(f"Failed to get widgets for dashboard {dashboard_id}: {e}")
            raise
    
    @app.route('/api/dashboards/<dashboard_id>/summary', methods=['GET'])
    def get_dashboard_summary(dashboard_id):
        """Get dashboard summary."""
        try:
            summary = dashboards.get_dashboard_summary(dashboard_id)
            return jsonify(summary)
        except Exception as e:
            logger.error(f"Failed to get dashboard summary {dashboard_id}: {e}")
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
            logger.error(f"Failed to get widget {widget_id}: {e}")
            raise
    
    @app.route('/api/widgets/<widget_id>/jaql', methods=['GET'])
    def get_widget_jaql(widget_id):
        """Get JAQL query for a widget."""
        try:
            widget_jaql = widgets.get_widget_jaql(widget_id)
            return jsonify(widget_jaql)
        except Exception as e:
            logger.error(f"Failed to get JAQL for widget {widget_id}: {e}")
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
            logger.error(f"Failed to get data for widget {widget_id}: {e}")
            raise
    
    @app.route('/api/widgets/<widget_id>/summary', methods=['GET'])
    def get_widget_summary(widget_id):
        """Get widget summary."""
        try:
            summary = widgets.get_widget_summary(widget_id)
            return jsonify(summary)
        except Exception as e:
            logger.error(f"Failed to get widget summary {widget_id}: {e}")
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
            logger.error(f"Failed to execute SQL query on {datasource}: {e}")
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
            logger.error(f"Failed to validate SQL query: {e}")
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
            logger.error(f"Failed to execute JAQL query on {datasource}: {e}")
            raise
    
    @app.route('/api/datasources/<datasource>/jaql/metadata', methods=['GET'])
    def get_jaql_metadata(datasource):
        """Get JAQL metadata for datasource."""
        try:
            table_name = request.args.get('table')
            metadata = jaql.get_jaql_metadata(datasource, table_name)
            return jsonify(metadata)
        except Exception as e:
            logger.error(f"Failed to get JAQL metadata for {datasource}: {e}")
            raise
    
    @app.route('/api/datasources/<datasource>/catalog', methods=['GET'])
    def get_datasource_catalog(datasource):
        """Get complete catalog for datasource."""
        try:
            catalog = jaql.get_datasource_catalog(datasource)
            return jsonify(catalog)
        except Exception as e:
            logger.error(f"Failed to get catalog for {datasource}: {e}")
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
            logger.error(f"Failed to search dashboards: {e}")
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
            logger.error(f"Failed to search data models: {e}")
            raise
    
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

    logger.info("Flask application configured successfully")
    return app


# Create application instance
app = create_app()


if __name__ == '__main__':
    # Run development server
    app.run(
        host='0.0.0.0',
        port=Config.FLASK_PORT,
        debug=Config.FLASK_DEBUG
    )