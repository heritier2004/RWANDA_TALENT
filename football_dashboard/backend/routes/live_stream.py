"""
Live Stream and ML Training API Routes
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import uuid
import os
import sys
from database import get_db_connection

live_stream_bp = Blueprint("live_stream", __name__)

# Allowed model types for ML training
ALLOWED_MODEL_TYPES = frozenset(["yolov8", "yolov5", "faster_rcnn"])


def _verify_team_access(cursor, user_id, team_id):
    """Verify user has access to the specified team.

    Returns True if user has access, False otherwise.
    """
    # Get user's role and entity_id
    cursor.execute("SELECT role, entity_id FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()

    if not user:
        return False

    # Handle both tuple (non-dict cursor) and dict (dictionary=True cursor)
    # This prevents TypeError when cursor type changes
    if isinstance(user, dict):
        role = user.get("role")
        entity_id = user.get("entity_id")
    else:
        # Assume tuple (role, entity_id)
        try:
            role, entity_id = user
        except (TypeError, ValueError) as e:
            print(f"ERROR: Unexpected user data format: {user}, error: {e}")
            return False

    # Superadmin has access to all teams
    if role == "superadmin":
        return True

    # Check if user is associated with this team via entity_id
    # Safely handle None values to avoid TypeError
    if entity_id is not None and team_id is not None:
        try:
            if int(entity_id) == int(team_id):
                return True
        except (ValueError, TypeError):
            pass  # Invalid format, continue to other checks

    # Ferwafa (federation) has access to all teams
    if role == "ferwafa":
        return True

    return False


def _get_stream_team_id(cursor, stream_id):
    """Get the team_id associated with a stream."""
    cursor.execute("SELECT team_id FROM live_streams WHERE id = %s", (stream_id,))
    result = cursor.fetchone()
    return result[0] if result else None


# Stream server configuration from environment variables
def get_stream_config():
    """Get stream server configuration from environment variables"""
    return {
        "rtmp_host": os.environ.get("RTMP_HOST", "localhost"),
        "stream_port": os.environ.get("STREAM_PORT", "8080"),
        "stream_path": os.environ.get("STREAM_PATH", "live"),
    }


@live_stream_bp.route("/create", methods=["POST"])
@jwt_required()
def create_stream():
    """Create a new live stream"""
    data = request.get_json()
    conn = None
    cursor = None

    # Validate and convert IDs to integers
    try:
        match_id = int(data.get("match_id")) if data.get("match_id") else None
        team_id = int(data.get("team_id")) if data.get("team_id") else None
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid match_id or team_id"}), 400

    # Validate and sanitize stream_name - limit length and strip special chars
    raw_stream_name = data.get("stream_name", "")
    if raw_stream_name:
        # Limit to 100 chars and remove potentially dangerous characters
        # Allow only alphanumeric, spaces, hyphens, underscores
        import re

        stream_name = re.sub(r"[^\w\s\-_]", "", raw_stream_name)[:100].strip()
        if not stream_name:
            stream_name = f"Stream_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    else:
        stream_name = f"Stream_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Generate unique stream key - use full UUID for better entropy
    stream_key = str(uuid.uuid4())

    # Get stream configuration from environment
    stream_config = get_stream_config()
    rtmp_url = f"rtmp://{stream_config['rtmp_host']}/{stream_config['stream_path']}/{stream_key}"
    stream_url = f"http://{stream_config['rtmp_host']}:{stream_config['stream_port']}/{stream_config['stream_path']}/{stream_key}"

    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor()

        # Get current user for authorization
        current_user_id = get_jwt_identity()

        # Authorization: Verify user has access to this team
        if not _verify_team_access(cursor, current_user_id, team_id):
            cursor.close()
            conn.close()
            return jsonify(
                {
                    "error": "Access denied. You do not have permission to create a stream for this team."
                }
            ), 403

        cursor.execute(
            """
            INSERT INTO live_streams (match_id, team_id, stream_name, stream_url, rtmp_url, status)
            VALUES (%s, %s, %s, %s, %s, %s)
        """,
            (match_id, team_id, stream_name, stream_url, rtmp_url, "inactive"),
        )

        stream_id = cursor.lastrowid
        conn.commit()

        return jsonify(
            {
                "success": True,
                "stream_id": stream_id,
                "stream_name": stream_name,
                "rtmp_url": rtmp_url,
                "stream_url": stream_url,
                "stream_key": stream_key,
                "message": "Stream created! Use RTMP URL in BlackMagic",
            }
        ), 200
    except Exception as e:
        print(f"Error creating stream: {e}")
        if conn:
            conn.rollback()
        return jsonify({"error": "Failed to create stream"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


@live_stream_bp.route("/create-session", methods=["POST"])
@jwt_required()
def create_analytics_session():
    """Create a unified analytics session (Hardware or External)"""
    data = request.get_json()
    user_id = get_jwt_identity()

    source_type = data.get("source_type")
    session_name = data.get(
        "session_name", f"Session_{datetime.now().strftime('%H%M%S')}"
    )
    external_url = data.get("external_url")

    stream_key = str(uuid.uuid4())[:8]
    rtmp_url = f"rtmp://ai.rwandatalent.com/live/{stream_key}"

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO analytics_sessions (user_id, source_type, session_name, external_url, ingest_url, stream_key, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
            (
                user_id,
                source_type,
                session_name,
                external_url,
                rtmp_url if source_type == "hardware" else external_url,
                stream_key,
                "In-Progress",
            ),
        )

        conn.commit()
        return jsonify(
            {
                "success": True,
                "rtmp_url": rtmp_url,
                "stream_key": stream_key,
                "message": "Session initialized",
            }
        ), 201
    except Exception as e:
        print(f"Error creating session: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@live_stream_bp.route("/sessions", methods=["GET"])
@jwt_required()
def list_analytics_sessions():
    """List active sessions for user"""
    user_id = get_jwt_identity()
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM analytics_sessions WHERE user_id = %s ORDER BY created_at DESC LIMIT 10",
            (user_id,),
        )
        sessions = cursor.fetchall()
        return jsonify({"sessions": sessions}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@live_stream_bp.route("/camera-chunk", methods=["POST"])
@jwt_required()
def receive_camera_chunk():
    """Receive a video chunk from device camera streaming.

    Chunks are stored temporarily and auto-deleted after processing
    to keep database and disk usage minimal.
    """
    import tempfile
    import shutil

    session_id = request.form.get("session_id")
    chunk = request.files.get("chunk")

    if not session_id or not chunk:
        return jsonify({"error": "Missing session_id or chunk"}), 400

    try:
        # Use system temp directory - auto-cleaned by OS
        temp_base = tempfile.gettempdir()
        upload_dir = os.path.join(temp_base, "camera_streams", str(session_id))
        os.makedirs(upload_dir, exist_ok=True)

        # Save chunk temporarily
        chunk_filename = f"chunk_{datetime.now().strftime('%H%M%S_%f')}.webm"
        chunk_path = os.path.join(upload_dir, chunk_filename)
        chunk.save(chunk_path)

        # Auto-cleanup: delete chunks older than 60 seconds in this session
        import time

        now = time.time()
        for f in os.listdir(upload_dir):
            fpath = os.path.join(upload_dir, f)
            if os.path.isfile(fpath) and (now - os.path.getmtime(fpath)) > 60:
                os.remove(fpath)

        return jsonify({"success": True, "chunk": chunk_filename}), 200
    except Exception as e:
        print(f"Error saving camera chunk: {e}")
        return jsonify({"error": "Failed to save chunk"}), 500


@live_stream_bp.route("/camera-stop", methods=["POST"])
@jwt_required()
def stop_camera_stream():
    """Stop a camera stream and clean up all temporary files."""
    import tempfile
    import shutil

    data = request.get_json()
    session_id = data.get("session_id") if data else None

    try:
        # Clean up temp chunks for this session
        if session_id:
            temp_base = tempfile.gettempdir()
            session_dir = os.path.join(temp_base, "camera_streams", str(session_id))
            if os.path.exists(session_dir):
                shutil.rmtree(session_dir)

        # Update session status in DB
        if session_id:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE analytics_sessions SET status = 'Completed' WHERE id = %s",
                    (session_id,),
                )
                conn.commit()
                cursor.close()
                conn.close()

        return jsonify(
            {"success": True, "message": "Camera stream stopped, temp files cleaned"}
        ), 200
    except Exception as e:
        print(f"Error stopping camera: {e}")
        return jsonify({"error": "Failed to stop camera stream"}), 500


# Track processing threads and their status
_processing_status = {}


@live_stream_bp.route("/process-video", methods=["POST"])
@jwt_required()
def process_video():
    """Start video processing for a YouTube URL or uploaded video.
    Runs in a background thread so the UI doesn't block.
    """
    import threading

    data = request.get_json()
    video_url = data.get("video_url")
    match_id = data.get("match_id", 1)
    team_id = data.get("team_id", 1)
    session_name = data.get("session_name", "Video Analysis")
    session_id = data.get("session_id")  # Use existing session if provided

    if not video_url:
        return jsonify({"error": "video_url is required"}), 400

    # Get the JWT token from the request header
    auth_header = request.headers.get("Authorization", "")
    token = (
        auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else ""
    )

    user_id = get_jwt_identity()

    # Create or update session in DB
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if session_id:
            # Update existing session
            cursor.execute(
                "UPDATE analytics_sessions SET status = 'Processing' WHERE id = %s",
                (session_id,),
            )
        else:
            # Create new session
            stream_key = str(uuid.uuid4())[:8]
            cursor.execute(
                """INSERT INTO analytics_sessions
                   (user_id, source_type, session_name, external_url, ingest_url, stream_key, status)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (
                    user_id,
                    "external_url",
                    session_name,
                    video_url,
                    video_url,
                    stream_key,
                    "Processing",
                ),
            )
            session_id = cursor.lastrowid

        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error creating session: {e}")
        return jsonify({"error": "Failed to create session"}), 500

    # Capture values before starting thread (Flask request context is lost in threads)
    backend_url = request.host_url.rstrip("/")
    # Use 127.0.0.1 for internal API calls
    if "localhost" in backend_url or "0.0.0.0" in backend_url:
        backend_url = backend_url.replace("localhost", "127.0.0.1").replace(
            "0.0.0.0", "127.0.0.1"
        )

    # Initialize status tracking
    _processing_status[session_id] = {
        "status": "starting",
        "progress": 0,
        "message": "Initializing...",
        "players_found": 0,
    }

    # Run video processing in background thread
    def run_processing():
        try:
            ai_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "..", "ai"
            )
            if ai_path not in sys.path:
                sys.path.insert(0, ai_path)
            from video_processor import process_youtube_url

            print(f"[VIDEO PROCESSOR] Starting download and analysis for: {video_url}")
            print(f"[VIDEO PROCESSOR] Backend URL: {backend_url}")
            print(f"[VIDEO PROCESSOR] Session ID: {session_id}")

            _processing_status[session_id]["status"] = "downloading"
            _processing_status[session_id]["message"] = "Downloading video..."

            success = process_youtube_url(
                url=video_url,
                backend_url=backend_url,
                token=token,
                match_id=match_id,
                team_id=team_id,
            )

            if success:
                print(f"[VIDEO PROCESSOR] Processing complete!")
                _processing_status[session_id]["status"] = "completed"
                _processing_status[session_id]["message"] = "Done!"
            else:
                print(f"[VIDEO PROCESSOR] Processing returned False")
                _processing_status[session_id]["status"] = "error"
                _processing_status[session_id]["message"] = "Failed - check server logs"

            # Mark session as completed
            conn2 = get_db_connection()
            if conn2:
                c2 = conn2.cursor()
                c2.execute(
                    "UPDATE analytics_sessions SET status = 'Completed' WHERE id = %s",
                    (session_id,),
                )
                conn2.commit()
                c2.close()
                conn2.close()
        except Exception as e:
            import traceback

            print(f"[VIDEO PROCESSOR] ERROR: {e}")
            traceback.print_exc()
            _processing_status[session_id]["status"] = "error"
            _processing_status[session_id]["message"] = str(e)
            try:
                conn3 = get_db_connection()
                if conn3:
                    c3 = conn3.cursor()
                    c3.execute(
                        "UPDATE analytics_sessions SET status = 'Completed' WHERE id = %s",
                        (session_id,),
                    )
                    conn3.commit()
                    c3.close()
                    conn3.close()
            except:
                pass

    thread = threading.Thread(target=run_processing, daemon=True)
    thread.start()

    return jsonify(
        {
            "success": True,
            "session_id": session_id,
            "message": f"Video processing started for: {video_url}",
        }
    ), 200


