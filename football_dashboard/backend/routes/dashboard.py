"""
Dashboard Routes
Provides aggregated data for dashboard views
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import mysql.connector
from datetime import datetime, timedelta
from database import get_db_connection

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/overview", methods=["GET"])
@jwt_required()
def get_overview():
    """Get dashboard overview statistics"""
    user_id = get_jwt_identity()

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Convert string user_id to int for database query
        try:
            user_id_int = int(user_id)
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid user identity"}), 401

        # Get user info
        cursor.execute(
            "SELECT role, entity_id FROM users WHERE id = %s", (user_id_int,)
        )
        user = cursor.fetchone()

        response = {}

        # Get player counts, match counts, and entity counts in consolidated chunks
        if user["role"] == "superadmin" or user["role"] == "ferwafa":
            cursor.execute("SELECT COUNT(*) as count FROM players")
            response["total_players"] = cursor.fetchone()["count"]

            cursor.execute("SELECT COUNT(*) as count FROM users")
            response["total_users"] = cursor.fetchone()["count"]

        allowed_roles = {"school", "academy", "club"}
        if user["role"] in allowed_roles:
            id_field = f"{user['role']}_id"
            cursor.execute(
                f"SELECT COUNT(*) as count FROM players WHERE {id_field} = %s",
                (user["entity_id"],),
            )
            response["total_players"] = cursor.fetchone()["count"]

        # Consolidate Match and Club counts into single queries where possible
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN status = 'live' THEN 1 ELSE 0 END) as live,
                SUM(CASE WHEN status = 'scheduled' THEN 1 ELSE 0 END) as scheduled,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                COUNT(*) as total_matches
            FROM matches
        """)
        match_stats = cursor.fetchone()
        response.update(
            {
                "active_matches": match_stats["live"] or 0,
                "scheduled_matches": match_stats["scheduled"] or 0,
                "completed_matches": match_stats["completed"] or 0,
            }
        )

        cursor.execute(
            "SELECT (SELECT COUNT(*) FROM clubs) as clubs, (SELECT COUNT(*) FROM schools) as schools, (SELECT COUNT(*) FROM academies) as academies"
        )
        entity_counts = cursor.fetchone()
        response.update(
            {
                "total_clubs": entity_counts["clubs"],
                "total_schools": entity_counts["schools"],
                "total_academies": entity_counts["academies"],
            }
        )

        # Get top performer (keep separate as it's a join)
        cursor.execute("""
            SELECT p.name, SUM(s.goals) as goals
            FROM players p
            JOIN statistics s ON p.id = s.player_id
            GROUP BY p.id
            ORDER BY goals DESC
            LIMIT 1
        """)
        top_scorer = cursor.fetchone()
        response["top_scorer"] = (
            top_scorer if top_scorer else {"name": "N/A", "goals": 0}
        )

        cursor.close()
        conn.close()

        return jsonify(response), 200

    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500


@dashboard_bp.route("/recent-matches", methods=["GET"])
@jwt_required()
def get_recent_matches():
    """Get recent match results"""
    user_id = get_jwt_identity()
    limit = request.args.get("limit", 5, type=int)

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
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
        """,
            (limit,),
        )

        matches = cursor.fetchall()

        for match in matches:
            if match.get("match_date"):
                match["match_date"] = match["match_date"].isoformat()

        cursor.close()
        conn.close()

        return jsonify(matches), 200

    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500


@dashboard_bp.route("/upcoming-matches", methods=["GET"])
@jwt_required()
def get_upcoming_matches():
    """Get upcoming matches"""
    user_id = get_jwt_identity()
    limit = request.args.get("limit", 5, type=int)

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
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
        """,
            (limit,),
        )

        matches = cursor.fetchall()

        for match in matches:
            if match.get("match_date"):
                match["match_date"] = match["match_date"].isoformat()

        cursor.close()
        conn.close()

        return jsonify(matches), 200

    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500


@dashboard_bp.route("/performance", methods=["GET"])
@jwt_required()
def get_performance_data():
    """Get performance data for charts"""
    user_id = get_jwt_identity()

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Convert string user_id to int for database query
        try:
            user_id_int = int(user_id)
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid user identity"}), 401

        # Get user info
        cursor.execute(
            "SELECT role, entity_id FROM users WHERE id = %s", (user_id_int,)
        )
        user = cursor.fetchone()

        # Get goals per month (last 6 months)
        months_ago = datetime.now() - timedelta(days=180)

        if user["role"] == "superadmin" or user["role"] == "ferwafa":
            cursor.execute(
                """
                SELECT 
                    DATE_FORMAT(m.match_date, '%%Y-%%m') as month,
                    SUM(s.goals) as goals
                FROM statistics s
                JOIN matches m ON s.match_id = m.id
                WHERE m.match_date >= %s
                GROUP BY DATE_FORMAT(m.match_date, '%%Y-%%m')
                ORDER BY month
            """,
                (months_ago,),
            )
        else:
            id_field = f"{user['role']}_id"
            cursor.execute(
                f"""
                SELECT 
                    DATE_FORMAT(m.match_date, '%%Y-%%m') as month,
                    SUM(s.goals) as goals
                FROM statistics s
                JOIN matches m ON s.match_id = m.id
                JOIN players p ON s.player_id = p.id
                WHERE m.match_date >= %s AND p.{id_field} = %s
                GROUP BY DATE_FORMAT(m.match_date, '%%Y-%%m')
                ORDER BY month
            """,
                (months_ago, user["entity_id"]),
            )

        goals_data = cursor.fetchall()

        # Get player position distribution
        if user["role"] == "superadmin" or user["role"] == "ferwafa":
            cursor.execute("""
                SELECT position, COUNT(*) as count
                FROM players
                GROUP BY position
            """)
        else:
            id_field = f"{user['role']}_id"
            cursor.execute(
                f"""
                SELECT position, COUNT(*) as count
                FROM players
                WHERE {id_field} = %s
                GROUP BY position
            """,
                (user["entity_id"],),
            )

        position_data = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify(
            {"goals_per_month": goals_data, "position_distribution": position_data}
        ), 200

    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500


@dashboard_bp.route("/entity-summary", methods=["GET"])
@jwt_required()
def get_entity_summary():
    """Get summary for FERWAFA/Super Admin - all entities"""
    user_id = get_jwt_identity()

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Convert string user_id to int for database query
        try:
            user_id_int = int(user_id)
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid user identity"}), 401

        # Get user info
        cursor.execute("SELECT role FROM users WHERE id = %s", (user_id_int,))
        user = cursor.fetchone()

        if user["role"] not in ["superadmin", "ferwafa"]:
            return jsonify({"error": "Access denied"}), 403

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

        return jsonify(
            {"clubs": clubs, "academies": academies, "schools": schools}
        ), 200

    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
