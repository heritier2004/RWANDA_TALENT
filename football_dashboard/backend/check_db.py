
import mysql.connector
try:
    from database import DB_CONFIG
except ImportError:
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'root',
        'password': '',
        'database': 'football_dashboard'
    }

def check_db():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        tables = ['clubs', 'academies', 'schools', 'players', 'matches', 'users']
        for table in tables:
            print(f"\n--- Table: {table} ---")
            try:
                cursor.execute(f"DESCRIBE {table}")
                columns = cursor.fetchall()
                for col in columns:
                    print(col)
            except Exception as e:
                print(f"Error describing {table}: {e}")
                
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    check_db()
