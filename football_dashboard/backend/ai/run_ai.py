"""
AI Runner Module - Main Pipeline Controller
Coordinates detection, tracking, metrics, and event detection
Sends data to backend every 15 minutes
"""

import cv2
import time
import json
import os
import requests
import threading
from typing import Optional, Dict, List
from datetime import datetime

# Import AI modules
from camera import VideoCapture, get_video_source
from detection import YOLODetector
from tracking import PlayerTracker
from metrics import PlayerMetrics
from event import EventDetector


class AIRunner:
    """Main AI processing pipeline"""
    
    def __init__(self, 
                 video_source: str = "0",
                 backend_url: str = "http://localhost:5000",
                 analysis_interval: int = 900,  # 15 minutes in seconds
                 match_id: int = 1,
                 team_id: int = 1):
        """
        Initialize AI Runner
        
        Args:
            video_source: Video source (webcam index, file path, or stream URL)
            backend_url: URL of the backend API
            analysis_interval: Seconds between sending data to backend
            match_id: Current match ID
            team_id: Current team ID
        """
        self.video_source = video_source
        self.backend_url = backend_url
        self.analysis_interval = analysis_interval
        self.match_id = match_id
        self.team_id = team_id
        
        # Initialize components
        self.camera = None
        self.detector = YOLODetector()
        self.tracker = PlayerTracker()
        self.metrics = PlayerMetrics()
        self.event_detector = EventDetector()
        
        # State
        self.is_running = False
        self.start_time = None
        self.last_analysis_time = None
        self.frame_count = 0
        
        # Current data for backend
        self.current_stats = {}
        
    def start(self):
        """Start the AI processing pipeline"""
        print("=" * 50)
        print("Starting AI Player Tracking System")
        print("=" * 50)
        
        # Open video source
        self.camera = VideoCapture(self.video_source)
        if not self.camera.open():
            print("Error: Could not open video source")
            return False
        
        self.is_running = True
        self.start_time = time.time()
        self.last_analysis_time = self.start_time
        
        print(f"Video source: {self.video_source}")
        print(f"Backend URL: {self.backend_url}")
        print(f"Analysis interval: {self.analysis_interval} seconds")
        print("-" * 50)
        
        # Start processing loop
        self._process_loop()
        
        return True
    
    def _process_loop(self):
        """Main processing loop"""
        fps = self.camera.fps if self.camera.fps > 0 else 30.0
        print(f"Processing at {fps} FPS")
        
        while self.is_running:
            # Read frame
            ret, frame = self.camera.read()
            
            if not ret:
                print("Warning: Could not read frame")
                # For video files, loop back
                if not self.video_source.isdigit():
                    self.camera.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                else:
                    break
            
            self.frame_count += 1
            
            # Get current time
            current_time = self.camera.get_timestamp() / 1000.0  # Convert to seconds
            if current_time <= 0:
                current_time = time.time() - self.start_time
            
            # Step 1: Detect players
            detections = self.detector.detect(frame)
            
            # Step 2: Track players
            tracked_objects = self.tracker.update(detections, self.frame_count)
            
            # Step 3: Calculate metrics
            player_metrics = self.metrics.update(tracked_objects, current_time, fps)
            self.current_stats = player_metrics
            
            # Step 4: Detect events
            events = self.event_detector.detect_events(tracked_objects, current_time)
            
            # Print progress every 30 frames
            if self.frame_count % 30 == 0:
                elapsed = current_time
                minutes = elapsed / 60.0
                print(f"Frame {self.frame_count} | Time: {minutes:.1f} min | Players: {len(tracked_objects)}")
            
            # Step 5: Check if it's time to send data to backend
            time_since_last = current_time - self.last_analysis_time
            if time_since_last >= self.analysis_interval:
                self._send_stats_to_backend()
                self.last_analysis_time = current_time
            
            # Small delay to prevent CPU overload
            time.sleep(0.01)
        
        # Cleanup
        self._cleanup()
    
    def _send_stats_to_backend(self):
        """Send statistics to backend API"""
        print("\n" + "=" * 50)
        print(f"Sending stats to backend at {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 50)
        
        # Get all player summaries
        player_summaries = self.metrics.get_all_summaries()
        
        # Get match stats
        match_stats = self.metrics.get_match_stats()
        
        # Get recent events
        recent_events = self.event_detector.get_recent_events(60)
        
        # Prepare data
        data = {
            'match_id': self.match_id,
            'team_id': self.team_id,
            'timestamp': datetime.now().isoformat(),
            'elapsed_minutes': match_stats.get('match_duration_minutes', 0),
            'players': player_summaries,
            'match_stats': match_stats,
            'events': recent_events
        }
        
        print(f"Players tracked: {len(player_summaries)}")
        print(f"Match duration: {match_stats.get('match_duration_minutes', 0):.1f} minutes")
        
        # Send to backend
        try:
            response = requests.post(
                f"{self.backend_url}/api/ai/stats",
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                print("✓ Stats sent successfully!")
                print(f"  Response: {response.json()}")
            else:
                print(f"✗ Error sending stats: {response.status_code}")
                print(f"  Response: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("✗ Could not connect to backend")
            print(f"  Make sure Flask is running at {self.backend_url}")
        except Exception as e:
            print(f"✗ Error: {e}")
        
        print("-" * 50)
    
    def _cleanup(self):
        """Cleanup resources"""
        print("\nCleaning up...")
        
        if self.camera:
            self.camera.release()
        
        # Delete video file if it was a file
        if self.video_source.endswith(('.mp4', '.avi', '.mov')):
            if os.path.exists(self.video_source):
                try:
                    os.remove(self.video_source)
                    print(f"Deleted video file: {self.video_source}")
                except:
                    pass
        
        print("AI Runner stopped.")
    
    def stop(self):
        """Stop the AI processing"""
        self.is_running = False
    
    def get_current_stats(self) -> dict:
        """Get current statistics"""
        return {
            'players': self.metrics.get_all_summaries(),
            'match_stats': self.metrics.get_match_stats(),
            'top_players': self.metrics.get_top_players(5),
            'events': self.event_detector.get_event_summary()
        }


def run_ai_pipeline(video_source: str = "0",
                   backend_url: str = "http://localhost:5000",
                   match_id: int = 1,
                   team_id: int = 1):
    """
    Run the AI pipeline
    
    Args:
        video_source: Video source (0 for webcam, path to video file, or stream URL)
        backend_url: Backend API URL
        match_id: Match ID
        team_id: Team ID
    """
    runner = AIRunner(
        video_source=video_source,
        backend_url=backend_url,
        match_id=match_id,
        team_id=team_id
    )
    
    try:
        runner.start()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        runner.stop()
    except Exception as e:
        print(f"Error: {e}")
        runner.stop()


# Main entry point
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Football Player Tracking AI')
    parser.add_argument('--source', '-s', type=str, default='0',
                       help='Video source: 0 (webcam), path to video file, or stream URL')
    parser.add_argument('--backend', '-b', type=str, default='http://localhost:5000',
                       help='Backend API URL')
    parser.add_argument('--match', '-m', type=int, default=1,
                       help='Match ID')
    parser.add_argument('--team', '-t', type=int, default=1,
                       help='Team ID')
    
    args = parser.parse_args()
    
    print("Football Player Tracking AI System")
    print("=" * 50)
    print(f"Video Source: {args.source}")
    print(f"Backend URL: {args.backend}")
    print(f"Match ID: {args.match}")
    print(f"Team ID: {args.team}")
    print("=" * 50)
    
    run_ai_pipeline(
        video_source=args.source,
        backend_url=args.backend,
        match_id=args.match,
        team_id=args.team
    )
