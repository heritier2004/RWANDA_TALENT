"""
Create test user in database
Run this script to add a test user for development

WARNING: This script creates a user with a password from environment variable.
Do NOT hardcode passwords in production!
"""
import os
import mysql.connector
from flask_bcrypt import Bcrypt

# Database configuration - use environment variables
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'database': os.environ.get('DB_NAME', 'football_dashboard'),
    'charset': 'utf8mb4'
}

def create_test_user():
    """Create test user with credentials from environment variables"""
    # Get credentials from environment
    test_username = os.environ.get('TEST_USER_NAME', 'test')
    test_email = os.environ.get('TEST_USER_EMAIL', 'test@test.com')
    test_password = os.environ.get('TEST_USER_PASSWORD')
    test_role = os.environ.get('TEST_USER_ROLE', 'superadmin')
    
    if not test_password:
        print("ERROR: TEST_USER_PASSWORD environment variable is not set!")
        print("Please set it before running this script:")
        print("  Windows: set TEST_USER_PASSWORD=your_password")
        print("  Linux/Mac: export TEST_USER_PASSWORD=your_password")
        return
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Generate password hash from environment variable
        bcrypt = Bcrypt()
        password_hash = bcrypt.generate_password_hash(test_password).decode('utf-8')
        
        # Insert test user
        cursor.execute("""
            INSERT INTO users (username, email, password, role, entity_id, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
            ON DUPLICATE KEY UPDATE password = %s
        """, (test_username, test_email, password_hash, test_role, None, password_hash))
        
        conn.commit()
        print(f"Test user created successfully!")
        print(f"Username: {test_username}")
        print(f"Role: {test_role}")
        print(f"Password: [HIDDEN - use TEST_USER_PASSWORD environment variable]")
        
        cursor.close()
        conn.close()
        
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
        print("\nMake sure:")
        print("1. MySQL server is running")
        print("2. Database 'football_dashboard' exists")
        print("3. Run the main SQL script first: football_dashboard/database/football_dashboard.sql")
        print("4. Set DB_HOST, DB_USER, DB_PASSWORD, DB_NAME environment variables")

if __name__ == '__main__':
    create_test_user()
