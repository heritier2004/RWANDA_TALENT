import os
import sys

# Add backend directory to path to import database
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from database import get_db_connection

def check_password_hash():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT username, password FROM users WHERE username = 'ferwafa'")
        user = cursor.fetchone()
        
        if user:
            print(f"User: {user['username']}")
            print(f"Hash: {user['password']}")
            # Check length and prefix
            is_valid = user['password'].startswith('$2b$') or user['password'].startswith('$2a$')
            print(f"Is valid bcrypt hash (prefix check): {is_valid}")
        else:
            print("User 'ferwafa' not found.")
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error checking hash: {e}")

if __name__ == "__main__":
    check_password_hash()
