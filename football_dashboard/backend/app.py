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

# Import routes
from routes.auth import auth_bp
from routes.players import players_bp
from routes.matches import matches_bp
from routes.stats import stats_bp
from routes.dashboard import dashboard_bp

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'football-dashboard-secret-key-2024')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-football-secret-key-2024')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Initialize extensions
CORS(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(players_bp, url_prefix='/api/players')
app.register_blueprint(matches_bp, url_prefix='/api/matches')
app.register_blueprint(stats_bp, url_prefix='/api/stats')
app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')

# Database configuration
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'database': os.environ.get('DB_NAME', 'football_dashboard'),
    'charset': 'utf8mb4'
}

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'Football Academy Management System',
        'version': '1.0.0'
    })

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
    app.run(debug=True, host='0.0.0.0', port=5000)
