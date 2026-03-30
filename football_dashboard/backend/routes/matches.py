"""
Matches Routes
Handles match CRUD operations and lineup management
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import mysql.connector
from datetime import datetime
from database import get_db_connection

matches_bp = Blueprint("matches", __name__)


@matches_bp.route("/", methods=["GET"])
@jwt_required()
def get_matches():
    """Get all matches (filtered by user role)"""
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

        if user["role"] in ["superadmin", "ferwafa"]:
            # See all matches
            cursor.execute("""
                SELECT m.*, 
                       h.name as home_team_name, 
                       a.name as away_team_name,
                       v.name as venue_name
                FROM matches m
                LEFT JOIN clubs h ON m.home_team_id = h.id
                LEFT JOIN clubs a ON m.away_team_id = a.id
                LEFT JOIN venues v ON m.venue_id = v.id
                ORDER BY m.match_date DESC
            """)
        elif user["role"] == "club":
            # See matches involving their club
            cursor.execute(
                """
                SELECT m.*, 
                       h.name as home_team_name, 
                       a.name as away_team_name,
                       v.name as venue_name
                FROM matches m
                LEFT JOIN clubs h ON m.home_team_id = h.id
                LEFT JOIN clubs a ON m.away_team_id = a.id
                LEFT JOIN venues v ON m.venue_id = v.id
                WHERE m.home_team_id = %s OR m.away_team_id = %s
                ORDER BY m.match_date DESC
            """,
                (user["entity_id"], user["entity_id"]),
            )
        else:
            # Schools and academies see their matches
            cursor.execute(
                """
                SELECT m.*, 
                       h.name as home_team_name, 
                       a.name as away_team_name,
                       v.name as venue_name
                FROM matches m
                LEFT JOIN clubs h ON m.home_team_id = h.id
                LEFT JOIN clubs a ON m.away_team_id = a.id
                LEFT JOIN venues v ON m.venue_id = v.id
                WHERE m.home_team_id = %s OR m.away_team_id = %s
                ORDER BY m.match_date DESC
            """,
                (user["entity_id"], user["entity_id"]),
            )

        matches = cursor.fetchall()

        # Convert datetime objects to strings
        for match in matches:
            if match.get("match_date"):
                match["match_date"] = match["match_date"].isoformat()
            if match.get("created_at"):
                match["created_at"] = match["created_at"].isoformat()

        cursor.close()
        conn.close()

        return jsonify(matches), 200

    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500


@matches_bp.route("/<int:match_id>", methods=["GET"])
@jwt_required()
def get_match(match_id):
    """Get a single match by ID with lineup"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Get match
        cursor.execute(
            """
            SELECT m.*, 
                   h.name as home_team_name, 
                   a.name as away_team_name,
                   v.name as venue_name
            FROM matches m
            LEFT JOIN clubs h ON m.home_team_id = h.id
            LEFT JOIN clubs a ON m.away_team_id = a.id
            LEFT JOIN venues v ON m.venue_id = v.id
            WHERE m.id = %s
        """,
            (match_id,),
        )

        match = cursor.fetchone()

        if not match:
            return jsonify({"error": "Match not found"}), 404

        # Get lineup
        cursor.execute(
            """
            SELECT ml.*, p.name as player_name, p.jersey_number, p.position
            FROM match_lineups ml
            JOIN players p ON ml.player_id = p.id
            WHERE ml.match_id = %s
            ORDER BY ml.position_type DESC, ml.position_order
        """,
            (match_id,),
        )

        lineup = cursor.fetchall()
        match["lineup"] = lineup

        # Convert datetime
        if match.get("match_date"):
            match["match_date"] = match["match_date"].isoformat()

        cursor.close()
        conn.close()

        return jsonify(match), 200

    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500


