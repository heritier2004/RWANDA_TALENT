"""Test database connection"""
import os
import mysql.connector

# Set environment variables for XAMPP
os.environ['DB_HOST'] = 'localhost'
os.environ['DB_USER'] = 'root'
os.environ['DB_PASSWORD'] = ''
os.environ['DB_NAME'] = 'football_dashboard'

# Import after setting env
from database import get_db_connection

print("Testing database connection...")
print(f"DB_HOST: {os.environ.get('DB_HOST')}")
print(f"DB_USER: {os.environ.get('DB_USER')}")
print(f"DB_NAME: {os.environ.get('DB_NAME')}")

conn = get_db_connection()
if conn:
    print("SUCCESS: Database connection works!")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    print(f"Found {count} users in database")
    cursor.close()
    conn.close()
else:
    print("FAILED: Database connection error!")
    print("Make sure XAMPP MySQL is running (check XAMPP Control Panel)")