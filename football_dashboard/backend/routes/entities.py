"""
Entities API Routes
Handles clubs, academies, schools CRUD operations
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from database import get_db_connection

entities_bp = Blueprint('entities', __name__)


def _get_user_role(user_id):
    """Get user role and entity_id from database.
    
    Returns tuple: (role, entity_id) or (None, None) if user not found.
    """
    try:
        conn = get_db_connection()
        if not conn:
            return None, None
        cursor = conn.cursor()
        cursor.execute("SELECT role, entity_id FROM users WHERE id = %s", (user_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        # Safely handle None result
        if result is None:
            return None, None
        return (result[0], result[1]) if result else (None, None)
    except Exception as e:
        print(f"Error getting user role: {e}")
        return None, None


def _check_superadmin_access(user_id):
    """Check if user is superadmin.
    
    Returns True if user has superadmin role, False otherwise.
    """
    role, _ = _get_user_role(user_id)
    return role == 'superadmin'


# ==================== CLUBS ====================

@entities_bp.route('/clubs', methods=['GET'])
@jwt_required()
def get_clubs():
    """Get all clubs - accessible by all authenticated users"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM clubs ORDER BY name")
        clubs = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Convert datetime to string
        for club in clubs:
            if club.get('created_at'):
                club['created_at'] = club['created_at'].isoformat()
            if club.get('updated_at'):
                club['updated_at'] = club['updated_at'].isoformat()
        
        return jsonify(clubs), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@entities_bp.route('/clubs', methods=['POST'])
