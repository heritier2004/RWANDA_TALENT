import mysql.connector
from database import DB_CONFIG

def migrate():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("Adding location columns to players table...")
        
        # Add columns if they don't exist
        columns = [
            ("district", "VARCHAR(100)"),
            ("sector", "VARCHAR(100)"),
            ("cell", "VARCHAR(100)"),
            ("village", "VARCHAR(100)")
        ]
        
        for col_name, col_type in columns:
            try:
                cursor.execute(f"ALTER TABLE players ADD COLUMN {col_name} {col_type}")
                print(f"Added column: {col_name}")
            except mysql.connector.Error as err:
                if err.errno == 1060: # Column already exists
                    print(f"Column {col_name} already exists.")
                else:
                    print(f"Error adding {col_name}: {err}")
        
        conn.commit()
        print("Migration completed successfully.")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate()
