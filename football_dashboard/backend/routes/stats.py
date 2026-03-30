"""
Statistics Routes
Handles player and match statistics
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import mysql.connector
from datetime import datetime, timedelta
from database import get_db_connection

stats_bp = Blueprint('stats', __name__)

# Auto-update interval in minutes
LIVE_UPDATE_INTERVAL = 15

# Removed local DB_CONFIG - now using centralized database.py


@stats_bp.route('/overview', methods=['GET'])
@jwt_required()
def get_stats_overview():
    """Get overall statistics overview"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Consolidate into a single query for better performance
        cursor.execute("""
            SELECT 
                COALESCE(SUM(goals), 0) as total_goals,
                COALESCE(SUM(assists), 0) as total_assists,
                COALESCE(SUM(minutes_played), 0) as total_minutes,
                COALESCE(AVG(performance_score), 0) as avg_performance
            FROM statistics
        """)
        stats = cursor.fetchone()
        
        # Get user count
        cursor.execute("SELECT COUNT(*) as count FROM users")
        user_count = cursor.fetchone()['count']
        
        # Get database size in MB
        cursor.execute("""
            SELECT SUM(data_length + index_length) / 1024 / 1024 AS size 
            FROM information_schema.TABLES 
            WHERE table_schema = 'football_dashboard'
        """)
        db_size_row = cursor.fetchone()
        db_size = round(float(db_size_row['size'] or 0), 2)
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'total_goals': stats['total_goals'],
            'total_assists': stats['total_assists'],
            'total_minutes': stats['total_minutes'],
            'avg_performance': round(float(stats['avg_performance']), 1),
            'users': user_count,
            'db_size': db_size
        }), 200
        
    except Exception as e:
        print(f"Error getting stats overview: {e}")
        return jsonify({'error': 'Failed to load statistics'}), 500


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
                COALESCE(SUM(goals), 0) as total_goals,
                COALESCE(SUM(assists), 0) as total_assists,
                COALESCE(SUM(minutes_played), 0) as total_minutes,
                COALESCE(SUM(yellow_cards), 0) as yellow_cards,
                COALESCE(SUM(red_cards), 0) as red_cards
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
        
        # Use different aliases to avoid conflict: sch=schools, acd=academies, clb=clubs
        cursor.execute("""
            SELECT 
                p.id,
                p.name,
                p.position,
                p.photo_url,
                p.nationality,
                COALESCE(SUM(s.goals), 0) as goals,
                COALESCE(SUM(s.assists), 0) as assists,
                COUNT(s.id) as matches,
                CASE 
                    WHEN p.school_id IS NOT NULL THEN sch.name
                    WHEN p.academy_id IS NOT NULL THEN acd.name
                    WHEN p.club_id IS NOT NULL THEN clb.name
                END as entity_name
            FROM players p
            LEFT JOIN statistics s ON p.id = s.player_id
            LEFT JOIN schools sch ON p.school_id = sch.id
            LEFT JOIN academies acd ON p.academy_id = acd.id
            LEFT JOIN clubs clb ON p.club_id = clb.id
            GROUP BY p.id
            ORDER BY goals DESC, assists DESC
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
        
        # Use column mapping to avoid f-string SQL injection pattern
        # Validated at line 382, but avoid f-strings for SQL tables/columns
        column_map = {'school': 'school_id', 'academy': 'academy_id', 'club': 'club_id'}
        id_field = column_map.get(entity_type)
        
        cursor.execute(f"SELECT id, name FROM {entity_type} WHERE id = %s", (entity_id,))
        entity = cursor.fetchone()
        
        if not entity:
            return jsonify({'error': 'Entity not found'}), 404
        
        # Build query with validated column - use separate queries per entity type
        # This avoids dynamic SQL column names while maintaining correctness
        if entity_type == 'school':
            player_query = """
                SELECT 
                    p.id,
                    p.name,
                    p.position,
                    p.jersey_number,
                    COALESCE(SUM(s.goals), 0) as total_goals,
                    COALESCE(SUM(s.assists), 0) as total_assists,
                    COALESCE(SUM(s.minutes_played), 0) as total_minutes,
                    COUNT(DISTINCT s.match_id) as matches_played
                FROM players p
                LEFT JOIN statistics s ON p.id = s.player_id
                WHERE p.school_id = %s
                GROUP BY p.id
                ORDER BY total_goals DESC
            """
        elif entity_type == 'academy':
            player_query = """
                SELECT 
                    p.id,
                    p.name,
                    p.position,
                    p.jersey_number,
                    COALESCE(SUM(s.goals), 0) as total_goals,
                    COALESCE(SUM(s.assists), 0) as total_assists,
                    COALESCE(SUM(s.minutes_played), 0) as total_minutes,
                    COUNT(DISTINCT s.match_id) as matches_played
                FROM players p
                LEFT JOIN statistics s ON p.id = s.player_id
                WHERE p.academy_id = %s
                GROUP BY p.id
                ORDER BY total_goals DESC
            """
        else:  # club
            player_query = """
                SELECT 
                    p.id,
                    p.name,
                    p.position,
                    p.jersey_number,
                    COALESCE(SUM(s.goals), 0) as total_goals,
                    COALESCE(SUM(s.assists), 0) as total_assists,
                    COALESCE(SUM(s.minutes_played), 0) as total_minutes,
                    COUNT(DISTINCT s.match_id) as matches_played
                FROM players p
                LEFT JOIN statistics s ON p.id = s.player_id
                WHERE p.club_id = %s
                GROUP BY p.id
                ORDER BY total_goals DESC
            """
        
        cursor.execute(player_query, (entity_id,))
        
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
