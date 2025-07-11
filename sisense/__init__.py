"""
Sisense module for Flask integration.

This module provides a complete interface to the Sisense REST API v1/v2
with production-grade error handling, authentication, and data access.
"""

from . import auth
from . import datamodels
from . import connections
from . import dashboards
from . import widgets
from . import sql
from . import jaql
from . import utils
from . import logger
from . import enhanced_auth

__version__ = '2.0.0'
__all__ = [
    'auth',
    'datamodels', 
    'connections',
    'dashboards',
    'widgets',
    'sql',
    'jaql',
    'utils',
    'logger',
    'enhanced_auth'
]
