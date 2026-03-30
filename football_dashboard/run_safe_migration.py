import mysql.connector
from mysql.connector import Error
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from backend.database import get_db_connection


def column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table."""
    cursor.execute(
        """
        SELECT COUNT(*) FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = %s AND COLUMN_NAME = %s
    """,
        (table_name, column_name),
    )
    return cursor.fetchone()[0] > 0


def table_exists(cursor, table_name):
    """Check if a table exists in the database."""
    cursor.execute(
        """
        SELECT COUNT(*) FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = %s
    """,
        (table_name,),
    )
    return cursor.fetchone()[0] > 0


def constraint_exists(cursor, constraint_name):
    """Check if a foreign key constraint exists."""
    cursor.execute(
        """
        SELECT COUNT(*) FROM information_schema.REFERENTIAL_CONSTRAINTS
        WHERE CONSTRAINT_SCHEMA = DATABASE()
        AND CONSTRAINT_NAME = %s
    """,
        (constraint_name,),
    )
    return cursor.fetchone()[0] > 0


def safe_add_column(cursor, table, column, definition):
    """Add a column only if it doesn't exist."""
    if not column_exists(cursor, table, column):
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
            print(f"  + Added column {table}.{column}")
        except Error as e:
            print(f"  ! Could not add {table}.{column}: {e}")
    else:
        print(f"  = Column {table}.{column} already exists")


