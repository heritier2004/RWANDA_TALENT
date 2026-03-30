"""
Authentication Routes
Handles user login, registration, and session management
"""

import mysql.connector
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask_bcrypt import Bcrypt
from datetime import datetime
from database import get_db_connection

auth_bp = Blueprint("auth", __name__)
bcrypt = Bcrypt()


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user"""
    data = request.get_json()

    required_fields = ["username", "password", "email", "role"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    # Validate role
    valid_roles = ["school", "academy", "club", "scout", "ferwafa", "superadmin"]
    if data["role"] not in valid_roles:
        return jsonify({"error": "Invalid role"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Check if username exists
        cursor.execute("SELECT id FROM users WHERE username = %s", (data["username"],))
        if cursor.fetchone():
            return jsonify({"error": "Username already exists"}), 409

        # Hash password
        hashed_password = bcrypt.generate_password_hash(data["password"]).decode(
            "utf-8"
        )

        # Insert user
        sql = """INSERT INTO users (username, email, password, role, entity_id, created_at) 
                  VALUES (%s, %s, %s, %s, %s, %s)"""
        values = (
            data["username"],
            data["email"],
            hashed_password,
            data["role"],
            data.get("entity_id"),
            datetime.now(),
        )

        cursor.execute(sql, values)
        conn.commit()
        user_id = cursor.lastrowid

        cursor.close()
        conn.close()

        # Create access token - use string for consistency with login route
        access_token = create_access_token(identity=str(user_id))

        return jsonify(
            {
                "message": "User registered successfully",
                "user_id": user_id,
                "access_token": access_token,
                "role": data["role"],
            }
        ), 201

    except Exception as err:
        print(f"Registration error: {err}")
        # Check for duplicate entry
        if "Duplicate entry" in str(err):
            return jsonify({"error": "Email or username already exists"}), 409
        return jsonify({"error": "Registration failed"}), 500


@auth_bp.route("/login", methods=["POST"])
def login():
    """User login"""
    data = request.get_json()

    if not data or not data.get("username") or not data.get("password"):
        return jsonify({"error": "Missing username or password"}), 400

    login_id = data.get("username").strip()
    password = data.get("password")

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Get user by username OR email (case-insensitive for username)
        cursor.execute(
            "SELECT * FROM users WHERE LOWER(username) = LOWER(%s) OR LOWER(email) = LOWER(%s)",
            (login_id, login_id),
        )
        user = cursor.fetchone()

        # Log attempt (simplified for brevity)
        ip = request.remote_addr

        if not user:
            # Optionally log failed attempt to system_errors if suspicious
            cursor.execute(
                "INSERT INTO system_errors (error_message, endpoint, severity, created_at) VALUES (%s, %s, %s, %s)",
                (
                    f"Failed login attempt for unknown user: {login_id}",
                    "/api/auth/login",
                    "low",
                    datetime.now(),
                ),
            )
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({"error": "Invalid credentials"}), 401

        # Check password
        if not bcrypt.check_password_hash(user["password"], password):
            # Log failed password attempt
            cursor.execute(
                "INSERT INTO system_errors (error_message, endpoint, username, severity, created_at) VALUES (%s, %s, %s, %s, %s)",
                (
                    f"Invalid password for user: {user['username']}",
                    "/api/auth/login",
                    user["username"],
                    "medium",
                    datetime.now(),
                ),
            )
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({"error": "Invalid credentials"}), 401

        # Log successful login to audit_logs if it exists
        try:
            cursor.execute(
                "INSERT INTO audit_logs (username, action, table_name, record_id, ip_address, created_at) VALUES (%s, %s, %s, %s, %s, %s)",
                (user["username"], "login", "users", user["id"], ip, datetime.now()),
            )
            conn.commit()
        except Exception as e:
            print(f"Error logging login: {e}")

        cursor.close()
        conn.close()

        # Create access token
        access_token = create_access_token(identity=str(user["id"]))

        return jsonify(
            {
                "message": "Login successful",
                "access_token": access_token,
                "user": {
                    "id": user["id"],
                    "username": user["username"],
                    "email": user["email"],
                    "role": user["role"],
                    "entity_id": user["entity_id"],
                },
            }
        ), 200

    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500


@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    """User logout - client should discard token"""
    return jsonify({"message": "Logout successful"}), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_current_user():
    """Get current authenticated user"""
    user_id = get_jwt_identity()

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT id, username, email, role, entity_id, created_at FROM users WHERE id = %s",
            (user_id,),
        )
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if not user:
            return jsonify({"error": "User not found"}), 404

        return jsonify(user), 200

    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500


@auth_bp.route("/change-password", methods=["POST"])
@jwt_required()
def change_password():
    """Change user password"""
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data or not data.get("current_password") or not data.get("new_password"):
        return jsonify({"error": "Missing password fields"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Get current password
        cursor.execute("SELECT password FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        if not bcrypt.check_password_hash(user["password"], data["current_password"]):
            return jsonify({"error": "Current password is incorrect"}), 401

        # Update password
        hashed_password = bcrypt.generate_password_hash(data["new_password"]).decode(
            "utf-8"
        )
        cursor.execute(
            "UPDATE users SET password = %s WHERE id = %s", (hashed_password, user_id)
        )
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"message": "Password changed successfully"}), 200

    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500


# Role-based access helpers
@auth_bp.route("/roles", methods=["GET"])
def get_roles():
    """Get all available roles"""
    roles = [
        {"id": "school", "name": "School", "description": "School football team"},
        {"id": "academy", "name": "Academy", "description": "Football academy"},
        {"id": "club", "name": "Club", "description": "Football club"},
        {"id": "scout", "name": "Scout", "description": "Talent scout"},
        {
            "id": "ferwafa",
            "name": "FERWAFA",
            "description": "Rwanda Football Association",
        },
        {
            "id": "superadmin",
            "name": "Super Admin",
            "description": "System administrator",
        },
    ]
    return jsonify(roles), 200


@auth_bp.route("/users", methods=["GET"])
@jwt_required()
def get_users():
    """Get users with pagination (admin only)"""
    conn = None
    cursor = None
    try:
        # Get pagination parameters
        page = request.args.get("page", 1, type=int)
        limit = request.args.get("limit", 50, type=int)

        # Sanitize pagination values
        page = max(1, page)
        limit = min(max(1, limit), 100)  # Cap at 100 per page
        offset = (page - 1) * limit

        # Get current user to check role
        current_user_id = get_jwt_identity()
        if not current_user_id:
            return jsonify({"error": "Invalid token"}), 401

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor(dictionary=True)

        # Get current user details - use dictionary cursor for consistent access
        cursor.execute("SELECT role FROM users WHERE id = %s", (current_user_id,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "User not found"}), 404

        # Access role consistently from dictionary
        user_role = user.get("role")

        # Only superadmin can see all users
        if user_role != "superadmin":
            return jsonify({"error": "Access denied. Admin only."}), 403

        # Get total count for pagination
        cursor.execute("SELECT COUNT(*) as total FROM users")
        total_count = cursor.fetchone()["total"]

        # Get paginated users
        cursor.execute(
            """
            SELECT id, username, email, role, entity_id, is_active, created_at, updated_at
            FROM users
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """,
            (limit, offset),
        )
        users = cursor.fetchall()

        # Convert datetime to string
        for u in users:
            if u.get("created_at"):
                u["created_at"] = u["created_at"].isoformat()
            if u.get("updated_at"):
                u["updated_at"] = u["updated_at"].isoformat()
            # Convert is_active to boolean
            u["is_active"] = bool(u.get("is_active", True))

        return jsonify(
            {
                "users": users,
                "count": len(users),
                "total": total_count,
                "page": page,
                "limit": limit,
                "total_pages": (total_count + limit - 1) // limit,
            }
        ), 200

    except Exception as e:
        print(f"Error getting users: {e}")
        return jsonify({"error": "Failed to retrieve users"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


@auth_bp.route("/users/<int:user_id>", methods=["PUT"])
@jwt_required()
def update_user(user_id):
    """Update user details (email, role, entity_id) - admin only"""
    current_user_id = get_jwt_identity()
    if not current_user_id:
        return jsonify({"error": "Invalid token"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing update data"}), 400

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Check if current user is admin
        cursor.execute("SELECT role FROM users WHERE id = %s", (current_user_id,))
        user = cursor.fetchone()

        if not user or user.get("role") != "superadmin":
            return jsonify({"error": "Access denied. Admin only."}), 403

        # Check if target user exists
        cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        if not cursor.fetchone():
            return jsonify({"error": "User not found"}), 404

        # Build update query
        allowed_fields = ["email", "role", "entity_id", "is_active"]
        update_parts = []
        values = []

        for field in allowed_fields:
            if field in data:
                update_parts.append(f"{field} = %s")
                values.append(data[field])

        if not update_parts:
            return jsonify({"error": "No valid fields provided for update"}), 400

        sql = f"UPDATE users SET {', '.join(update_parts)}, updated_at = NOW() WHERE id = %s"
        values.append(user_id)

        cursor.execute(sql, tuple(values))
        conn.commit()

        return jsonify({"message": "User updated successfully"}), 200

    except Exception as e:
        print(f"Error updating user: {e}")
        if conn:
            conn.rollback()
        return jsonify({"error": "Failed to update user"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@auth_bp.route("/users/<int:user_id>", methods=["DELETE"])
@jwt_required()
def delete_user(user_id):
    """Delete a user (admin only)"""
    # Validate user_id - must be positive integer
    if not isinstance(user_id, int) or user_id <= 0:
        return jsonify({"error": "Invalid user ID"}), 400

    current_user_id = get_jwt_identity()
    if not current_user_id:
        return jsonify({"error": "Invalid token"}), 401

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor(dictionary=True)

        # Get current user to check role - use dictionary cursor for consistency
        cursor.execute("SELECT role FROM users WHERE id = %s", (current_user_id,))
        user = cursor.fetchone()

        if not user or user.get("role") != "superadmin":
            return jsonify({"error": "Access denied. Admin only."}), 403

        # Don't allow deleting yourself - convert both to int for comparison
        try:
            if int(user_id) == int(current_user_id):
                return jsonify({"error": "Cannot delete your own account"}), 400
        except (ValueError, TypeError):
            pass

        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        if not cursor.fetchone():
            return jsonify({"error": "User not found"}), 404

        # Delete user
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()

        return jsonify({"message": "User deleted successfully"}), 200

    except Exception as e:
        print(f"Error deleting user: {e}")
        if conn:
            conn.rollback()
        return jsonify({"error": "Failed to delete user"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


@auth_bp.route("/users/<int:user_id>/toggle", methods=["POST"])
@jwt_required()
def toggle_user_status(user_id):
    """Toggle user active status (pause/activate) - admin only"""
    current_user_id = get_jwt_identity()
    if not current_user_id:
        return jsonify({"error": "Invalid token"}), 401

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor(dictionary=True)

        # Get current user to check role
        cursor.execute("SELECT role FROM users WHERE id = %s", (current_user_id,))
        user = cursor.fetchone()

        if not user or user.get("role") != "superadmin":
            return jsonify({"error": "Access denied. Admin only."}), 403

        # Don't allow toggling your own status
        if user_id == current_user_id:
            return jsonify({"error": "Cannot toggle your own status"}), 400

        # Get target user current status
        cursor.execute(
            "SELECT id, username, is_active FROM users WHERE id = %s", (user_id,)
        )
        target_user = cursor.fetchone()

        if not target_user:
            return jsonify({"error": "User not found"}), 404

        # Toggle the status
        new_status = not target_user.get("is_active", True)
        cursor.execute(
            "UPDATE users SET is_active = %s WHERE id = %s", (new_status, user_id)
        )
        conn.commit()

        status_text = "activated" if new_status else "deactivated"
        return jsonify(
            {"message": f"User {status_text} successfully", "is_active": new_status}
        ), 200

    except Exception as e:
        print(f"Error toggling user status: {e}")
        if conn:
            conn.rollback()
        return jsonify({"error": "Failed to toggle user status"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
