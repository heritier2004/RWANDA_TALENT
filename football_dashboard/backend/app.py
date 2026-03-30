"""
Football Academy Management System - Flask Backend
Main application entry point
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from datetime import timedelta
import os
import sys
import warnings

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    warnings.warn("python-dotenv not installed. Environment variables must be set manually.")


def _get_secret_keys():
    """Get secret keys from environment variables.
    
    Returns tuple of (SECRET_KEY, JWT_SECRET_KEY).
    Raises ValueError if keys are not set - no fallback defaults.
    """
    secret_key = os.environ.get('SECRET_KEY')
    jwt_secret_key = os.environ.get('JWT_SECRET_KEY')
    
    if not secret_key:
        raise ValueError('SECRET_KEY environment variable must be set!')
    if not jwt_secret_key:
        raise ValueError('JWT_SECRET_KEY environment variable must be set!')
    
    return (secret_key, jwt_secret_key)
# Set default database configuration for XAMPP/local development
# These can be overridden by environment variables
if 'DB_HOST' not in os.environ:
    os.environ['DB_HOST'] = 'localhost'
if 'DB_USER' not in os.environ:
    os.environ['DB_USER'] = 'root'
if 'DB_PASSWORD' not in os.environ:
    os.environ['DB_PASSWORD'] = ''
if 'DB_NAME' not in os.environ:
    os.environ['DB_NAME'] = 'football_dashboard'

# Import routes
from routes.auth import auth_bp
from routes.players import players_bp
from routes.matches import matches_bp
from routes.stats import stats_bp
from routes.dashboard import dashboard_bp
from routes.logs import logs_bp
from routes.ai_stats import ai_stats_bp
from routes.live_stream import live_stream_bp
from routes.entities import entities_bp
from routes.ml import ml_bp
from routes.debug import debug_bp
from routes.leagues import leagues_bp
from routes.announcements import announcements_bp
from routes.ferwafa_analytics import ferwafa_analytics_bp
from database import DB_CONFIG

import os

# Get the base directory (project root)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')
STATIC_DIR = os.path.join(os.path.dirname(__file__), 'static')
UPLOAD_P_DIR = os.path.join(STATIC_DIR, 'uploads', 'players')

# Ensure upload directories exist
os.makedirs(UPLOAD_P_DIR, exist_ok=True)

app = Flask(__name__, static_folder='static')

# Serve static frontend files
@app.route('/')
def index():
    from flask import send_from_directory
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/<path:path>')
def serve_frontend(path):
    from flask import send_from_directory
    # Skip API routes
    if path.startswith('api/'):
        return jsonify({'error': 'API endpoint not found'}), 404
    # Try to serve from frontend directory
    try:
        return send_from_directory(FRONTEND_DIR, path)
    except:
        return send_from_directory(FRONTEND_DIR, 'index.html')

# Configuration - require secret keys from environment
# Set these environment variables before running:
#   - SECRET_KEY
#   - JWT_SECRET_KEY
try:
    secret_key, jwt_secret_key = _get_secret_keys()
except ValueError as e:
    print(f"ERROR: {e}")
    print("Please set SECRET_KEY and JWT_SECRET_KEY environment variables")
    sys.exit(1)

app.config['SECRET_KEY'] = secret_key
app.config['JWT_SECRET_KEY'] = jwt_secret_key
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Initialize extensions
# Restrict CORS to specific origins for security
# In production, set CORS_ORIGINS environment variable with comma-separated list of allowed origins
cors_origins = os.environ.get('CORS_ORIGINS', 'http://localhost:5000,http://127.0.0.1:5000')
CORS(app, origins=cors_origins.split(','))
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(players_bp, url_prefix='/api/players')
app.register_blueprint(matches_bp, url_prefix='/api/matches')
app.register_blueprint(stats_bp, url_prefix='/api/stats')
app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
app.register_blueprint(logs_bp, url_prefix='/api/logs')
app.register_blueprint(ai_stats_bp, url_prefix='/api/ai')
app.register_blueprint(live_stream_bp, url_prefix='/api/live-stream')
app.register_blueprint(entities_bp, url_prefix='/api/entities')
app.register_blueprint(ml_bp, url_prefix='/api/ml')
app.register_blueprint(leagues_bp, url_prefix='/api/leagues')
app.register_blueprint(announcements_bp, url_prefix='/api/announcements')
app.register_blueprint(ferwafa_analytics_bp, url_prefix='/api/ferwafa')

# Only register debug blueprint when explicitly enabled
# Requires both FLASK_ENV != 'production' AND DEBUG=true for defense-in-depth
if os.environ.get('FLASK_ENV') != 'production' and os.environ.get('DEBUG', '').lower() == 'true':
    app.register_blueprint(debug_bp, url_prefix='/api/debug')

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'Football Academy Management System',
        'version': '1.0.0'
    })

# Database configuration - imported from database module
# Using centralized DB_CONFIG from database.py

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# Role-based access control helper
def check_role(required_roles):
    """Decorator factory for role-based access control"""
    def decorator(f):
        def wrapper(*args, **kwargs):
            from flask_jwt_extended import get_jwt_identity
            from models.user_model import get_user_by_id
            
            user_id = get_jwt_identity()
            user = get_user_by_id(user_id)
            
            if not user or user['role'] not in required_roles:
                return jsonify({'error': 'Access denied'}), 403
            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator

if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', '').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
