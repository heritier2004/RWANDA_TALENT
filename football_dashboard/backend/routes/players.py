"""
Players Routes
Handles player CRUD operations
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import uuid
import mysql.connector
from database import get_db_connection

players_bp = Blueprint('players', __name__)

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
    
    # Convert string user_id to int for database query
    # Validate that user_id is a valid positive integer
    try:
        if not user_id:
            return jsonify({'error': 'User ID not found in token'}), 401
        
        user_id_int = int(user_id)
        
        # Ensure user_id is a positive integer
        if user_id_int <= 0:
            return jsonify({'error': 'Invalid user ID: must be a positive integer'}), 401
            
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid user identity: must be a valid integer'}), 401
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get user info - use converted integer user_id_int
        cursor.execute("SELECT role, entity_id FROM users WHERE id = %s", (user_id_int,))
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
        return jsonify({'error': 'Missing required fields: name, dob, nationality, position'}), 400
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # Get user info
        cursor.execute("SELECT role, entity_id FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user_role = user.get('role')
        user_entity_id = user.get('entity_id')
        
        # Generate registration number - validate entity_id is set for entity-specific roles
        # For school/academy/club roles, entity_id must be set
        # For superadmin/ferwafa/scout roles, entity_id can be provided in request data
        if user_role in ['school', 'academy', 'club'] and user_entity_id is None:
            return jsonify({'error': f'User with role {user_role} must have an entity_id assigned. Please contact administrator.'}), 400
        
        # For entity-specific roles, use the user's entity_id
        # For other roles (superadmin, ferwafa, scout), use provided values from request
        entity_id_for_reg = user_entity_id if user_role in ['school', 'academy', 'club'] else data.get('school_id') or data.get('academy_id') or data.get('club_id')
        
        if entity_id_for_reg is None:
            return jsonify({'error': 'Entity ID is required. Please specify school_id, academy_id, or club_id.'}), 400
        
        reg_number = generate_registration_number(user_role, entity_id_for_reg)
        
        # Determine which entity ID to use based on role
        school_id = None
        academy_id = None
        club_id = None
        
        def safe_int(val):
            try:
                if not val or str(val).strip() == "" or str(val).lower() == "null":
                    return None
                i = int(val)
                return i if i > 0 else None
            except (ValueError, TypeError):
                return None

        if user_role == 'school':
            school_id = user_entity_id
        elif user_role == 'academy':
            academy_id = user_entity_id
        elif user_role == 'club':
            club_id = user_entity_id
        else:
            # For other roles (superadmin, ferwafa, scout), use provided values from request
            school_id = safe_int(data.get('school_id'))
            academy_id = safe_int(data.get('academy_id'))
            club_id = safe_int(data.get('club_id'))
        
        # FINAL SAFETY CHECK: Does the entity actually exist in the DB?
        def check_exists(table, eid):
            if eid is None: return True
            cursor.execute(f"SELECT id FROM {table} WHERE id = %s", (eid,))
            return cursor.fetchone() is not None

        if not check_exists('schools', school_id):
            return jsonify({'error': f'Your account is linked to a non-existent School (ID: {school_id}). Please contact an administrator.'}), 400
        if not check_exists('academies', academy_id):
            return jsonify({'error': f'Your account is linked to a non-existent Academy (ID: {academy_id}). Please contact an administrator.'}), 400
        if not check_exists('clubs', club_id):
            return jsonify({'error': f'Your account is linked to a non-existent Club (ID: {club_id}). Please contact an administrator.'}), 400
        
        # Insert player
        sql = """INSERT INTO players 
                 (registration_number, name, dob, nationality, jersey_number, position, photo_url, 
                  height_cm, weight_kg, district, sector, cell, village, 
                  school_id, academy_id, club_id, created_at) 
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        
        values = (
            reg_number,
            data['name'],
            data['dob'],
            data['nationality'],
            data.get('jersey_number'),
            data['position'],
            data.get('photo_url'),
            data.get('height_cm'),
            data.get('weight_kg'),
            data.get('district'),
            data.get('sector'),
            data.get('cell'),
            data.get('village'),
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
        
        # Build update query with whitelist to prevent SQL injection
        allowed_fields = {'name', 'dob', 'nationality', 'jersey_number', 'position', 'photo_url', 
                          'height_cm', 'weight_kg', 'district', 'sector', 'cell', 'village'}
        update_fields = []
        values = []
        
        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = %s")
                values.append(data[field])
        
        if not update_fields:
            return jsonify({'error': 'No fields to update'}), 400
        
        values.append(player_id)
        
        # Build query safely using validated field names
        set_clause = ', '.join(update_fields)
        sql = f"UPDATE players SET {set_clause} WHERE id = %s"
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
    """Upload player photo permanently"""
    from werkzeug.utils import secure_filename
    import os
    
    if 'photo' not in request.files:
        return jsonify({'error': 'No photo provided'}), 400
    
    file = request.files['photo']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        filename = secure_filename(file.filename)
        # Use a timestamp to prevent overwriting- same file names
        filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
        
        # Absolute path to static/uploads/players
        upload_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'uploads', 'players')
        os.makedirs(upload_dir, exist_ok=True)
        
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        
        # Publicly accessible URL
        public_url = f"/static/uploads/players/{filename}"
        
        return jsonify({
            'message': 'Photo uploaded successfully',
            'photo_url': public_url
        }), 200
        
    except Exception as err:
        return jsonify({'error': str(err)}), 500
