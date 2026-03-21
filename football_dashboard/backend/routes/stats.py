"""
Statistics Routes
Handles player and match statistics
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import mysql.connector
from datetime import datetime, timedelta

stats_bp = Blueprint('stats', __name__)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'football_dashboard',
    'charset': 'utf8mb4'
}

# Auto-update interval in minutes
LIVE_UPDATE_INTERVAL = 15

def get_db_connection():
    """Create database connection"""
    return mysql.connector.connect(**DB_CONFIG)

@stats_bp.route('/player/<int:player_id>', methods=['GET'])
@jwt_required()
def get_player_stats(player_id):
    """Get statistics for a specific player"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get player info
        cursor.execute("SELECT * FROM players WHERE id = %s", (player_id,))
        player = cursor.fetchone()
        
        if not player:
            return jsonify({'error': 'Player not found'}), 404
        
        # Get player statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_matches,
                SUM(goals) as total_goals,
                SUM(assists) as total_assists,
                SUM(minutes_played) as total_minutes,
                SUM(yellow_cards) as yellow_cards,
                SUM(red_cards) as red_cards
            FROM statistics 
            WHERE player_id = %s
        """, (player_id,))
        
        stats = cursor.fetchone()
        
        # Get recent matches
        cursor.execute("""
            SELECT s.*, m.match_date, m.home_team_id, m.away_team_id,
                   h.name as home_team, a.name as away_team
            FROM statistics s
            JOIN matches m ON s.match_id = m.id
            LEFT JOIN clubs h ON m.home_team_id = h.id
            LEFT JOIN clubs a ON m.away_team_id = a.id
            WHERE s.player_id = %s
            ORDER BY m.match_date DESC
            LIMIT 10
        """, (player_id,))
        
        recent_matches = cursor.fetchall()
        
        for match in recent_matches:
            if match.get('match_date'):
                match['match_date'] = match['match_date'].isoformat()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'player': player,
            'total_stats': stats,
            'recent_matches': recent_matches
        }), 200
        
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500

@stats_bp.route('/top-scorers', methods=['GET'])
@jwt_required()
def get_top_scorers():
    """Get top scorers across all entities"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        limit = request.args.get('limit', 10, type=int)
        
        cursor.execute("""
            SELECT 
                p.id,
                p.name,
                p.position,
                p.photo_url,
                p.nationality,
                SUM(s.goals) as total_goals,
                COUNT(s.id) as matches_played,
                CASE 
                    WHEN p.school_id IS NOT NULL THEN s.name
                    WHEN p.academy_id IS NOT NULL THEN a.name
                    WHEN p.club_id IS NOT NULL THEN c.name
                END as entity_name
            FROM players p
            LEFT JOIN statistics s ON p.id = s.player_id
            LEFT JOIN schools s ON p.school_id = s.id
            LEFT JOIN academies a ON p.academy_id = a.id
            LEFT JOIN clubs c ON p.club_id = c.id
            GROUP BY p.id
            HAVING total_goals > 0
            ORDER BY total_goals DESC
            LIMIT %s
        """, (limit,))
        
        scorers = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify(scorers), 200
        
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500

@stats_bp.route('/top-assists', methods=['GET'])
@jwt_required()
def get_top_assists():
    """Get top assists across all entities"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        limit = request.args.get('limit', 10, type=int)
        
        cursor.execute("""
            SELECT 
                p.id,
                p.name,
                p.position,
                p.photo_url,
                p.nationality,
                SUM(s.assists) as total_assists,
                COUNT(s.id) as matches_played
            FROM players p
            LEFT JOIN statistics s ON p.id = s.player_id
            GROUP BY p.id
            HAVING total_assists > 0
            ORDER BY total_assists DESC
            LIMIT %s
        """, (limit,))
        
        assists = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify(assists), 200
        
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500

@stats_bp.route('/match/<int:match_id>', methods=['GET'])
@jwt_required()
def get_match_stats(match_id):
    """Get statistics for a specific match"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get match info
        cursor.execute("""
            SELECT m.*, 
                   h.name as home_team_name, 
                   a.name as away_team_name
            FROM matches m
            LEFT JOIN clubs h ON m.home_team_id = h.id
            LEFT JOIN clubs a ON m.away_team_id = a.id
            WHERE m.id = %s
        """, (match_id,))
        
        match = cursor.fetchone()
        
        if not match:
            return jsonify({'error': 'Match not found'}), 404
        
        # Get match statistics
        cursor.execute("""
            SELECT s.*, p.name as player_name, p.jersey_number, p.position
            FROM statistics s
            JOIN players p ON s.player_id = p.id
            WHERE s.match_id = %s
            ORDER BY p.position
        """, (match_id,))
        
        match_stats = cursor.fetchall()
        
        if match.get('match_date'):
            match['match_date'] = match['match_date'].isoformat()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'match': match,
            'player_stats': match_stats
        }), 200
        
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500

