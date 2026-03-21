"""
Dashboard Routes
Provides aggregated data for dashboard views
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import mysql.connector
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__)

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

@dashboard_bp.route('/overview', methods=['GET'])
@jwt_required()
def get_overview():
    """Get dashboard overview statistics"""
    user_id = get_jwt_identity()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get user info
        cursor.execute("SELECT role, entity_id FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        response = {}
        
        # Get total players
        if user['role'] == 'superadmin' or user['role'] == 'ferwafa':
            cursor.execute("SELECT COUNT(*) as count FROM players")
            response['total_players'] = cursor.fetchone()['count']
        elif user['role'] in ['school', 'academy', 'club']:
            id_field = f"{user['role']}_id"
            cursor.execute(f"SELECT COUNT(*) as count FROM players WHERE {id_field} = %s", (user['entity_id'],))
            response['total_players'] = cursor.fetchone()['count']
        
        # Get active matches
        cursor.execute("SELECT COUNT(*) as count FROM matches WHERE status = 'live'")
        response['active_matches'] = cursor.fetchone()['count']
        
        # Get scheduled matches
        cursor.execute("SELECT COUNT(*) as count FROM matches WHERE status = 'scheduled'")
        response['scheduled_matches'] = cursor.fetchone()['count']
        
        # Get total matches played
        cursor.execute("SELECT COUNT(*) as count FROM matches WHERE status = 'completed'")
        response['completed_matches'] = cursor.fetchone()['count']
        
        # Get top scorer
        cursor.execute("""
            SELECT p.name, SUM(s.goals) as goals
            FROM players p
            JOIN statistics s ON p.id = s.player_id
            GROUP BY p.id
            ORDER BY goals DESC
            LIMIT 1
        """)
        top_scorer = cursor.fetchone()
        response['top_scorer'] = top_scorer if top_scorer else {'name': 'N/A', 'goals': 0}
        
        # Get total entities
        cursor.execute("SELECT COUNT(*) as count FROM clubs")
        response['total_clubs'] = cursor.fetchone()['count']
        
        cursor.close()
        conn.close()
        
        return jsonify(response), 200
        
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500

@dashboard_bp.route('/recent-matches', methods=['GET'])
@jwt_required()
def get_recent_matches():
    """Get recent match results"""
    user_id = get_jwt_identity()
    limit = request.args.get('limit', 5, type=int)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT m.*, 
                   h.name as home_team_name, 
                   a.name as away_team_name,
                   h.logo_url as home_logo,
                   a.logo_url as away_logo
            FROM matches m
            LEFT JOIN clubs h ON m.home_team_id = h.id
            LEFT JOIN clubs a ON m.away_team_id = a.id
            WHERE m.status = 'completed'
            ORDER BY m.match_date DESC
            LIMIT %s
        """, (limit,))
        
        matches = cursor.fetchall()
        
        for match in matches:
            if match.get('match_date'):
                match['match_date'] = match['match_date'].isoformat()
        
        cursor.close()
        conn.close()
        
        return jsonify(matches), 200
        
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500

