import os
import sys
from flask_bcrypt import Bcrypt

# Add backend directory to path to import database
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from database import get_db_connection

def test_login():
    try:
        bcrypt = Bcrypt()
        test_password = "Ferwafa@2026"
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM users WHERE username = 'ferwafa'")
        user = cursor.fetchone()
        
        if not user:
            print("User 'ferwafa' not found in database.")
            return

        print(f"User found: {user['username']}")
        print(f"Stored Hash: {user['password']}")
        
        match = bcrypt.check_password_hash(user['password'], test_password)
        print(f"Password '{test_password}' match: {match}")
        
        # Test lowercase version just in case
        match_lower = bcrypt.check_password_hash(user['password'], test_password.lower())
        print(f"Password '{test_password.lower()}' match: {match_lower}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error testing login: {e}")

if __name__ == "__main__":
    test_login()
