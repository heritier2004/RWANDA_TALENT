from flask import Blueprint, jsonify, request
from database import get_db_connection
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

announcements_bp = Blueprint('announcements', __name__)

@announcements_bp.route('', methods=['GET'])
def get_announcements():
    """Get all announcements visible to the current user role"""
    role = request.args.get('role', 'all')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # Fetch announcements for 'all' or specific role
        cursor.execute(
            "SELECT a.*, u.username as author FROM announcements a "
            "LEFT JOIN users u ON a.author_id = u.id "
            "WHERE a.target_role = 'all' OR a.target_role = %s "
            "ORDER BY a.created_at DESC LIMIT 20",
            (role,)
        )
        announcements = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(announcements), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@announcements_bp.route('', methods=['POST'])
@jwt_required()
def create_announcement():
    """Create a new announcement (FERWAFA/Admin only)"""
    user_id = get_jwt_identity()
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT role FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    
    if not user or user['role'] not in ['ferwafa', 'superadmin']:
        cursor.close()
        conn.close()
        return jsonify({'error': 'Unauthorized'}), 403
        
    data = request.get_json()
    if not data or not data.get('title') or not data.get('content'):
        cursor.close()
        conn.close()
        return jsonify({'error': 'Missing title or content'}), 400
        
    try:
        cursor.execute(
            "INSERT INTO announcements (title, content, category, target_role, author_id) VALUES (%s, %s, %s, %s, %s)",
            (data['title'], data['content'], data.get('category', 'General'), data.get('target_role', 'all'), user_id)
        )
        conn.commit()
        ann_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return jsonify({'message': 'Announcement published successfully', 'id': ann_id}), 201
    except Exception as e:
        cursor.close()
        conn.close()
        return jsonify({'error': str(e)}), 500
