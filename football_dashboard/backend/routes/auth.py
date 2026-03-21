"""
Authentication Routes
Handles user login, registration, and session management
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask_bcrypt import Bcrypt
import mysql.connector
from datetime import datetime

auth_bp = Blueprint('auth', __name__)
bcrypt = Bcrypt()

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'football_dashboard',
    'charset': 'utf8mb4'
}

def get_db_connection():
    """Create database connection"""
    return mysql.connector.connect(**DB_CONFIG)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    
    required_fields = ['username', 'password', 'email', 'role']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Validate role
    valid_roles = ['school', 'academy', 'club', 'scout', 'ferwafa', 'superadmin']
    if data['role'] not in valid_roles:
        return jsonify({'error': 'Invalid role'}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if username exists
        cursor.execute("SELECT id FROM users WHERE username = %s", (data['username'],))
        if cursor.fetchone():
            return jsonify({'error': 'Username already exists'}), 409
        
        # Hash password
        hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        
        # Insert user
        sql = """INSERT INTO users (username, email, password, role, entity_id, created_at) 
                  VALUES (%s, %s, %s, %s, %s, %s)"""
        values = (
            data['username'],
            data['email'],
            hashed_password,
            data['role'],
            data.get('entity_id'),
            datetime.now()
        )
        
        cursor.execute(sql, values)
        conn.commit()
        user_id = cursor.lastrowid
        
        cursor.close()
        conn.close()
        
        # Create access token
        access_token = create_access_token(identity=user_id)
        
        return jsonify({
            'message': 'User registered successfully',
            'user_id': user_id,
            'access_token': access_token,
            'role': data['role']
        }), 201
        
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login"""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Missing username or password'}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get user by username
        cursor.execute("SELECT * FROM users WHERE username = %s", (data['username'],))
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Check password
        if not bcrypt.check_password_hash(user['password'], data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Create access token
        access_token = create_access_token(identity=user['id'])
        
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'role': user['role'],
                'entity_id': user['entity_id']
            }
        }), 200
        
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """User logout - client should discard token"""
    return jsonify({'message': 'Logout successful'}), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current authenticated user"""
    user_id = get_jwt_identity()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT id, username, email, role, entity_id, created_at FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify(user), 200
        
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or not data.get('current_password') or not data.get('new_password'):
        return jsonify({'error': 'Missing password fields'}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get current password
        cursor.execute("SELECT password FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not bcrypt.check_password_hash(user['password'], data['current_password']):
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        # Update password
        hashed_password = bcrypt.generate_password_hash(data['new_password']).decode('utf-8')
        cursor.execute("UPDATE users SET password = %s WHERE id = %s", (hashed_password, user_id))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Password changed successfully'}), 200
        
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500

# Role-based access helpers
@auth_bp.route('/roles', methods=['GET'])
def get_roles():
    """Get all available roles"""
    roles = [
        {'id': 'school', 'name': 'School', 'description': 'School football team'},
        {'id': 'academy', 'name': 'Academy', 'description': 'Football academy'},
        {'id': 'club', 'name': 'Club', 'description': 'Football club'},
        {'id': 'scout', 'name': 'Scout', 'description': 'Talent scout'},
        {'id': 'ferwafa', 'name': 'FERWAFA', 'description': 'Rwanda Football Association'},
        {'id': 'superadmin', 'name': 'Super Admin', 'description': 'System administrator'}
    ]
    return jsonify(roles), 200
