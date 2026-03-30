"""
AI Stats API Routes
Receives statistics from AI module and saves to database
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from database import get_db_connection

ai_stats_bp = Blueprint("ai_stats", __name__)


def _verify_team_access(cursor, user_id, team_id):
    """Verify user has access to the specified team.

    Returns True if user has access, False otherwise.
    """
    # Get user's role and entity_id
    cursor.execute("SELECT role, entity_id FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()

    if not user:
        return False

    # Handle both dict (dictionary=True cursor) and tuple (regular cursor) return types
    # This prevents TypeError when cursor type changes
    if isinstance(user, dict):
        role = user.get("role")
        entity_id = user.get("entity_id")
    else:
        # Assume tuple (role, entity_id)
        try:
            role, entity_id = user
        except (TypeError, ValueError) as e:
            print(f"ERROR: Unexpected user data format: {user}, error: {e}")
            return False

    # Superadmin has access to all teams
    if role == "superadmin":
        return True

    # Check if user is associated with this team via entity_id
    # entity_id maps to school/academy/club id - with safe type conversion
    if entity_id is not None and team_id is not None:
        try:
            user_entity_id = int(entity_id)
            target_team_id = int(team_id)
            if user_entity_id == target_team_id:
                return True
        except (ValueError, TypeError):
            pass  # Invalid entity_id format, continue to other checks

    # Ferwafa (federation) can submit stats for all teams
    # Scouts can only VIEW data, not submit stats
    if role == "ferwafa":
        return True

    return False


def _team_exists(cursor, team_id):
    """Check if a team exists in the database.

    Uses clubs table since there's no separate teams table.
    Also checks academies and schools for entity_id compatibility.
    """
    # Check clubs first (most common for matches)
    cursor.execute("SELECT id FROM clubs WHERE id = %s", (team_id,))
    if cursor.fetchone():
        return True

    # Check academies
    cursor.execute("SELECT id FROM academies WHERE id = %s", (team_id,))
    if cursor.fetchone():
        return True

    # Check schools
    cursor.execute("SELECT id FROM schools WHERE id = %s", (team_id,))
    return cursor.fetchone() is not None


@ai_stats_bp.route("/stats", methods=["POST"])
@jwt_required()
def receive_ai_stats():
    """
    Receive statistics from AI module
    Called every 15 minutes by the AI runner
    """
    conn = None
    cursor = None
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Get current user identity for authorization
        current_user_id = get_jwt_identity()

        match_id = data.get("match_id")
        team_id = data.get("team_id")
        timestamp = data.get("timestamp")
        elapsed_minutes = data.get("elapsed_minutes", 0)
        players = data.get("players", [])
        match_stats = data.get("match_stats", {})
        events = data.get("events", [])

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor()

        # Validate main IDs - handle None explicitly to avoid TypeError
        try:
            match_id = int(match_id) if match_id is not None else 0
            team_id = int(team_id) if team_id is not None else 0
        except (ValueError, TypeError) as e:
            return jsonify({"error": "Invalid match_id or team_id format"}), 400

        # Validate team_id is valid
        if team_id <= 0:
            return jsonify({"error": "Invalid team_id"}), 400

        # Validate match_id is valid when provided
        if match_id < 0:
            return jsonify({"error": "match_id must be a non-negative integer"}), 400

        # Validate team exists
        if not _team_exists(cursor, team_id):
            return jsonify({"error": "Team not found"}), 404

        # Authorization: Verify user has access to this team
        if not _verify_team_access(cursor, current_user_id, team_id):
            return jsonify(
                {
                    "error": "Access denied. You do not have permission to add stats for this team."
                }
            ), 403

        # Insert player statistics
        for player in players:
            track_id = player.get("track_id", 0)
            jersey_number = player.get("jersey_number")  # Get detected jersey number
            total_distance = float(player.get("total_distance", 0))
            avg_speed = float(player.get("avg_speed", 0))
            max_speed = float(player.get("max_speed", 0))
            sprint_count = int(player.get("sprint_count", 0))
            high_speed_count = int(player.get("high_speed_count", 0))
            minutes = float(player.get("minutes", 0))
            performance_score = float(player.get("performance_score", 0))

            # Try to find player by jersey_number (ideal) or track_id (fallback)
            player_id = _get_or_create_player(cursor, track_id, team_id, jersey_number)

            # Insert statistics with team_id
            insert_stat = """
                INSERT INTO statistics 
                (player_id, match_id, team_id, distance, avg_speed, max_speed, 
                 sprint_count, high_speed_count, minutes_played, performance_score, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            cursor.execute(
                insert_stat,
                (
                    player_id,
                    match_id,
                    team_id,
                    total_distance,
                    avg_speed,
                    max_speed,
                    sprint_count,
                    high_speed_count,
                    int(minutes),
                    performance_score,
                    datetime.now(),
                ),
            )

        conn.commit()

        return jsonify(
            {
                "success": True,
                "message": f"Stats saved for {len(players)} players",
                "match_id": match_id,
                "elapsed_minutes": elapsed_minutes,
            }
        ), 200

    except Exception as e:
        import traceback

        print(f"Error processing AI stats: {e}")
        traceback.print_exc()
        if conn:
            conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


@ai_stats_bp.route("/test-stats", methods=["POST"])
@jwt_required()
def receive_test_stats():
    """Test endpoint: inserts stats without team/match validation"""
    conn = None
    cursor = None
    try:
        data = request.get_json()
        current_user_id = get_jwt_identity()

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor()

        # Get user info
        cursor.execute(
            "SELECT role, entity_id FROM users WHERE id = %s", (current_user_id,)
        )
        user = cursor.fetchone()
        if not user:
            return jsonify({"error": "User not found"}), 404

        role = user[0] if isinstance(user, tuple) else user.get("role")
        entity_id = user[1] if isinstance(user, tuple) else user.get("entity_id")

        # Use entity_id as team_id, default to 1
        team_id = entity_id if entity_id else 1
        match_id = data.get("match_id", 1)
        players = data.get("players", [])

        # Ensure a match exists (create if needed)
        cursor.execute("SELECT id FROM matches WHERE id = %s", (match_id,))
        if not cursor.fetchone():
            try:
                cursor.execute(
                    "INSERT INTO matches (home_team_id, away_team_id, match_date, status) VALUES (%s, %s, %s, %s)",
                    (
                        team_id,
                        (team_id % 10) + 1,
                        datetime.now().strftime("%Y-%m-%d"),
                        "completed",
                    ),
                )
                match_id = cursor.lastrowid
                conn.commit()
                print(f"[TEST-STATS] Created match ID: {match_id}")
            except Exception as me:
                print(f"[TEST-STATS] Could not create match: {me}")

        # Insert stats directly without validation
        for player in players:
            track_id = player.get("track_id", 0)
            total_distance = float(player.get("total_distance", 0))
            avg_speed = float(player.get("avg_speed", 0))
            max_speed = float(player.get("max_speed", 0))
            sprint_count = int(player.get("sprint_count", 0))
            high_speed_count = int(player.get("high_speed_count", 0))
            minutes = float(player.get("minutes", 0))
            performance_score = float(player.get("performance_score", 0))

            # Create a placeholder player for this track
            player_name = f"AI_Player_{track_id}"
            cursor.execute(
                "SELECT id FROM players WHERE name = %s AND (club_id = %s OR school_id = %s OR academy_id = %s)",
                (player_name, team_id, team_id, team_id),
            )
            existing = cursor.fetchone()
            if existing:
                player_id = existing[0]
            else:
                cursor.execute(
                    """INSERT INTO players (name, registration_number, club_id, school_id, academy_id, position, nationality)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (
                        player_name,
                        f"AI-{track_id}",
                        team_id if role == "club" else None,
                        team_id if role == "school" else None,
                        team_id if role == "academy" else None,
                        "Unknown",
                        "Unknown",
                    ),
                )
                player_id = cursor.lastrowid

            # Insert statistics
            cursor.execute(
                """INSERT INTO statistics
                   (player_id, match_id, team_id, distance, avg_speed, max_speed,
                    sprint_count, high_speed_count, minutes_played, performance_score, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    player_id,
                    match_id,
                    team_id,
                    total_distance,
                    avg_speed,
                    max_speed,
                    sprint_count,
                    high_speed_count,
                    int(minutes),
                    performance_score,
                    datetime.now(),
                ),
            )

        conn.commit()
        return jsonify(
            {"success": True, "message": f"Test stats saved for {len(players)} players"}
        ), 200

    except Exception as e:
        import traceback

        print(f"Error in test-stats: {e}")
        traceback.print_exc()
        if conn:
            conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def _get_or_create_player(cursor, track_id, team_id, jersey_number=None):
    """Get or create a player entry based on AI detection.

    Priority 1: Match by jersey_number and team_id (Real database player)
    Priority 2: Match by track_id-based name (Existing AI player)
    Priority 3: Create new AI player
    """
    # 1. Try matching by Jersey Number within the team
    if jersey_number is not None:
        try:
            jn = int(jersey_number)
            # Check clubs
            cursor.execute(
                "SELECT id FROM players WHERE jersey_number = %s AND club_id = %s",
                (jn, team_id),
            )
            res = cursor.fetchone()
            if res:
                return res[0]

            # Check academies
            cursor.execute(
                "SELECT id FROM players WHERE jersey_number = %s AND academy_id = %s",
                (jn, team_id),
            )
            res = cursor.fetchone()
            if res:
                return res[0]

            # Check schools
            cursor.execute(
                "SELECT id FROM players WHERE jersey_number = %s AND school_id = %s",
                (jn, team_id),
            )
            res = cursor.fetchone()
            if res:
                return res[0]
        except (ValueError, TypeError):
            pass

    # 2. Try matching by track_id-based name (Fallback)
    try:
        track_id = int(track_id)
    except (ValueError, TypeError):
        track_id = 0

    player_name = f"Player_{track_id}"
    if jersey_number:
        player_name = f"Team{team_id}_J{jersey_number}"

    cursor.execute("SELECT id FROM players WHERE name = %s", (player_name,))
    result = cursor.fetchone()

    if result:
        return result[0]

    # Determine which entity_id to use based on team_id
    # team_id could be club_id, academy_id, or school_id
    club_id = None
    academy_id = None
    school_id = None

    # Check if team_id exists in each table to determine type
    cursor.execute("SELECT id FROM clubs WHERE id = %s", (team_id,))
    if cursor.fetchone():
        club_id = int(team_id)
    else:
        cursor.execute("SELECT id FROM academies WHERE id = %s", (team_id,))
        if cursor.fetchone():
            academy_id = int(team_id)
        else:
            cursor.execute("SELECT id FROM schools WHERE id = %s", (team_id,))
            if cursor.fetchone():
                school_id = int(team_id)

    # Create new player with validated data using correct column
    cursor.execute(
        """
        INSERT INTO players (name, club_id, academy_id, school_id, position, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
    """,
        (player_name, club_id, academy_id, school_id, "Unknown", datetime.now()),
    )

    return cursor.lastrowid


@ai_stats_bp.route("/stats/<int:match_id>", methods=["GET"])
@jwt_required()
def get_match_stats(match_id):
    """Get statistics for a specific match"""
    conn = None
    cursor = None
    try:
        current_user_id = get_jwt_identity()

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor(dictionary=True)

        # Get match to find associated team
        cursor.execute("SELECT team_id FROM matches WHERE id = %s", (match_id,))
        match = cursor.fetchone()

        if match:
            team_id = match.get("team_id") or match.get(0)  # Handle both dict and tuple
            if team_id:
                # Authorization: Verify user has access to this team
                if not _verify_team_access(cursor, current_user_id, team_id):
                    return jsonify(
                        {
                            "error": "Access denied. You do not have permission to view stats for this team."
                        }
                    ), 403

        # Get player statistics
        cursor.execute(
            """
            SELECT
                p.id,
                p.name,
                p.position,
                p.jersey_number,
                s.distance,
                s.avg_speed,
                s.max_speed,
                s.sprint_count,
                s.minutes_played,
                s.performance_score,
                s.created_at
            FROM statistics s
            JOIN players p ON s.player_id = p.id
            WHERE s.match_id = %s
            ORDER BY s.performance_score DESC
        """,
            (match_id,),
        )

        stats = cursor.fetchall()

        # Convert datetime to string
        for stat in stats:
            if stat.get("created_at"):
                stat["created_at"] = stat["created_at"].isoformat()

        return jsonify(
            {"match_id": match_id, "statistics": stats, "total_players": len(stats)}
        ), 200

    except Exception as e:
        print(f"Error getting match stats: {e}")
        return jsonify({"error": "Failed to retrieve match statistics"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


@ai_stats_bp.route("/top-players", methods=["GET"])
@jwt_required()
def get_top_players():
    """Get top performing players across all matches"""
    conn = None
    cursor = None
    try:
        limit = request.args.get("limit", 10, type=int)

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT 
                p.id,
                p.name,
                p.position,
                p.jersey_number,
                p.photo_url,
                AVG(s.performance_score) as avg_performance,
                AVG(s.distance) as avg_distance,
                AVG(s.avg_speed) as avg_speed,
                AVG(s.sprint_count) as avg_sprints,
                COUNT(s.id) as match_count
            FROM players p
            JOIN statistics s ON p.id = s.player_id
            GROUP BY p.id
            ORDER BY avg_performance DESC
            LIMIT %s
        """,
            (limit,),
        )

        players = cursor.fetchall()

        # Convert to JSON serializable
        for player in players:
            if player.get("avg_performance"):
                player["avg_performance"] = float(player["avg_performance"])
            if player.get("avg_distance"):
                player["avg_distance"] = float(player["avg_distance"])
            if player.get("avg_speed"):
                player["avg_speed"] = float(player["avg_speed"])

        return jsonify({"top_players": players, "count": len(players)}), 200

    except Exception as e:
        print(f"Error getting top players: {e}")
        return jsonify({"error": "Failed to retrieve player rankings"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


@ai_stats_bp.route("/report/<int:match_id>", methods=["GET"])
@jwt_required()
def get_match_report(match_id):
    """Get aggregate match report including team and player deep-dive"""
    conn = None
    cursor = None
    try:
        user_id = get_jwt_identity()
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Get team aggregates
        cursor.execute(
            """
            SELECT 
                SUM(distance) as team_distance,
                AVG(avg_speed) as team_avg_speed,
                MAX(max_speed) as team_top_speed,
                SUM(sprint_count) as team_sprints,
                AVG(performance_score) as team_quality
            FROM statistics 
            WHERE match_id = %s
        """,
            (match_id,),
        )
        team_stats = cursor.fetchone()

        if not team_stats or team_stats["team_distance"] is None:
            return jsonify({"error": "No statistics found for this match"}), 404

        # Get individual breakdown
        cursor.execute(
            """
            SELECT 
                p.name, p.position, p.jersey_number,
                s.distance, s.avg_speed, s.max_speed, s.sprint_count, s.performance_score
            FROM statistics s
            JOIN players p ON s.player_id = p.id
            WHERE s.match_id = %s
            ORDER BY s.performance_score DESC
        """,
            (match_id,),
        )
        player_stats = cursor.fetchall()

        return jsonify(
            {
                "success": True,
                "match_id": match_id,
                "team_stats": {
                    "total_distance": float(team_stats["team_distance"] or 0),
                    "avg_speed": float(team_stats["team_avg_speed"] or 0),
                    "top_speed": float(team_stats["team_top_speed"] or 0),
                    "total_sprints": int(team_stats["team_sprints"] or 0),
                    "quality_score": float(team_stats["team_quality"] or 0),
                },
                "player_stats": player_stats,
            }
        ), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
