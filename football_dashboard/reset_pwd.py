import os
import sys
from flask_bcrypt import Bcrypt

# Add backend directory to path to import database
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from database import get_db_connection

def reset_ferwafa_password():
    try:
        bcrypt = Bcrypt()
        new_password = "Ferwafa@2026"
        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("UPDATE users SET password = %s WHERE username = 'ferwafa'", (hashed_password,))
        conn.commit()
        
        if cursor.rowcount > 0:
            print(f"Password for 'ferwafa' has been reset to: {new_password}")
        else:
            print("User 'ferwafa' not found or password update failed.")
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error resetting password: {e}")

if __name__ == "__main__":
    reset_ferwafa_password()
