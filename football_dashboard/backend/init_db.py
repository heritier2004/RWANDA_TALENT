"""
Database Initialization Script
Creates all required tables using the unified schema.
Run this once after setting up the database for the first time.
For existing databases, use run_safe_migration.py instead.
"""

import mysql.connector
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database import DB_CONFIG


def init_tables():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Create analytics_sessions table
        cursor.execute("""
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
            )
        """)

        # Create live_streams table with full columns
        cursor.execute("""
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
            )
        """)

        # Create ml_training table
        cursor.execute("""
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
            )
        """)

        # Create leagues table
        cursor.execute("""
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
        """)

        # Create announcements table
        cursor.execute("""
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
        """)

        # Ensure analytics_sessions source_type ENUM is correct
        try:
            cursor.execute(
                "ALTER TABLE analytics_sessions MODIFY COLUMN source_type ENUM('hardware', 'external_url', 'camera') NOT NULL"
            )
        except Exception:
            pass

        conn.commit()
        print("Database tables initialized successfully!")
        print("For full schema, run the unified_schema.sql or run_safe_migration.py")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error initializing database: {e}")


if __name__ == "__main__":
    init_tables()
