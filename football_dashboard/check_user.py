import os
import sys

# Add backend directory to path to import database
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from database import get_db_connection

def check_ferwafa_user():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT id, username, email, role, is_active FROM users WHERE username = 'ferwafa' OR role = 'ferwafa'")
        users = cursor.fetchall()
        
        if not users:
            print("No users found with username 'ferwafa' or role 'ferwafa'.")
        else:
            print("Found users:")
            for user in users:
                print(user)
                
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error checking user: {e}")

if __name__ == "__main__":
    check_ferwafa_user()