@live_stream_bp.route("/process-status/<int:session_id>", methods=["GET"])
@jwt_required()
def get_process_status(session_id):
    """Get the status of a video processing job"""
    status = _processing_status.get(
        session_id,
        {
            "status": "unknown",
            "progress": 0,
            "message": "No status available",
            "players_found": 0,
        },
    )
    return jsonify(status), 200


@live_stream_bp.route("/start/<int:stream_id>", methods=["POST"])
@jwt_required()
def start_stream(stream_id):
    """Start a live stream"""
    conn = None
    cursor = None
    try:
        current_user_id = get_jwt_identity()

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor()

        # Get stream's team_id for authorization
        stream_team_id = _get_stream_team_id(cursor, stream_id)
        if stream_team_id is None:
            return jsonify({"error": "Stream not found"}), 404

        # Authorization: Verify user has access to this team
        if not _verify_team_access(cursor, current_user_id, stream_team_id):
            return jsonify(
                {
                    "error": "Access denied. You do not have permission to manage this stream."
                }
            ), 403

        cursor.execute(
            """
            UPDATE live_streams 
            SET status = 'active', started_at = NOW()
            WHERE id = %s
        """,
            (stream_id,),
        )

        conn.commit()

        return jsonify({"success": True, "message": "Stream started!"}), 200
    except Exception as e:
        print(f"Error starting stream: {e}")
        if conn:
            conn.rollback()
        return jsonify({"error": "Failed to start stream"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


@live_stream_bp.route("/stop/<int:stream_id>", methods=["POST"])
@jwt_required()
def stop_stream(stream_id):
    """Stop a live stream"""
    conn = None
    cursor = None
    try:
        current_user_id = get_jwt_identity()

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor()

        # Get stream's team_id for authorization
        stream_team_id = _get_stream_team_id(cursor, stream_id)
        if stream_team_id is None:
            return jsonify({"error": "Stream not found"}), 404

        # Authorization: Verify user has access to this team
        if not _verify_team_access(cursor, current_user_id, stream_team_id):
            return jsonify(
                {
                    "error": "Access denied. You do not have permission to manage this stream."
                }
            ), 403

        cursor.execute(
            """
            UPDATE live_streams 
            SET status = 'inactive', ended_at = NOW()
            WHERE id = %s
        """,
            (stream_id,),
        )

        conn.commit()

        return jsonify({"success": True, "message": "Stream stopped!"}), 200
    except Exception as e:
        print(f"Error stopping stream: {e}")
        if conn:
            conn.rollback()
        return jsonify({"error": "Failed to stop stream"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


@live_stream_bp.route("/list", methods=["GET"])
@jwt_required()
def list_streams():
    """List streams - superadmin/ferwafa see all, others see only their team's streams"""
    current_user_id = get_jwt_identity()
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor(dictionary=True)

        # Get current user's role and entity_id for authorization
        cursor.execute(
            "SELECT role, entity_id FROM users WHERE id = %s", (current_user_id,)
        )
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "User not found"}), 404

        # Superadmin and ferwafa can see all streams
        if user["role"] in ["superadmin", "ferwafa"]:
            cursor.execute("SELECT * FROM live_streams ORDER BY created_at DESC")
        else:
            # Other users can only see their team's streams
            entity_id = user["entity_id"]
            if entity_id:
                cursor.execute(
                    "SELECT * FROM live_streams WHERE team_id = %s ORDER BY created_at DESC",
                    (entity_id,),
                )
            else:
                # User without entity_id sees nothing
                cursor.execute("SELECT * FROM live_streams WHERE 1=0")

        streams = cursor.fetchall()

        return jsonify({"streams": streams}), 200
    except Exception as e:
        print(f"Error listing streams: {e}")
        return jsonify({"error": "Failed to retrieve streams"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


# ML Training Routes


def _verify_ml_training_access(cursor, user_id, training_id=None):
    """Verify user has access to ML training.

    Returns True if user can manage ML training (superadmin/ferwafa),
    or if training_id provided, check if user owns that training.
    """
    cursor.execute("SELECT role, entity_id FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()

    if not user:
        return False

    # Handle both tuple and dict return types
    if isinstance(user, dict):
        role = user.get("role")
        entity_id = user.get("entity_id")
    else:
        try:
            role, entity_id = user
        except (TypeError, ValueError):
            return False

    # Superadmin and ferwafa can manage all training
    if role in ["superadmin", "ferwafa"]:
        return True

    # If training_id provided, check ownership
    if training_id:
        cursor.execute("SELECT team_id FROM ml_training WHERE id = %s", (training_id,))
        result = cursor.fetchone()
        if result:
            training_team_id = (
                result[0] if isinstance(result, tuple) else result.get("team_id")
            )
            if (
                training_team_id
                and entity_id
                and int(training_team_id) == int(entity_id)
            ):
                return True

    return False


@live_stream_bp.route("/training/create", methods=["POST"])
@jwt_required()
def create_ml_training():
    """Create ML training job"""
    current_user_id = get_jwt_identity()
    data = request.get_json()

    # Validate required fields
    if not data.get("name"):
        return jsonify({"error": "Training name is required"}), 400

    name = data.get("name")
    description = data.get("description", "")
    model_type = data.get("model_type", "yolov8")
    team_id = data.get("team_id")  # Optional team_id for team-specific training

    # Validate model_type against allowed types
    if model_type not in ALLOWED_MODEL_TYPES:
        return jsonify(
            {
                "error": "Invalid model_type. Must be one of: "
                + ", ".join(sorted(ALLOWED_MODEL_TYPES))
            }
        ), 400

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor()

        # Authorization: Verify user has access to the team (if team_id provided)
        if team_id:
            try:
                team_id = int(team_id)
            except (ValueError, TypeError):
                return jsonify({"error": "Invalid team_id"}), 400

            if not _verify_team_access(cursor, current_user_id, team_id):
                return jsonify(
                    {
                        "error": "Access denied. You do not have permission to create training for this team."
                    }
                ), 403
        else:
            # No team_id - check if user can create global training (superadmin only)
            cursor.execute("SELECT role FROM users WHERE id = %s", (current_user_id,))
            user = cursor.fetchone()
            user_role = user[0] if user else None
            if user_role != "superadmin":
                return jsonify(
                    {
                        "error": "Only superadmin can create global training jobs without a team."
                    }
                ), 403

        cursor.execute(
            """
            INSERT INTO ml_training (name, description, model_type, status, team_id)
            VALUES (%s, %s, %s, %s, %s)
        """,
            (name, description, model_type, "pending", team_id),
        )

        training_id = cursor.lastrowid
        conn.commit()

        return jsonify(
            {
                "success": True,
                "training_id": training_id,
                "message": "ML training job created!",
            }
        ), 200
    except Exception as e:
        print(f"Error creating ML training: {e}")
        if conn:
            conn.rollback()
        return jsonify({"error": "Failed to create training job"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


@live_stream_bp.route("/training/start/<int:training_id>", methods=["POST"])
@jwt_required()
def start_ml_training(training_id):
    """Start ML training"""
    current_user_id = get_jwt_identity()
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor()

        # Authorization: Verify user has access to this training job
        if not _verify_ml_training_access(cursor, current_user_id, training_id):
            return jsonify(
                {
                    "error": "Access denied. You do not have permission to manage this training job."
                }
            ), 403

        # In a real system, this would trigger actual training
        cursor.execute(
            """
            UPDATE ml_training 
            SET status = 'training'
            WHERE id = %s
        """,
            (training_id,),
        )

        conn.commit()

        return jsonify({"success": True, "message": "ML training started!"}), 200
    except Exception as e:
        print(f"Error starting ML training: {e}")
        if conn:
            conn.rollback()
        return jsonify({"error": "Failed to start training"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


@live_stream_bp.route("/training/list", methods=["GET"])
@jwt_required()
def list_ml_training():
    """List ML training jobs - superadmin/ferwafa see all, others see only their team's jobs"""
    current_user_id = get_jwt_identity()
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor(dictionary=True)

        # Get user's role and entity_id
        cursor.execute(
            "SELECT role, entity_id FROM users WHERE id = %s", (current_user_id,)
        )
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "User not found"}), 404

        # Superadmin and ferwafa can see all training jobs
        if user["role"] in ["superadmin", "ferwafa"]:
            cursor.execute("SELECT * FROM ml_training ORDER BY created_at DESC")
        else:
            # Other users can only see their team's training jobs
            entity_id = user.get("entity_id")
            if entity_id:
                cursor.execute(
                    "SELECT * FROM ml_training WHERE team_id = %s OR team_id IS NULL ORDER BY created_at DESC",
                    (entity_id,),
                )
            else:
                # User without entity_id sees only global (no team) jobs
                cursor.execute(
                    "SELECT * FROM ml_training WHERE team_id IS NULL ORDER BY created_at DESC"
                )

        trainings = cursor.fetchall()

        return jsonify({"trainings": trainings}), 200
    except Exception as e:
        print(f"Error listing ML training: {e}")
        return jsonify({"error": "Failed to retrieve training jobs"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


@live_stream_bp.route("/training/<int:training_id>", methods=["GET"])
@jwt_required()
def get_training_status(training_id):
    """Get training status"""
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM ml_training WHERE id = %s", (training_id,))
        training = cursor.fetchone()

        if not training:
            return jsonify({"error": "Training not found"}), 404

        return jsonify(training), 200
    except Exception as e:
        print(f"Error getting training status: {e}")
        return jsonify({"error": "Failed to get training status"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