@dashboard_bp.route('/upcoming-matches', methods=['GET'])
@jwt_required()
def get_upcoming_matches():
    """Get upcoming matches"""
    user_id = get_jwt_identity()
    limit = request.args.get('limit', 5, type=int)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT m.*, 
                   h.name as home_team_name, 
                   a.name as away_team_name,
                   h.logo_url as home_logo,
                   a.logo_url as away_logo,
                   v.name as venue_name
            FROM matches m
            LEFT JOIN clubs h ON m.home_team_id = h.id
            LEFT JOIN clubs a ON m.away_team_id = a.id
            LEFT JOIN venues v ON m.venue_id = v.id
            WHERE m.status = 'scheduled' AND m.match_date >= NOW()
            ORDER BY m.match_date ASC
            LIMIT %s
        """, (limit,))
        
        matches = cursor.fetchall()
        
        for match in matches:
            if match.get('match_date'):
                match['match_date'] = match['match_date'].isoformat()
        
        cursor.close()
        conn.close()
        
        return jsonify(matches), 200
        
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500

@dashboard_bp.route('/performance', methods=['GET'])
@jwt_required()
def get_performance_data():
    """Get performance data for charts"""
    user_id = get_jwt_identity()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get user info
        cursor.execute("SELECT role, entity_id FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        # Get goals per month (last 6 months)
        months_ago = datetime.now() - timedelta(days=180)
        
        if user['role'] == 'superadmin' or user['role'] == 'ferwafa':
            cursor.execute("""
                SELECT 
                    DATE_FORMAT(m.match_date, '%%Y-%%m') as month,
                    SUM(s.goals) as goals
                FROM statistics s
                JOIN matches m ON s.match_id = m.id
                WHERE m.match_date >= %s
                GROUP BY DATE_FORMAT(m.match_date, '%%Y-%%m')
                ORDER BY month
            """, (months_ago,))
        else:
            id_field = f"{user['role']}_id"
            cursor.execute(f"""
                SELECT 
                    DATE_FORMAT(m.match_date, '%%Y-%%m') as month,
                    SUM(s.goals) as goals
                FROM statistics s
                JOIN matches m ON s.match_id = m.id
                JOIN players p ON s.player_id = p.id
                WHERE m.match_date >= %s AND p.{id_field} = %s
                GROUP BY DATE_FORMAT(m.match_date, '%%Y-%%m')
                ORDER BY month
            """, (months_ago, user['entity_id']))
        
        goals_data = cursor.fetchall()
        
        # Get player position distribution
        if user['role'] == 'superadmin' or user['role'] == 'ferwafa':
            cursor.execute("""
                SELECT position, COUNT(*) as count
                FROM players
                GROUP BY position
            """)
        else:
            id_field = f"{user['role']}_id"
            cursor.execute(f"""
                SELECT position, COUNT(*) as count
                FROM players
                WHERE {id_field} = %s
                GROUP BY position
            """, (user['entity_id'],))
        
        position_data = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'goals_per_month': goals_data,
            'position_distribution': position_data
        }), 200
        
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500

@dashboard_bp.route('/entity-summary', methods=['GET'])
@jwt_required()
def get_entity_summary():
    """Get summary for FERWAFA/Super Admin - all entities"""
    user_id = get_jwt_identity()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get user info
        cursor.execute("SELECT role FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        if user['role'] not in ['superadmin', 'ferwafa']:
            return jsonify({'error': 'Access denied'}), 403
        
        # Get summary for clubs
        cursor.execute("""
            SELECT 
                c.id,
                c.name,
                COUNT(DISTINCT p.id) as player_count,
                COUNT(DISTINCT m.id) as match_count
            FROM clubs c
            LEFT JOIN players p ON p.club_id = c.id
            LEFT JOIN matches m ON m.home_team_id = c.id OR m.away_team_id = c.id
            GROUP BY c.id
            ORDER BY player_count DESC
        """)
        clubs = cursor.fetchall()
        
        # Get summary for academies
        cursor.execute("""
            SELECT 
                a.id,
                a.name,
                COUNT(DISTINCT p.id) as player_count
            FROM academies a
            LEFT JOIN players p ON p.academy_id = a.id
            GROUP BY a.id
            ORDER BY player_count DESC
        """)
        academies = cursor.fetchall()
        
        # Get summary for schools
        cursor.execute("""
            SELECT 
                s.id,
                s.name,
                COUNT(DISTINCT p.id) as player_count
            FROM schools s
            LEFT JOIN players p ON p.school_id = s.id
            GROUP BY s.id
            ORDER BY player_count DESC
        """)
        schools = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'clubs': clubs,
            'academies': academies,
            'schools': schools
        }), 200
        
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
