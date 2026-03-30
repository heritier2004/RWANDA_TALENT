"""
Schema Verification Script
Checks that all required tables and columns exist for the unified schema.
"""

import mysql.connector
from database import get_db_connection


def check_schema():
    conn = get_db_connection()
    if not conn:
        print("FAIL: Could not connect to database")
        return

    cursor = conn.cursor()
    issues = []

    # Tables that must exist
    required_tables = [
        "users",
        "schools",
        "academies",
        "clubs",
        "venues",
        "players",
        "matches",
        "match_lineups",
        "statistics",
        "scouts",
        "favorites",
        "training_sessions",
        "live_streams",
        "ml_training",
        "analytics_sessions",
        "leagues",
        "announcements",
        "system_errors",
        "audit_logs",
        "player_talent_history",
        "talent_recommendations",
    ]

    print("Checking required tables...")
    for table in required_tables:
        cursor.execute(
            """
            SELECT COUNT(*) FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s
        """,
            (table,),
        )
        if cursor.fetchone()[0] == 0:
            issues.append(f"Missing table: {table}")
            print(f"  FAIL: {table}")
        else:
            print(f"  OK: {table}")

    # Critical columns that must exist
    critical_checks = {
        "statistics": [
            "team_id",
            "distance",
            "avg_speed",
            "max_speed",
            "sprint_count",
            "high_speed_count",
            "performance_score",
            "goals",
            "assists",
            "minutes_played",
            "yellow_cards",
            "red_cards",
            "rating",
        ],
        "players": [
            "registration_number",
            "name",
            "position",
            "school_id",
            "academy_id",
            "club_id",
            "height_cm",
            "weight_kg",
            "district",
            "sector",
            "cell",
            "village",
        ],
        "users": ["role", "entity_id", "is_active"],
        "live_streams": ["team_id", "started_at", "ended_at"],
    }

    print("\nChecking critical columns...")
    for table, columns in critical_checks.items():
        cursor.execute(
            """
            SELECT COUNT(*) FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s
        """,
            (table,),
        )
        if cursor.fetchone()[0] == 0:
            print(f"  SKIP: {table} (table missing)")
            continue

        for col in columns:
            cursor.execute(
                """
                SELECT COUNT(*) FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = %s AND COLUMN_NAME = %s
            """,
                (table, col),
            )
            if cursor.fetchone()[0] == 0:
                issues.append(f"Missing column: {table}.{col}")
                print(f"  FAIL: {table}.{col}")
            else:
                print(f"  OK: {table}.{col}")

    cursor.close()
    conn.close()

    print("\n" + "=" * 50)
    if issues:
        print(f"ISSUES FOUND: {len(issues)}")
        for issue in issues:
            print(f"  - {issue}")
        print("\nRun 'python run_safe_migration.py' to fix these issues.")
    else:
        print("All checks passed! Schema is complete.")
    print("=" * 50)


if __name__ == "__main__":
    check_schema()
