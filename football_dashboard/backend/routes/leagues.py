from flask import Blueprint, jsonify, request
from database import get_db_connection
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

leagues_bp = Blueprint('leagues', __name__)

def check_ferwafa_role():
    """Helper to check if current user is ferwafa"""
    user_id = get_jwt_identity()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT role FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user and user['role'] in ['ferwafa', 'superadmin']

@leagues_bp.route('', methods=['GET'])
def get_leagues():
    """List all leagues"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM leagues ORDER BY name ASC")
        leagues = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(leagues), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@leagues_bp.route('', methods=['POST'])
@jwt_required()
def create_league():
    """Create a new league (FERWAFA only)"""
    if not check_ferwafa_role():
        return jsonify({'error': 'Unauthorized. FERWAFA access required.'}), 403
        
    data = request.get_json()
    if not data or not data.get('name') or not data.get('category') or not data.get('season'):
        return jsonify({'error': 'Missing required fields'}), 400
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO leagues (name, category, season, description) VALUES (%s, %s, %s, %s)",
            (data['name'], data['category'], data['season'], data.get('description', ''))
        )
        conn.commit()
        league_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return jsonify({'message': 'League created successfully', 'id': league_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@leagues_bp.route('/<int:league_id>', methods=['PUT'])
@jwt_required()
def update_league(league_id):
    """Update league details"""
    if not check_ferwafa_role():
        return jsonify({'error': 'Unauthorized'}), 403
        
    data = request.get_json()
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE leagues SET name=%s, category=%s, season=%s, description=%s WHERE id=%s",
            (data['name'], data['category'], data['season'], data.get('description', ''), league_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'message': 'League updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@leagues_bp.route('/<int:league_id>', methods=['DELETE'])
@jwt_required()
def delete_league(league_id):
    """Delete a league"""
    if not check_ferwafa_role():
        return jsonify({'error': 'Unauthorized'}), 403
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM leagues WHERE id=%s", (league_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'message': 'League deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