def run_safe_migration():
    print("=" * 60)
    print("  Football Dashboard - Safe Database Migration")
    print("  Migrating to Unified Schema v2.0")
    print("=" * 60)

    conn = get_db_connection()
    if not conn:
        print("FAIL: Could not connect to database.")
        print("Make sure MySQL is running and DB credentials are correct.")
        return False

    cursor = conn.cursor()
    migrated = 0

    try:
        # ================================================
        # 1. CREATE MISSING TABLES
        # ================================================
        print("\n[1/6] Creating missing tables...")

        tables = {
            "leagues": """
                CREATE TABLE IF NOT EXISTS leagues (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    category ENUM('Professional', 'Academy', 'School', 'Amateur') NOT NULL,
                    season VARCHAR(20) NOT NULL,
                    description TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_category (category)
                ) ENGINE=InnoDB
            """,
            "announcements": """
                CREATE TABLE IF NOT EXISTS announcements (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    content TEXT NOT NULL,
                    category ENUM('General', 'Match Update', 'Scouting', 'Regulation', 'Urgent') DEFAULT 'General',
                    target_role ENUM('all', 'school', 'academy', 'club', 'scout') DEFAULT 'all',
                    author_id INT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_created (created_at),
                    INDEX idx_target (target_role)
                ) ENGINE=InnoDB
            """,
            "live_streams": """
                CREATE TABLE IF NOT EXISTS live_streams (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    match_id INT,
                    team_id INT,
                    stream_name VARCHAR(255),
                    stream_url TEXT,
                    rtmp_url TEXT,
                    status VARCHAR(50) DEFAULT 'inactive',
                    started_at TIMESTAMP NULL,
                    ended_at TIMESTAMP NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_match_id (match_id),
                    INDEX idx_team_id (team_id),
                    INDEX idx_status (status)
                ) ENGINE=InnoDB
            """,
            "ml_training": """
                CREATE TABLE IF NOT EXISTS ml_training (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    model_type VARCHAR(50) DEFAULT 'yolov8',
                    status VARCHAR(50) DEFAULT 'pending',
                    progress INT DEFAULT 0,
                    team_id INT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_status (status),
                    INDEX idx_team_id (team_id)
                ) ENGINE=InnoDB
            """,
            "analytics_sessions": """
                CREATE TABLE IF NOT EXISTS analytics_sessions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    source_type ENUM('hardware', 'external_url', 'camera') NOT NULL,
                    external_url TEXT,
                    ingest_url TEXT,
                    stream_key VARCHAR(100),
                    watch_url TEXT,
                    status ENUM('Ready', 'In-Progress', 'Completed', 'Processing') DEFAULT 'Ready',
                    session_name VARCHAR(255),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_user (user_id),
                    INDEX idx_status (status)
                ) ENGINE=InnoDB
            """,
            "system_errors": """
                CREATE TABLE IF NOT EXISTS system_errors (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NULL,
                    error_message TEXT NOT NULL,
                    stack_trace TEXT,
                    endpoint VARCHAR(255),
                    severity ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium',
                    browser_info TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_user (user_id),
                    INDEX idx_severity (severity),
                    INDEX idx_created (created_at)
                ) ENGINE=InnoDB
            """,
            "player_talent_history": """
                CREATE TABLE IF NOT EXISTS player_talent_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    player_id INT NOT NULL,
                    match_id INT,
                    analysis_date DATE,
                    talent_score FLOAT,
                    speed_avg FLOAT,
                    distance_covered FLOAT,
                    sprints INT,
                    top_speed FLOAT,
                    notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_player (player_id),
                    INDEX idx_date (analysis_date)
                ) ENGINE=InnoDB
            """,
            "talent_recommendations": """
                CREATE TABLE IF NOT EXISTS talent_recommendations (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    player_id INT NOT NULL,
                    source VARCHAR(50),
                    recommendation_text TEXT,
                    status VARCHAR(50) DEFAULT 'pending',
                    scout_notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_status (status)
                ) ENGINE=InnoDB
            """,
        }

        for table_name, ddl in tables.items():
            if not table_exists(cursor, table_name):
                cursor.execute(ddl)
                print(f"  + Created table: {table_name}")
                migrated += 1
            else:
                print(f"  = Table {table_name} already exists")

        # ================================================
        # 2. FIX STATISTICS TABLE (merge AI + match stats)
        # ================================================
        print("\n[2/6] Fixing statistics table (adding AI tracking columns)...")

        if table_exists(cursor, "statistics"):
            stat_columns = [
                ("team_id", "INT DEFAULT NULL"),
                ("distance", "FLOAT DEFAULT 0"),
                ("avg_speed", "FLOAT DEFAULT 0"),
                ("max_speed", "FLOAT DEFAULT 0"),
                ("sprint_count", "INT DEFAULT 0"),
                ("high_speed_count", "INT DEFAULT 0"),
                ("performance_score", "FLOAT DEFAULT 0"),
                (
                    "updated_at",
                    "DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP",
                ),
            ]
            for col, defn in stat_columns:
                safe_add_column(cursor, "statistics", col, defn)
                migrated += 1

            # Add index on team_id if not exists
            try:
                cursor.execute("SHOW INDEX FROM statistics WHERE Key_name = 'idx_team'")
                if not cursor.fetchone():
                    cursor.execute(
                        "ALTER TABLE statistics ADD INDEX idx_team (team_id)"
                    )
                    print("  + Added index idx_team on statistics")
            except Error:
                pass

            # Add index on performance_score if not exists
            try:
                cursor.execute(
                    "SHOW INDEX FROM statistics WHERE Key_name = 'idx_performance'"
                )
                if not cursor.fetchone():
                    cursor.execute(
                        "ALTER TABLE statistics ADD INDEX idx_performance (performance_score DESC)"
                    )
                    print("  + Added index idx_performance on statistics")
            except Error:
                pass
        else:
            print(
                "  ! Statistics table not found - will be created by unified_schema.sql"
            )

        # ================================================
        # 3. FIX PLAYERS TABLE
        # ================================================
        print("\n[3/6] Fixing players table (adding missing columns)...")

        if table_exists(cursor, "players"):
            player_columns = [
                ("district", "VARCHAR(100)"),
                ("sector", "VARCHAR(100)"),
                ("cell", "VARCHAR(100)"),
                ("village", "VARCHAR(100)"),
            ]
            for col, defn in player_columns:
                safe_add_column(cursor, "players", col, defn)
                migrated += 1

            # Make registration_number nullable for AI-created players
            try:
                cursor.execute("""
                    SELECT IS_NULLABLE FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_NAME = 'players' AND COLUMN_NAME = 'registration_number'
                """)
                result = cursor.fetchone()
                if result and result[0] == "NO":
                    cursor.execute(
                        "ALTER TABLE players MODIFY COLUMN registration_number VARCHAR(50) NULL"
                    )
                    print("  + Made registration_number nullable (for AI players)")
            except Error as e:
                print(f"  ! Could not modify registration_number: {e}")

            # Make dob and nationality nullable for AI-created players
            try:
                cursor.execute("""
                    SELECT IS_NULLABLE FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_NAME = 'players' AND COLUMN_NAME = 'dob'
                """)
                result = cursor.fetchone()
                if result and result[0] == "NO":
                    cursor.execute("ALTER TABLE players MODIFY COLUMN dob DATE NULL")
                    print("  + Made dob nullable (for AI players)")
            except Error:
                pass

            try:
                cursor.execute("""
                    SELECT IS_NULLABLE FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_NAME = 'players' AND COLUMN_NAME = 'nationality'
                """)
                result = cursor.fetchone()
                if result and result[0] == "NO":
                    cursor.execute(
                        "ALTER TABLE players MODIFY COLUMN nationality VARCHAR(100) NULL DEFAULT 'Rwandan'"
                    )
                    print("  + Made nationality nullable with default 'Rwandan'")
            except Error:
                pass

            # Add 'Unknown' to position ENUM if not present
            try:
                cursor.execute("""
                    SELECT COLUMN_TYPE FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_NAME = 'players' AND COLUMN_NAME = 'position'
                """)
                result = cursor.fetchone()
                if result and "Unknown" not in result[0]:
                    cursor.execute("""ALTER TABLE players MODIFY COLUMN position ENUM('Goalkeeper', 'Defender', 'Midfielder', 'Forward',
                        'Center Back', 'Left Back', 'Right Back',
                        'Central Midfielder', 'Attacking Midfielder', 'Defensive Midfielder',
                        'Striker', 'Left Winger', 'Right Winger', 'Unknown') DEFAULT 'Unknown'""")
                    print("  + Added 'Unknown' to player position ENUM")
            except Error:
                pass

        # ================================================
        # 4. FIX USERS TABLE
        # ================================================
        print("\n[4/6] Fixing users table...")
        if table_exists(cursor, "users"):
            safe_add_column(cursor, "users", "is_active", "BOOLEAN DEFAULT TRUE")
            cursor.execute("UPDATE users SET is_active = TRUE WHERE is_active IS NULL")
            migrated += 1

        # ================================================
        # 5. FIX LIVE_STREAMS TABLE
        # ================================================
        print("\n[5/6] Fixing live_streams table...")
        if table_exists(cursor, "live_streams"):
            safe_add_column(cursor, "live_streams", "started_at", "TIMESTAMP NULL")
            safe_add_column(cursor, "live_streams", "ended_at", "TIMESTAMP NULL")
            safe_add_column(cursor, "live_streams", "team_id", "INT DEFAULT NULL")
            migrated += 1

        # ================================================
        # 6. SEED SAMPLE DATA
        # ================================================
        print("\n[6/6] Seeding sample data...")

        # Seed leagues
        sample_leagues = [
            (
                "Rwanda Premier League",
                "Professional",
                "2023/2024",
                "The top tier of professional football in Rwanda.",
            ),
            (
                "National Academy Series U17",
                "Academy",
                "2023/2024",
                "Elite youth development league for U17 players.",
            ),
            (
                "Inter-School Championship",
                "School",
                "2023/2024",
                "Annual football competition for secondary schools.",
            ),
        ]
        for name, cat, season, desc in sample_leagues:
            cursor.execute(
                "SELECT id FROM leagues WHERE name = %s AND season = %s", (name, season)
            )
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO leagues (name, category, season, description) VALUES (%s, %s, %s, %s)",
                    (name, cat, season, desc),
                )
                print(f"  + Seeded league: {name}")

        # Seed announcements
        if table_exists(cursor, "users"):
            sample_news = [
                (
                    "New Regulations on Youth Transfers",
                    "FERWAFA has released new guidelines for youth player transfers between academies and clubs.",
                    "Regulation",
                    "all",
                ),
                (
                    "Scouting Seminar in Kigali",
                    "A mandatory seminar for all registered scouts will be held next month at Amahoro Stadium.",
                    "Scouting",
                    "scout",
                ),
                (
                    "League Expansion Notice",
                    "The Rwanda Premier League will expand to 16 teams starting from the 2024/2025 season.",
                    "General",
                    "club",
                ),
            ]
            for title, content, cat, target in sample_news:
                cursor.execute(
                    "SELECT id FROM announcements WHERE title = %s", (title,)
                )
                if not cursor.fetchone():
                    cursor.execute(
                        "SELECT id FROM users WHERE role = 'ferwafa' LIMIT 1"
                    )
                    admin = cursor.fetchone()
                    author_id = admin[0] if admin else None
                    cursor.execute(
                        "INSERT INTO announcements (title, content, category, target_role, author_id) VALUES (%s, %s, %s, %s, %s)",
                        (title, content, cat, target, author_id),
                    )
                    print(f"  + Seeded announcement: {title}")

        conn.commit()
        print("\n" + "=" * 60)
        print(f"  Migration completed successfully!")
        print(f"  {migrated} changes applied.")
        print("=" * 60)
        return True

    except Error as e:
        print(f"\nFAIL: Migration error: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    success = run_safe_migration()
    sys.exit(0 if success else 1)
