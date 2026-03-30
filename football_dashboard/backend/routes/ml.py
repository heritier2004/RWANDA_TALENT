"""
ML Training API Routes
Handles the creation and management of machine learning analysis jobs
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import json
import uuid

ml_bp = Blueprint('ml', __name__)

# Simulated in-memory database for ML Jobs (in production, use MySQL)
# This allows the user to see "Changes" immediately without schema migrations
ml_jobs = []

@ml_bp.route('/train', methods=['POST'])
@jwt_required()
def create_training_job():
    """Create a new ML analysis job"""
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        
        job_type = data.get('type', 'Performance Analysis')
        video_source = data.get('source', '')
        
        # Generate standardized credentials for the user to send video
        job_id = str(uuid.uuid4())[:8]
        upload_endpoint = f"https://ai.rwandatalent.com/upload/{job_id}"
        stream_ingest = f"rtmp://ai.rwandatalent.com/ingest/{job_id}"
        
        job = {
            'id': job_id,
            'user_id': user_id,
            'type': job_type,
            'status': 'Processing',
            'progress': 10,
            'source': video_source,
            'upload_endpoint': upload_endpoint,
            'stream_ingest': stream_ingest,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        ml_jobs.append(job)
        
        return jsonify({
            'success': True,
            'message': 'ML Training Job started successfully',
            'job': job
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ml_bp.route('/jobs', methods=['GET'])
@jwt_required()
def get_ml_jobs():
    """Get all ML jobs for the current user"""
    user_id = get_jwt_identity()
    user_jobs = [j for j in ml_jobs if j['user_id'] == user_id]
    
    # Simulate progress updates for "Processing" jobs
    for j in user_jobs:
        if j['status'] == 'Processing' and j['progress'] < 100:
            j['progress'] += 15
            if j['progress'] >= 100:
                j['status'] = 'Completed'
                j['progress'] = 100
                
    return jsonify(user_jobs), 200

@ml_bp.route('/jobs/<job_id>', methods=['DELETE'])
@jwt_required()
def delete_job(job_id):
    """Delete a job record"""
    global ml_jobs
    ml_jobs = [j for j in ml_jobs if j['id'] != job_id]
    return jsonify({'success': True}), 200
