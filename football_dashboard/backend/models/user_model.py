"""
User Model
Database operations for users
"""

import mysql.connector
from datetime import datetime
from database import get_db_connection

def get_user_by_id(user_id):
    """Get user by ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT id, username, email, role, entity_id, created_at 
            FROM users WHERE id = %s
        """, (user_id,))
        
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return user
        
    except mysql.connector.Error:
        return None

def get_user_by_username(username):
    """Get user by username"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return user
        
    except mysql.connector.Error:
        return None

def get_users_by_role(role):
    """Get all users with a specific role"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT id, username, email, role, entity_id, created_at 
            FROM users WHERE role = %s
        """, (role,))
        
        users = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return users
        
    except mysql.connector.Error:
        return []

def get_all_users():
    """Get all users (for super admin)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT id, username, email, role, entity_id, created_at 
            FROM users ORDER BY created_at DESC
        """)
        
        users = cursor.fetchall()
        
        for user in users:
            if user.get('created_at'):
                user['created_at'] = user['created_at'].isoformat()
        
        cursor.close()
        conn.close()
        
        return users
        
    except mysql.connector.Error:
        return []

def create_user(username, email, password, role, entity_id=None):
    """Create a new user"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        sql = """INSERT INTO users (username, email, password, role, entity_id, created_at) 
                  VALUES (%s, %s, %s, %s, %s, %s)"""
        
        values = (username, email, password, role, entity_id, datetime.now())
        
        cursor.execute(sql, values)
        conn.commit()
        user_id = cursor.lastrowid
        
        cursor.close()
        conn.close()
        
        return user_id
        
    except mysql.connector.Error:
        return None

def update_user(user_id, data):
    """Update user information"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        update_fields = []
        values = []
        
        # Use explicit allowlist to prevent SQL injection
        allowed_fields = {'username', 'email', 'role', 'entity_id'}
        
        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = %s")
                values.append(data[field])
        
        if not update_fields:
            return False
        
        values.append(user_id)
        
        sql = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
        cursor.execute(sql, values)
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return True
        
    except mysql.connector.Error:
        return False

def delete_user(user_id):
    """Delete a user"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return True
        
    except mysql.connector.Error:
        return False

def check_user_permissions(user_id, entity_type, entity_id):
    """Check if user has permissions for a specific entity"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT role, entity_id 
            FROM users WHERE id = %s
        """, (user_id,))
        
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not user:
            return False
        
        # Super admin and FERWAFA have access to everything
        if user['role'] in ['superadmin', 'ferwafa']:
            return True
        
        # Check if user is linked to the entity
        if user['entity_id'] == entity_id:
            return True
        
        return False
        
    except mysql.connector.Error:
        return False
