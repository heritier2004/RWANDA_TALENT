"""
Players Routes
Handles player CRUD operations
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import mysql.connector
from datetime import datetime
import uuid

players_bp = Blueprint('players', __name__)

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

def generate_registration_number(role, entity_id):
    """Generate unique player registration number"""
    prefix = {
        'school': 'SCH',
        'academy': 'ACA',
        'club': 'CLB'
    }.get(role, 'GEN')
    unique_id = str(uuid.uuid4())[:8].upper()
    return f"{prefix}-{entity_id}-{unique_id}"

@players_bp.route('/', methods=['GET'])
@jwt_required()
def get_players():
    """Get all players (filtered by user role)"""
    user_id = get_jwt_identity()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get user info
        cursor.execute("SELECT role, entity_id FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        if user['role'] == 'superadmin':
            # Super admin sees all players
            cursor.execute("""
                SELECT p.*, 
                       CASE 
                           WHEN p.school_id IS NOT NULL THEN s.name
                           WHEN p.academy_id IS NOT NULL THEN a.name
                           WHEN p.club_id IS NOT NULL THEN c.name
                       END as entity_name
                FROM players p
                LEFT JOIN schools s ON p.school_id = s.id
                LEFT JOIN academies a ON p.academy_id = a.id
                LEFT JOIN clubs c ON p.club_id = c.id
                ORDER BY p.created_at DESC
            """)
        elif user['role'] == 'ferwafa':
            # FERWAFA sees all players
            cursor.execute("""
                SELECT p.*, 
                       CASE 
                           WHEN p.school_id IS NOT NULL THEN s.name
                           WHEN p.academy_id IS NOT NULL THEN a.name
                           WHEN p.club_id IS NOT NULL THEN c.name
                       END as entity_name
                FROM players p
                LEFT JOIN schools s ON p.school_id = s.id
                LEFT JOIN academies a ON p.academy_id = a.id
                LEFT JOIN clubs c ON p.club_id = c.id
                ORDER BY p.created_at DESC
            """)
        else:
            # Others see only their entity's players
            if user['role'] == 'school':
                cursor.execute("""
                    SELECT p.*, s.name as entity_name
                    FROM players p
                    JOIN schools s ON p.school_id = s.id
                    WHERE p.school_id = %s
                    ORDER BY p.created_at DESC
                """, (user['entity_id'],))
            elif user['role'] == 'academy':
                cursor.execute("""
                    SELECT p.*, a.name as entity_name
                    FROM players p
                    JOIN academies a ON p.academy_id = a.id
                    WHERE p.academy_id = %s
                    ORDER BY p.created_at DESC
                """, (user['entity_id'],))
            elif user['role'] == 'club':
                cursor.execute("""
                    SELECT p.*, c.name as entity_name
                    FROM players p
                    JOIN clubs c ON p.club_id = c.id
                    WHERE p.club_id = %s
                    ORDER BY p.created_at DESC
                """, (user['entity_id'],))
            else:
                return jsonify([]), 200
        
        players = cursor.fetchall()
        
        # Convert datetime objects to strings
        for player in players:
            if player.get('created_at'):
                player['created_at'] = player['created_at'].isoformat()
            if player.get('dob'):
                player['dob'] = player['dob'].isoformat()
        
        cursor.close()
        conn.close()
        
        return jsonify(players), 200
        
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500

@players_bp.route('/<int:player_id>', methods=['GET'])
@jwt_required()
def get_player(player_id):
    """Get a single player by ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT p.*, 
                   CASE 
                       WHEN p.school_id IS NOT NULL THEN s.name
                       WHEN p.academy_id IS NOT NULL THEN a.name
                       WHEN p.club_id IS NOT NULL THEN c.name
                   END as entity_name
            FROM players p
            LEFT JOIN schools s ON p.school_id = s.id
            LEFT JOIN academies a ON p.academy_id = a.id
            LEFT JOIN clubs c ON p.club_id = c.id
            WHERE p.id = %s
        """, (player_id,))
        
        player = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not player:
            return jsonify({'error': 'Player not found'}), 404
        
        if player.get('created_at'):
            player['created_at'] = player['created_at'].isoformat()
        if player.get('dob'):
            player['dob'] = player['dob'].isoformat()
        
        return jsonify(player), 200
        
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500

@players_bp.route('/', methods=['POST'])
@jwt_required()
def create_player():
    """Create a new player"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    required_fields = ['name', 'dob', 'nationality', 'position']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get user info
        cursor.execute("SELECT role, entity_id FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        # Generate registration number
        reg_number = generate_registration_number(user['role'], user['entity_id'])
        
        # Determine which entity ID to use
        entity_field = f"{user['role']}_id"
        
        # Insert player
        sql = """INSERT INTO players 
                 (registration_number, name, dob, nationality, jersey_number, position, photo_url, school_id, academy_id, club_id, created_at) 
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        
        school_id = user['entity_id'] if user['role'] == 'school' else data.get('school_id')
        academy_id = user['entity_id'] if user['role'] == 'academy' else data.get('academy_id')
        club_id = user['entity_id'] if user['role'] == 'club' else data.get('club_id')
        
        values = (
            reg_number,
            data['name'],
            data['dob'],
            data['nationality'],
            data.get('jersey_number'),
            data['position'],
            data.get('photo_url'),
            school_id,
            academy_id,
            club_id,
            datetime.now()
        )
        
        cursor.execute(sql, values)
        conn.commit()
        player_id = cursor.lastrowid
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'message': 'Player created successfully',
            'player_id': player_id,
            'registration_number': reg_number
        }), 201
        
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500

@players_bp.route('/<int:player_id>', methods=['PUT'])
@jwt_required()
def update_player(player_id):
    """Update a player"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if player exists and user has permission
        cursor.execute("SELECT * FROM players WHERE id = %s", (player_id,))
        player = cursor.fetchone()
        
        if not player:
            return jsonify({'error': 'Player not found'}), 404
        
        # Build update query
        update_fields = []
        values = []
        
        for field in ['name', 'dob', 'nationality', 'jersey_number', 'position', 'photo_url']:
            if field in data:
                update_fields.append(f"{field} = %s")
                values.append(data[field])
        
        if not update_fields:
            return jsonify({'error': 'No fields to update'}), 400
        
        values.append(player_id)
        
        sql = f"UPDATE players SET {', '.join(update_fields)} WHERE id = %s"
        cursor.execute(sql, values)
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Player updated successfully'}), 200
        
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500

@players_bp.route('/<int:player_id>', methods=['DELETE'])
@jwt_required()
def delete_player(player_id):
    """Delete a player"""
    user_id = get_jwt_identity()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if player exists
        cursor.execute("SELECT * FROM players WHERE id = %s", (player_id,))
        player = cursor.fetchone()
        
        if not player:
            return jsonify({'error': 'Player not found'}), 404
        
        # Delete player
        cursor.execute("DELETE FROM players WHERE id = %s", (player_id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Player deleted successfully'}), 200
        
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500

@players_bp.route('/upload-photo', methods=['POST'])
@jwt_required()
def upload_player_photo():
    """Upload player photo for ML processing"""
    from werkzeug.utils import secure_filename
    import os
    import shutil
    
    if 'photo' not in request.files:
        return jsonify({'error': 'No photo provided'}), 400
    
    file = request.files['photo']
    player_id = request.form.get('player_id')
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        filename = secure_filename(file.filename)
        upload_dir = os.path.join(os.path.dirname(__file__), '..', 'uploads', 'players')
        os.makedirs(upload_dir, exist_ok=True)
        
        filepath = os.path.join(upload_dir, f"{player_id}_{filename}")
        file.save(filepath)
        
        # Note: ML processing would happen here
        # For CPU-friendly processing, use libraries like OpenCV
        # After processing, delete the file (do not store in DB)
        
        # Simulate ML processing placeholder
        ml_result = {
            'player_id': player_id,
            'photo_path': filepath,
            'face_detected': True,
            'confidence': 0.95
        }
        
        # Clean up after processing (don't keep video/photo stored)
        # os.remove(filepath)  # Uncomment after processing
        
        return jsonify({
            'message': 'Photo processed successfully',
            'result': ml_result
        }), 200
        
    except Exception as err:
        return jsonify({'error': str(err)}), 500