@jwt_required()
def create_club():
    """Create a new club - superadmin only"""
    current_user_id = get_jwt_identity()
    
    # Check if user is superadmin
    if not _check_superadmin_access(current_user_id):
        return jsonify({'error': 'Access denied. Superadmin only.'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Validate required fields
    club_name = data.get('name')
    if not club_name:
        return jsonify({'error': 'Club name is required'}), 400
    
    # Input sanitization - limit name length and strip whitespace
    if club_name and len(club_name.strip()) > 255:
        return jsonify({'error': 'Club name too long (max 255 chars)'}), 400
    club_name = club_name.strip()
    
    # Validate short_name - max 50 chars
    short_name = data.get('short_name', '')
    if short_name and len(short_name.strip()) > 50:
        return jsonify({'error': 'Short name too long (max 50 chars)'}), 400
    
    # Validate founded_year - must be reasonable 4-digit number
    founded_year = data.get('founded_year')
    if founded_year is not None:
        try:
            founded_year = int(founded_year)
            current_year = datetime.now().year
            if founded_year < 1800 or founded_year > current_year + 5:
                return jsonify({'error': f'Founded year must be between 1800 and {current_year + 5}'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid founded_year format'}), 400
    
    # Validate phone format (basic - allows digits, spaces, dashes, plus, parentheses)
    phone = data.get('phone', '')
    if phone and not all(c.isdigit() or c in ' +-()' for c in phone):
        return jsonify({'error': 'Invalid phone format'}), 400
    
    # Validate email format if provided
    email = data.get('email', '')
    if email and '@' not in email:
        return jsonify({'error': 'Invalid email format'}), 400
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            INSERT INTO clubs (name, short_name, address, phone, email, stadium_name, founded_year)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (club_name, data.get('short_name'), data.get('address'), 
              data.get('phone'), data.get('email'), data.get('stadium_name'), 
              data.get('founded_year')))
        conn.commit()
        club_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return jsonify({'message': 'Club created', 'club_id': club_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@entities_bp.route('/clubs/<int:club_id>', methods=['PUT'])
@jwt_required()
def update_club(club_id):
    """Update a club - superadmin only"""
    current_user_id = get_jwt_identity()
    
    if not _check_superadmin_access(current_user_id):
        return jsonify({'error': 'Access denied. Superadmin only.'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            UPDATE clubs SET name=%s, short_name=%s, address=%s, phone=%s, 
            email=%s, stadium_name=%s, founded_year=%s WHERE id=%s
        """, (data.get('name'), data.get('short_name'), data.get('address'),
              data.get('phone'), data.get('email'), data.get('stadium_name'),
              data.get('founded_year'), club_id))
        conn.commit()
        
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Club not found'}), 404
        
        cursor.close()
        conn.close()
        return jsonify({'message': 'Club updated'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@entities_bp.route('/clubs/<int:club_id>', methods=['DELETE'])
@jwt_required()
def delete_club(club_id):
    """Delete a club - superadmin only"""
    current_user_id = get_jwt_identity()
    
    if not _check_superadmin_access(current_user_id):
        return jsonify({'error': 'Access denied. Superadmin only.'}), 403
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # Check if club exists
        cursor.execute("SELECT id FROM clubs WHERE id = %s", (club_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'error': 'Club not found'}), 404
        
        cursor.execute("DELETE FROM clubs WHERE id=%s", (club_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'message': 'Club deleted'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== ACADEMIES ====================

@entities_bp.route('/academies', methods=['GET'])
@jwt_required()
def get_academies():
    """Get all academies - accessible by all authenticated users"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM academies ORDER BY name")
        academies = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Convert datetime to string
        for academy in academies:
            if academy.get('created_at'):
                academy['created_at'] = academy['created_at'].isoformat()
            if academy.get('updated_at'):
                academy['updated_at'] = academy['updated_at'].isoformat()
        
        return jsonify(academies), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@entities_bp.route('/academies', methods=['POST'])
@jwt_required()
def create_academy():
    """Create a new academy - superadmin only"""
    current_user_id = get_jwt_identity()
    
    if not _check_superadmin_access(current_user_id):
        return jsonify({'error': 'Access denied. Superadmin only.'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    if not data.get('name'):
        return jsonify({'error': 'Academy name is required'}), 400
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            INSERT INTO academies (name, address, phone, email, director_name, established_year)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (data.get('name'), data.get('address'), data.get('phone'),
              data.get('email'), data.get('director_name'), data.get('established_year')))
        conn.commit()
        academy_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return jsonify({'message': 'Academy created', 'academy_id': academy_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@entities_bp.route('/academies/<int:academy_id>', methods=['PUT'])
@jwt_required()
def update_academy(academy_id):
    """Update an academy - superadmin only"""
    current_user_id = get_jwt_identity()
    
    if not _check_superadmin_access(current_user_id):
        return jsonify({'error': 'Access denied. Superadmin only.'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            UPDATE academies SET name=%s, address=%s, phone=%s, email=%s, 
            director_name=%s, established_year=%s WHERE id=%s
        """, (data.get('name'), data.get('address'), data.get('phone'),
              data.get('email'), data.get('director_name'), 
              data.get('established_year'), academy_id))
        conn.commit()
        
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Academy not found'}), 404
        
        cursor.close()
        conn.close()
        return jsonify({'message': 'Academy updated'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@entities_bp.route('/academies/<int:academy_id>', methods=['DELETE'])
@jwt_required()
def delete_academy(academy_id):
    """Delete an academy - superadmin only"""
    current_user_id = get_jwt_identity()
    
    if not _check_superadmin_access(current_user_id):
        return jsonify({'error': 'Access denied. Superadmin only.'}), 403
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # Check if academy exists
        cursor.execute("SELECT id FROM academies WHERE id = %s", (academy_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'error': 'Academy not found'}), 404
        
        cursor.execute("DELETE FROM academies WHERE id=%s", (academy_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'message': 'Academy deleted'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== SCHOOLS ====================

@entities_bp.route('/schools', methods=['GET'])
@jwt_required()
def get_schools():
    """Get all schools - accessible by all authenticated users"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM schools ORDER BY name")
        schools = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Convert datetime to string
        for school in schools:
            if school.get('created_at'):
                school['created_at'] = school['created_at'].isoformat()
            if school.get('updated_at'):
                school['updated_at'] = school['updated_at'].isoformat()
        
        return jsonify(schools), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@entities_bp.route('/schools', methods=['POST'])
@jwt_required()
def create_school():
    """Create a new school - superadmin only"""
    current_user_id = get_jwt_identity()
    
    if not _check_superadmin_access(current_user_id):
        return jsonify({'error': 'Access denied. Superadmin only.'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    if not data.get('name'):
        return jsonify({'error': 'School name is required'}), 400
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            INSERT INTO schools (name, address, phone, email, established_year)
            VALUES (%s, %s, %s, %s, %s)
        """, (data.get('name'), data.get('address'), data.get('phone'),
              data.get('email'), data.get('established_year')))
        conn.commit()
        school_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return jsonify({'message': 'School created', 'school_id': school_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@entities_bp.route('/schools/<int:school_id>', methods=['PUT'])
@jwt_required()
def update_school(school_id):
    """Update a school - superadmin only"""
    current_user_id = get_jwt_identity()
    
    if not _check_superadmin_access(current_user_id):
        return jsonify({'error': 'Access denied. Superadmin only.'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            UPDATE schools SET name=%s, address=%s, phone=%s, email=%s, 
            established_year=%s WHERE id=%s
        """, (data.get('name'), data.get('address'), data.get('phone'),
              data.get('email'), data.get('established_year'), school_id))
        conn.commit()
        
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({'error': 'School not found'}), 404
        
        cursor.close()
        conn.close()
        return jsonify({'message': 'School updated'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@entities_bp.route('/schools/<int:school_id>', methods=['DELETE'])
@jwt_required()
def delete_school(school_id):
    """Delete a school - superadmin only"""
    current_user_id = get_jwt_identity()
    
    if not _check_superadmin_access(current_user_id):
        return jsonify({'error': 'Access denied. Superadmin only.'}), 403
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # Check if school exists
        cursor.execute("SELECT id FROM schools WHERE id = %s", (school_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'error': 'School not found'}), 404
        
        cursor.execute("DELETE FROM schools WHERE id=%s", (school_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'message': 'School deleted'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== VENUES ====================

@entities_bp.route('/venues', methods=['GET'])
@jwt_required()
def get_venues():
    """Get all venues - accessible by all users"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM venues ORDER BY name")
        venues = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(venues), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== AUDIT LOGS ====================

@entities_bp.route('/audit-logs', methods=['GET'])
@jwt_required()
def get_audit_logs():
    """Get audit logs - superadmin only"""
    current_user_id = get_jwt_identity()
    
    if not _check_superadmin_access(current_user_id):
        return jsonify({'error': 'Access denied. Superadmin only.'}), 403
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM audit_logs 
            ORDER BY created_at DESC 
            LIMIT 100
        """)
        logs = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Convert datetime to string
        for log in logs:
            if log.get('created_at'):
                log['created_at'] = log['created_at'].isoformat()
        
        return jsonify(logs), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
