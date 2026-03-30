from flask import Blueprint, jsonify, request
from database import get_db_connection
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta

ferwafa_analytics_bp = Blueprint("ferwafa_analytics", __name__)


@ferwafa_analytics_bp.route("/matches", methods=["GET"])
@jwt_required()
def get_national_matches():
    """Get all matches in the country with filters"""
    category = request.args.get("category")  # Club, Academy, School
    date_from = request.args.get("from")
    date_to = request.args.get("to")

    query = """
        SELECT m.*, 
               h.name as home_team, h.logo_url as home_logo,
               a.name as away_team, a.logo_url as away_logo,
               v.name as venue_name
        FROM matches m
        JOIN clubs h ON m.home_team_id = h.id
        JOIN clubs a ON m.away_team_id = a.id
        LEFT JOIN venues v ON m.venue_id = v.id
        WHERE 1=1
    """
    params = []

    if date_from:
        query += " AND m.match_date >= %s"
        params.append(date_from)
    if date_to:
        query += " AND m.match_date <= %s"
        params.append(date_to)

    query += " ORDER BY m.match_date DESC LIMIT 50"

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params)
        matches = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(matches), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@ferwafa_analytics_bp.route("/talent-discovery", methods=["GET"])
@jwt_required()
def talent_discovery():
    """Advanced talent filtering and ranking"""
    age_min = request.args.get("age_min", type=int)
    age_max = request.args.get("age_max", type=int)
    position = request.args.get("position")
    period = request.args.get("period", "month")  # week, month, season

    # Calculate date threshold for performance
    days = 30
    if period == "week":
        days = 7
    elif period == "season":
        days = 365
    threshold_date = datetime.now() - timedelta(days=days)

    query = """
        SELECT p.id, p.name, p.dob, p.position, p.registration_number, p.photo_url,
               COALESCE(c.name, ac.name, sc.name) as entity_name,
               TIMESTAMPDIFF(YEAR, p.dob, CURDATE()) AS age,
               COUNT(s.id) as matches_played,
               SUM(s.goals) as total_goals,
               SUM(s.assists) as total_assists,
               AVG(s.rating) as avg_rating,
               (AVG(s.rating) * 10 + SUM(s.goals) * 5 + SUM(s.assists) * 3) as talent_score
        FROM players p
        LEFT JOIN clubs c ON p.club_id = c.id
        LEFT JOIN academies ac ON p.academy_id = ac.id
        LEFT JOIN schools sc ON p.school_id = sc.id
        JOIN statistics s ON p.id = s.player_id
        JOIN matches m ON s.match_id = m.id
        WHERE m.match_date >= %s
    """
    params = [threshold_date]

    if age_min:
        query += " AND TIMESTAMPDIFF(YEAR, p.dob, CURDATE()) >= %s"
        params.append(age_min)
    if age_max:
        query += " AND TIMESTAMPDIFF(YEAR, p.dob, CURDATE()) <= %s"
        params.append(age_max)
    if position:
        query += " AND p.position = %s"
        params.append(position)

    query += " GROUP BY p.id ORDER BY talent_score DESC LIMIT 20"

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params)
        talents = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(talents), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@ferwafa_analytics_bp.route("/player-report/<int:player_id>", methods=["GET"])
@jwt_required()
def get_player_report(player_id):
    """Detailed performance data for report generation"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Player basic info
        cursor.execute(
            """
            SELECT p.*, COALESCE(c.name, ac.name, s.name) as entity_name,
                   TIMESTAMPDIFF(YEAR, p.dob, CURDATE()) AS age
            FROM players p
            LEFT JOIN clubs c ON p.club_id = c.id
            LEFT JOIN academies ac ON p.academy_id = ac.id
            LEFT JOIN schools s ON p.school_id = s.id
            WHERE p.id = %s
        """,
            (player_id,),
        )
        player = cursor.fetchone()

        if not player:
            return jsonify({"error": "Player not found"}), 404

        # Recent match stats
        cursor.execute(
            """
            SELECT s.*, m.match_date, 
                   h.name as home_team, a.name as away_team
            FROM statistics s
            JOIN matches m ON s.match_id = m.id
            JOIN clubs h ON m.home_team_id = h.id
            JOIN clubs a ON m.away_team_id = a.id
            WHERE s.player_id = %s
            ORDER BY m.match_date DESC LIMIT 10
        """,
            (player_id,),
        )
        recent_stats = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify(
            {
                "player": player,
                "recent_stats": recent_stats,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        ), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
