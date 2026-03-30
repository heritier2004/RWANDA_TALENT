"""
Centralized database configuration

WARNING: Default values are for development only.
Ensure production deployment sets these environment variables:
  - DB_HOST: Database server hostname
  - DB_USER: Database username  
  - DB_PASSWORD: Database password (MUST be set in production!)
  - DB_NAME: Database name
"""
import os
import sys
import warnings
import mysql.connector
from mysql.connector import Error

# Get database configuration from environment variables
# Production MUST set these variables!
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD'),  # No default - must be set explicitly
    'database': os.environ.get('DB_NAME', 'football_dashboard'),
    'charset': 'utf8mb4'
}

# Check for production environment and enforce security requirements
is_production = os.environ.get('FLASK_ENV', '').lower() == 'production'

if is_production:
    # In production, password MUST be set
    if not DB_CONFIG['password']:
        print("CRITICAL ERROR: DB_PASSWORD environment variable is not set!")
        print("Production deployments require a database password for security.")
        print("Please set DB_PASSWORD environment variable before starting the application.")
        sys.exit(1)
    
    # In production, warn if using default root user
    if DB_CONFIG['user'] == 'root':
        warnings.warn(
            "WARNING: Using 'root' database user in production is not recommended. "
            "Create a dedicated database user with minimal required permissions."
        )


def get_db_connection():
    """Get database connection"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"Database connection error: {e}")
        return None