@matches_bp.route("/", methods=["POST"])
@jwt_required()
def create_match():
    """Create a new match"""
    user_id = get_jwt_identity()
    data = request.get_json()

    required_fields = ["home_team_id", "away_team_id", "match_date", "venue_id"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        # Validate user_id
        try:
            user_id_int = int(user_id)
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid user identity"}), 401

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Insert match
        sql = """INSERT INTO matches 
                 (home_team_id, away_team_id, match_date, venue_id, status, created_at) 
                 VALUES (%s, %s, %s, %s, %s, %s)"""

        values = (
            data["home_team_id"],
            data["away_team_id"],
            data["match_date"],
            data["venue_id"],
            data.get("status", "scheduled"),
            datetime.now(),
        )

        cursor.execute(sql, values)
        conn.commit()
        match_id = cursor.lastrowid

        cursor.close()
        conn.close()

        return jsonify(
            {"message": "Match created successfully", "match_id": match_id}
        ), 201

    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500


@matches_bp.route("/<int:match_id>", methods=["PUT"])
@jwt_required()
def update_match(match_id):
    """Update a match"""
    data = request.get_json()

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Check if match exists
        cursor.execute("SELECT * FROM matches WHERE id = %s", (match_id,))
        match = cursor.fetchone()

        if not match:
            return jsonify({"error": "Match not found"}), 404

        # Build update query
        update_fields = []
        values = []

        allowed_fields = [
            "home_team_id",
            "away_team_id",
            "match_date",
            "venue_id",
            "home_score",
            "away_score",
            "status",
            "match_time",
        ]

        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = %s")
                values.append(data[field])

        if not update_fields:
            return jsonify({"error": "No fields to update"}), 400

        values.append(match_id)

        sql = f"UPDATE matches SET {', '.join(update_fields)} WHERE id = %s"
        cursor.execute(sql, values)
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"message": "Match updated successfully"}), 200

    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500


@matches_bp.route("/<int:match_id>", methods=["DELETE"])
@jwt_required()
def delete_match(match_id):
    """Delete a match"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Check if match exists
        cursor.execute("SELECT * FROM matches WHERE id = %s", (match_id,))
        match = cursor.fetchone()

        if not match:
            return jsonify({"error": "Match not found"}), 404

        # Delete lineup first
        cursor.execute("DELETE FROM match_lineups WHERE match_id = %s", (match_id,))

        # Delete match
        cursor.execute("DELETE FROM matches WHERE id = %s", (match_id,))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"message": "Match deleted successfully"}), 200

    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500


@matches_bp.route("/<int:match_id>/lineup", methods=["POST"])
@jwt_required()
def set_lineup(match_id):
    """Set match lineup (starting XI and bench)"""
    user_id = get_jwt_identity()
    data = request.get_json()

    players = data.get("players", [])
    if not players:
        return jsonify({"error": "No players provided"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Check if match exists
        cursor.execute("SELECT * FROM matches WHERE id = %s", (match_id,))
        match = cursor.fetchone()

        if not match:
            return jsonify({"error": "Match not found"}), 404

        # Clear existing lineup
        cursor.execute("DELETE FROM match_lineups WHERE match_id = %s", (match_id,))

        # Insert new lineup
        sql = """INSERT INTO match_lineups 
                 (match_id, player_id, position_type, position_order) 
                 VALUES (%s, %s, %s, %s)"""

        for idx, player in enumerate(players):
            position_type = "starting" if idx < 11 else "bench"
            cursor.execute(sql, (match_id, player["player_id"], position_type, idx))

        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"message": "Lineup set successfully"}), 200

    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500


@matches_bp.route("/active", methods=["GET"])
@jwt_required()
def get_active_matches():
    """Get currently active matches"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT m.*, 
                   h.name as home_team_name, 
                   a.name as away_team_name,
                   v.name as venue_name
            FROM matches m
            LEFT JOIN clubs h ON m.home_team_id = h.id
            LEFT JOIN clubs a ON m.away_team_id = a.id
            LEFT JOIN venues v ON m.venue_id = v.id
            WHERE m.status = 'live'
            ORDER BY m.match_date DESC
        """)

        matches = cursor.fetchall()

        for match in matches:
            if match.get("match_date"):
                match["match_date"] = match["match_date"].isoformat()

        cursor.close()
        conn.close()

        return jsonify(matches), 200

    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
