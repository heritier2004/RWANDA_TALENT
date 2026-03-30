"""
Logs Routes
Handles system errors and audit logs (usage history)
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import mysql.connector
from datetime import datetime
from database import get_db_connection

logs_bp = Blueprint('logs', __name__)

@logs_bp.route('/errors', methods=['GET'])
@jwt_required()
def get_errors():
    """Get system errors with filtering"""
    user_id = get_jwt_identity()
    
    # Check if user is superadmin
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT role FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user or user['role'] != 'superadmin':
            return jsonify({'error': 'Unauthorized'}), 403
            
        # Pagination and filters
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        severity = request.args.get('severity')
        
        query = "SELECT e.*, u.username FROM system_errors e LEFT JOIN users u ON e.user_id = u.id"
        params = []
        
        if severity:
            query += " WHERE e.severity = %s"
            params.append(severity)
            
        query += " ORDER BY e.created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        cursor.execute(query, tuple(params))
        errors = cursor.fetchall()
        
        for error in errors:
            if error.get('created_at'):
                error['created_at'] = error['created_at'].isoformat()
                
        cursor.close()
        conn.close()
        
        return jsonify(errors), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@logs_bp.route('/usage', methods=['GET'])
@jwt_required()
def get_usage_history():
    """Get audit logs (usage history)"""
    user_id = get_jwt_identity()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT role FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user or user['role'] != 'superadmin':
            return jsonify({'error': 'Unauthorized'}), 403
            
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        action = request.args.get('action')
        
        query = "SELECT a.*, u.username FROM audit_logs a LEFT JOIN users u ON a.user_id = u.id"
        params = []
        
        if action:
            query += " WHERE a.action LIKE %s"
            params.append(f"%{action}%")
            
        query += " ORDER BY a.created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        cursor.execute(query, tuple(params))
        logs = cursor.fetchall()
        
        for log in logs:
            if log.get('created_at'):
                log['created_at'] = log['created_at'].isoformat()
                
        cursor.close()
        conn.close()
        
        return jsonify(logs), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@logs_bp.route('/report-error', methods=['POST'])
def report_error():
    """Endpoint for frontend to report errors"""
    data = request.get_json()
    
    # Try to get user_id from JWT if present (optional for this endpoint)
    # But often errors happen before login or during session expiry
    user_id = None
    # We don't use @jwt_required() here because we want to capture errors even if JWT is invalid/expired
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO system_errors (user_id, error_message, stack_trace, endpoint, severity, browser_info)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            data.get('user_id'),
            data.get('message', 'Unknown frontend error'),
            data.get('stack'),
            data.get('url'),
            data.get('severity', 'medium'),
            request.headers.get('User-Agent')
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'status': 'logged'}), 200
    except Exception as e:
        print(f"Failed to log frontend error: {e}")
        return jsonify({'error': 'Failed to log error'}), 500
