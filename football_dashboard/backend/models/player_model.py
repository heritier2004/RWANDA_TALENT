"""
Player Model
Database operations for players
"""

import mysql.connector
from datetime import datetime
import uuid
from database import get_db_connection


def generate_registration_number(role, entity_id):
    """Generate unique player registration number"""
    prefix = {"school": "SCH", "academy": "ACA", "club": "CLB"}.get(role, "GEN")
    unique_id = str(uuid.uuid4())[:8].upper()
    return f"{prefix}-{entity_id}-{unique_id}"


def get_all_players(filters=None):
    """Get all players with optional filters"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        sql = """
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
            WHERE 1=1
        """

        params = []

        if filters:
            if "entity_type" in filters and "entity_id" in filters:
                sql += f" AND p.{filters['entity_type']}_id = %s"
                params.append(filters["entity_id"])

            if "position" in filters:
                sql += " AND p.position = %s"
                params.append(filters["position"])

            if "search" in filters:
                sql += " AND (p.name LIKE %s OR p.registration_number LIKE %s)"
                search_term = f"%{filters['search']}%"
                params.extend([search_term, search_term])

        sql += " ORDER BY p.created_at DESC"

        cursor.execute(sql, params)
        players = cursor.fetchall()

        for player in players:
            if player.get("created_at"):
                player["created_at"] = player["created_at"].isoformat()
            if player.get("dob"):
                player["dob"] = player["dob"].isoformat()

        cursor.close()
        conn.close()

        return players

    except mysql.connector.Error:
        return []


def get_player_by_id(player_id):
    """Get player by ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
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
        """,
            (player_id,),
        )

        player = cursor.fetchone()

        if player:
            if player.get("created_at"):
                player["created_at"] = player["created_at"].isoformat()
            if player.get("dob"):
                player["dob"] = player["dob"].isoformat()

        cursor.close()
        conn.close()

        return player

    except mysql.connector.Error:
        return None


def get_player_by_registration(registration_number):
    """Get player by registration number"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM players WHERE registration_number = %s",
            (registration_number,),
        )
        player = cursor.fetchone()

        cursor.close()
        conn.close()

        return player

    except mysql.connector.Error:
        return None


def create_player(data, role, entity_id):
    """Create a new player"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Generate registration number
        reg_number = generate_registration_number(role, entity_id)

        sql = """INSERT INTO players 
                 (registration_number, name, dob, nationality, jersey_number, position, 
                  photo_url, school_id, academy_id, club_id, created_at) 
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

        school_id = entity_id if role == "school" else data.get("school_id")
        academy_id = entity_id if role == "academy" else data.get("academy_id")
        club_id = entity_id if role == "club" else data.get("club_id")

        values = (
            reg_number,
            data["name"],
            data["dob"],
            data["nationality"],
            data.get("jersey_number"),
            data["position"],
            data.get("photo_url"),
            school_id,
            academy_id,
            club_id,
            datetime.now(),
        )

        cursor.execute(sql, values)
        conn.commit()
        player_id = cursor.lastrowid

        cursor.close()
        conn.close()

        return player_id

    except mysql.connector.Error:
        return None


def update_player(player_id, data):
    """Update player information"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        update_fields = []
        values = []

        allowed_fields = [
            "name",
            "dob",
            "nationality",
            "jersey_number",
            "position",
            "photo_url",
            "school_id",
            "academy_id",
            "club_id",
        ]

        for field in allowed_fields:
            if field in data and data[field] is not None:
                update_fields.append(f"{field} = %s")
                values.append(data[field])

        if not update_fields:
            return False

        values.append(player_id)

        sql = f"UPDATE players SET {', '.join(update_fields)} WHERE id = %s"
        cursor.execute(sql, values)
        conn.commit()

        cursor.close()
        conn.close()

        return True

    except mysql.connector.Error:
        return False


def delete_player(player_id):
    """Delete a player"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("DELETE FROM players WHERE id = %s", (player_id,))
        conn.commit()

        cursor.close()
        conn.close()

        return True

    except mysql.connector.Error:
        return False


def get_players_by_entity(entity_type, entity_id):
    """Get all players for a specific entity"""
    # Validate entity_type against whitelist to prevent SQL injection
    allowed_entity_types = {"school", "academy", "club"}
    if entity_type not in allowed_entity_types:
        return []

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Use separate queries per entity type to avoid dynamic SQL column names
        if entity_type == "school":
            query = """
                SELECT * FROM players 
                WHERE school_id = %s
                ORDER BY jersey_number, name
            """
        elif entity_type == "academy":
            query = """
                SELECT * FROM players 
                WHERE academy_id = %s
                ORDER BY jersey_number, name
            """
        else:  # club
            query = """
                SELECT * FROM players 
                WHERE club_id = %s
                ORDER BY jersey_number, name
            """

        cursor.execute(query, (entity_id,))

        players = cursor.fetchall()

        for player in players:
            if player.get("created_at"):
                player["created_at"] = player["created_at"].isoformat()
            if player.get("dob"):
                player["dob"] = player["dob"].isoformat()

        cursor.close()
        conn.close()

        return players

    except mysql.connector.Error:
        return []


def search_players(query):
    """Search players by name or registration number"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        search_term = f"%{query}%"

        cursor.execute(
            """
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
            WHERE p.name LIKE %s OR p.registration_number LIKE %s
            ORDER BY p.name
            LIMIT 20
        """,
            (search_term, search_term),
        )

        players = cursor.fetchall()

        cursor.close()
        conn.close()

        return players

    except mysql.connector.Error:
        return []
