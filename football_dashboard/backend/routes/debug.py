"""
Debug Routes
Shows database contents for troubleshooting
WARNING: These endpoints should be disabled in production!
"""

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import get_db_connection
import os

debug_bp = Blueprint('debug', __name__)


def _is_debug_enabled():
    """Check if debug mode is enabled.
    
    Debug endpoints are only available when:
    1. FLASK_ENV is NOT 'production', AND
    2. DEBUG environment variable is set to 'true'
    
    This provides defense-in-depth protection.
    """
    flask_env = os.environ.get('FLASK_ENV', '').lower()
    debug_mode = os.environ.get('DEBUG', '').lower()
    
    # Explicitly disable in production
    if flask_env == 'production':
        return False
    
    # Only enable if DEBUG=true is explicitly set
    return debug_mode == 'true'


@debug_bp.route('/show-tables', methods=['GET'])
@jwt_required()
def show_tables():
    """Show all tables in the database - superadmin only, debug mode only"""
    
    # Guard against production environment - defense in depth
    if not _is_debug_enabled():
        return jsonify({'error': 'Debug endpoints are disabled. Set DEBUG=true and FLASK_ENV!=production to enable.'}), 403
    
    current_user_id = get_jwt_identity()
    
    # Import here to avoid circular import
    from routes.entities import _check_superadmin_access
    if not _check_superadmin_access(current_user_id):
        return jsonify({'error': 'Access denied. Superadmin only.'}), 403
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        table_names = []
        for row in tables:
            for key in row:
                table_names.append(row[key])
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'tables': table_names,
            'count': len(table_names)
        }), 200
        
    except Exception as e:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
        return jsonify({'error': str(e)}), 500


@debug_bp.route('/show-table/<table_name>', methods=['GET'])
@jwt_required()
def show_table_data(table_name):
    """Show all data in a specific table - superadmin only, debug mode only"""
    
    # Guard against production environment - defense in depth
    if not _is_debug_enabled():
        return jsonify({'error': 'Debug endpoints are disabled. Set DEBUG=true and FLASK_ENV!=production to enable.'}), 403
    
    current_user_id = get_jwt_identity()
    from routes.entities import _check_superadmin_access
    if not _check_superadmin_access(current_user_id):
        return jsonify({'error': 'Access denied. Superadmin only.'}), 403
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # Validate table name against whitelist to prevent SQL injection
        # This is a defense-in-depth measure - we validate against existing tables
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        valid_tables = [list(row.values())[0] for row in tables]
        
        # Additional validation: ensure table_name is alphanumeric (whitelist approach)
        # Only allow letters, numbers, underscores, and hyphens
        if not table_name.replace('_', '').replace('-', '').isalnum():
            return jsonify({'error': 'Invalid table name format'}), 400
        
        if table_name not in valid_tables:
            return jsonify({'error': f'Table {table_name} not found', 'valid_tables': valid_tables}), 404
        
        # Get table data - table_name is safe here due to whitelist validation above
        # We use backticks to safely quote the table name after validation
        cursor.execute(f"SELECT * FROM `{table_name}` LIMIT 50")
        rows = cursor.fetchall()
        
        # Convert datetime objects to strings
        for row in rows:
            for key, value in row.items():
                if hasattr(value, 'isoformat'):
                    row[key] = value.isoformat()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'table': table_name,
            'data': rows,
            'count': len(rows)
        }), 200
        
    except Exception as e:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
        return jsonify({'error': str(e)}), 500


@debug_bp.route('/show-players', methods=['GET'])
@jwt_required()
def show_players():
    """Show all players - superadmin only, debug mode only"""
    
    # Guard against production environment - defense in depth
    if not _is_debug_enabled():
        return jsonify({'error': 'Debug endpoints are disabled. Set DEBUG=true and FLASK_ENV!=production to enable.'}), 403
    
    current_user_id = get_jwt_identity()
    from routes.entities import _check_superadmin_access
    if not _check_superadmin_access(current_user_id):
        return jsonify({'error': 'Access denied. Superadmin only.'}), 403
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM players LIMIT 100")
        players = cursor.fetchall()
        
        # Convert datetime objects
        for player in players:
            for key, value in player.items():
                if hasattr(value, 'isoformat'):
                    player[key] = value.isoformat()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'players': players,
            'count': len(players)
        }), 200
        
    except Exception as e:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
        return jsonify({'error': str(e)}), 500


@debug_bp.route('/show-statistics', methods=['GET'])
@jwt_required()
def show_statistics():
    """Show all statistics records - superadmin only, debug mode only"""
    
    # Guard against production environment - defense in depth
    if not _is_debug_enabled():
        return jsonify({'error': 'Debug endpoints are disabled. Set DEBUG=true and FLASK_ENV!=production to enable.'}), 403
    
    current_user_id = get_jwt_identity()
    from routes.entities import _check_superadmin_access
    if not _check_superadmin_access(current_user_id):
        return jsonify({'error': 'Access denied. Superadmin only.'}), 403
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM statistics LIMIT 100")
        stats = cursor.fetchall()
        
        # Convert datetime objects
        for stat in stats:
            for key, value in stat.items():
                if hasattr(value, 'isoformat'):
                    stat[key] = value.isoformat()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'statistics': stats,
            'count': len(stats)
        }), 200
        
    except Exception as e:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
        return jsonify({'error': str(e)}), 500


@debug_bp.route('/show-matches', methods=['GET'])
@jwt_required()
def show_matches():
    """Show all matches - superadmin only, debug mode only"""
    
    # Guard against production environment - defense in depth
    if not _is_debug_enabled():
        return jsonify({'error': 'Debug endpoints are disabled. Set DEBUG=true and FLASK_ENV!=production to enable.'}), 403
    
    current_user_id = get_jwt_identity()
    from routes.entities import _check_superadmin_access
    if not _check_superadmin_access(current_user_id):
        return jsonify({'error': 'Access denied. Superadmin only.'}), 403
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM matches LIMIT 100")
        matches = cursor.fetchall()
        
        # Convert datetime objects
        for match in matches:
            for key, value in match.items():
                if hasattr(value, 'isoformat'):
                    match[key] = value.isoformat()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'matches': matches,
            'count': len(matches)
        }), 200
        
    except Exception as e:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
        return jsonify({'error': str(e)}), 500