@stats_bp.route('/', methods=['POST'])
@jwt_required()
def create_stat():
    """Create/update player statistics for a match"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    required_fields = ['player_id', 'match_id']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if stats already exist
        cursor.execute("""
            SELECT id FROM statistics 
            WHERE player_id = %s AND match_id = %s
        """, (data['player_id'], data['match_id']))
        
        existing = cursor.fetchone()
        
        if existing:
            # Update existing stats
            sql = """UPDATE statistics SET 
                     goals = %s, assists = %s, minutes_played = %s,
                     yellow_cards = %s, red_cards = %s,
                     updated_at = %s
                     WHERE player_id = %s AND match_id = %s"""
            
            values = (
                data.get('goals', 0),
                data.get('assists', 0),
                data.get('minutes_played', 0),
                data.get('yellow_cards', 0),
                data.get('red_cards', 0),
                datetime.now(),
                data['player_id'],
                data['match_id']
            )
        else:
            # Insert new stats
            sql = """INSERT INTO statistics 
                     (player_id, match_id, goals, assists, minutes_played,
                      yellow_cards, red_cards, created_at) 
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
            
            values = (
                data['player_id'],
                data['match_id'],
                data.get('goals', 0),
                data.get('assists', 0),
                data.get('minutes_played', 0),
                data.get('yellow_cards', 0),
                data.get('red_cards', 0),
                datetime.now()
            )
        
        cursor.execute(sql, values)
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Statistics updated successfully'}), 200
        
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500

@stats_bp.route('/live', methods=['GET'])
@jwt_required()
def get_live_stats():
    """Get live statistics (updated every 15 minutes)"""
    try:
        # Get matches from last 15 minutes
        time_threshold = datetime.now() - timedelta(minutes=LIVE_UPDATE_INTERVAL)
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get recent match statistics
        cursor.execute("""
            SELECT 
                m.id as match_id,
                m.match_date,
                m.home_team_id,
                m.away_team_id,
                m.home_score,
                m.away_score,
                m.status,
                h.name as home_team,
                a.name as away_team,
                COUNT(s.id) as player_events,
                SUM(s.goals) as total_goals,
                SUM(s.assists) as total_assists
            FROM matches m
            LEFT JOIN clubs h ON m.home_team_id = h.id
            LEFT JOIN clubs a ON m.away_team_id = a.id
            LEFT JOIN statistics s ON m.id = s.match_id
            WHERE m.match_date >= %s
            GROUP BY m.id
            ORDER BY m.match_date DESC
        """, (time_threshold,))
        
        live_stats = cursor.fetchall()
        
        for match in live_stats:
            if match.get('match_date'):
                match['match_date'] = match['match_date'].isoformat()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'last_updated': datetime.now().isoformat(),
            'update_interval_minutes': LIVE_UPDATE_INTERVAL,
            'matches': live_stats
        }), 200
        
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500

@stats_bp.route('/entity/<entity_type>/<int:entity_id>', methods=['GET'])
@jwt_required()
def get_entity_stats(entity_type, entity_id):
    """Get statistics for a specific entity (school/academy/club)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        valid_entities = ['school', 'academy', 'club']
        if entity_type not in valid_entities:
            return jsonify({'error': 'Invalid entity type'}), 400
        
        # Get entity players
        id_field = f"{entity_type}_id"
        cursor.execute(f"SELECT id, name FROM {entity_type}s WHERE id = %s", (entity_id,))
        entity = cursor.fetchone()
        
        if not entity:
            return jsonify({'error': 'Entity not found'}), 404
        
        # Get player statistics for this entity
        cursor.execute(f"""
            SELECT 
                p.id,
                p.name,
                p.position,
                p.jersey_number,
                SUM(s.goals) as total_goals,
                SUM(s.assists) as total_assists,
                SUM(s.minutes_played) as total_minutes,
                COUNT(DISTINCT s.match_id) as matches_played
            FROM players p
            LEFT JOIN statistics s ON p.id = s.player_id
            WHERE p.{id_field} = %s
            GROUP BY p.id
            ORDER BY total_goals DESC
        """, (entity_id,))
        
        player_stats = cursor.fetchall()
        
        # Get entity match history
        cursor.execute("""
            SELECT 
                m.id,
                m.match_date,
                m.home_score,
                m.away_score,
                m.status,
                h.name as home_team,
                a.name as away_team
            FROM matches m
            LEFT JOIN clubs h ON m.home_team_id = h.id
            LEFT JOIN clubs a ON m.away_team_id = a.id
            WHERE m.home_team_id = %s OR m.away_team_id = %s
            ORDER BY m.match_date DESC
            LIMIT 20
        """, (entity_id, entity_id))
        
        match_history = cursor.fetchall()
        
        for match in match_history:
            if match.get('match_date'):
                match['match_date'] = match['match_date'].isoformat()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'entity': entity,
            'player_stats': player_stats,
            'match_history': match_history
        }), 200
        
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
