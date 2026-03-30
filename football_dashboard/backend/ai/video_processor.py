"""
Video Processor - Download and analyze YouTube/local videos
Processes ended matches to auto-detect and track players
"""

import cv2
import os
import sys
import time
import json
import tempfile
import requests
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from detection import YOLODetector
from tracking import PlayerTracker
from metrics import PlayerMetrics
from event import EventDetector


def download_youtube_video(url, output_dir=None):
    """Download YouTube video using yt-dlp and return local file path"""
    import yt_dlp

    if output_dir is None:
        output_dir = tempfile.gettempdir()

    os.makedirs(output_dir, exist_ok=True)
    output_template = os.path.join(output_dir, "match_%(id)s.%(ext)s")

    ydl_opts = {
        "format": "best[height<=480]/best",
        "outtmpl": output_template,
        "quiet": False,
        "no_warnings": False,
        "merge_output_format": "mp4",
    }

    print(f"[DOWNLOAD] Fetching video from: {url}")
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            title = info.get("title", "Unknown")
            duration = info.get("duration", 0)

            # yt-dlp might change extension
            if not os.path.exists(filename):
                # Try with mp4 extension
                base = os.path.splitext(filename)[0]
                for ext in [".mp4", ".mkv", ".webm"]:
                    if os.path.exists(base + ext):
                        filename = base + ext
                        break

            print(f"[DOWNLOAD] Complete: {title} ({duration}s) -> {filename}")
            return filename, title, duration
    except Exception as e:
        import traceback

        print(f"[DOWNLOAD] ERROR: {e}")
        traceback.print_exc()
        return None, None, 0


def process_video(
    video_path,
    backend_url,
    token,
    match_id=1,
    team_id=1,
    send_interval_seconds=30,
    max_duration_minutes=None,
):
    """
    Process a video file: detect players, track them, calculate stats, send to backend.

    Args:
        video_path: Path to video file
        backend_url: Backend API URL
        token: JWT auth token
        match_id: Match ID for stats
        team_id: Team ID for stats
        send_interval_seconds: How often to send stats to backend
        max_duration_minutes: Max video length to process (None = full video)
    """
    print(f"\n{'=' * 50}")
    print(f"Processing video: {video_path}")
    print(f"{'=' * 50}")

    # Open video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"ERROR: Could not open video: {video_path}")
        return False

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration_sec = total_frames / fps if fps > 0 else 0

    print(
        f"Video: {width}x{height} @ {fps:.1f} FPS, {total_frames} frames, {duration_sec:.0f}s"
    )

    # Initialize AI components
    detector = YOLODetector(confidence=0.4)
    tracker = PlayerTracker(max_distance=150.0, max_frames_to_skip=30)
    metrics = PlayerMetrics(pixels_per_meter=50.0)
    event_detector = EventDetector(frame_width=width, frame_height=height)

    # Processing state
    frame_count = 0
    last_send_time = 0
    max_frames = (
        int(max_duration_minutes * 60 * fps) if max_duration_minutes else total_frames
    )
    frame_skip = max(1, int(fps / 10))  # Process ~10 frames per second for speed

    start_time = time.time()

    print(f"\nStarting processing (every {frame_skip} frames)...")
    print("-" * 50)

    try:
        while frame_count < max_frames:
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1

            # Skip frames for speed
            if frame_count % frame_skip != 0:
                continue

            # Current video time in seconds
            video_time = frame_count / fps

            # Step 1: Detect players
            detections = detector.detect(frame)

            # Step 2: Track players
            tracked_objects = tracker.update(detections, frame_count)

            # Step 3: Calculate metrics
            player_metrics = metrics.update(
                tracked_objects, video_time, fps / frame_skip
            )

            # Step 4: Detect events
            events = event_detector.detect_events(tracked_objects, video_time)

            # Print progress every 50 processed frames
            if (frame_count // frame_skip) % 50 == 0:
                progress = (frame_count / total_frames) * 100
                elapsed = time.time() - start_time
                n_tracked = len(tracked_objects)
                n_players = len(metrics.player_data)
                print(
                    f"[{progress:.0f}%] Frame {frame_count}/{total_frames} | "
                    f"Time: {video_time / 60:.1f}min | "
                    f"Detected: {n_tracked} | "
                    f"Total tracked: {n_players}"
                )

            # Step 5: Send stats to backend at intervals
            if video_time - last_send_time >= send_interval_seconds:
                _send_stats(
                    backend_url,
                    token,
                    match_id,
                    team_id,
                    metrics,
                    event_detector,
                    video_time,
                )
                last_send_time = video_time

    except KeyboardInterrupt:
        print("\nProcessing interrupted by user")
    finally:
        cap.release()

    # Send final stats
    _send_stats(
        backend_url,
        token,
        match_id,
        team_id,
        metrics,
        event_detector,
        frame_count / fps,
        final=True,
    )

    # Cleanup: delete downloaded video
    if os.path.exists(video_path):
        try:
            os.remove(video_path)
            print(f"\nCleaned up temp video: {video_path}")
        except:
            pass

    elapsed_total = time.time() - start_time
    print(f"\n{'=' * 50}")
    print(f"Processing complete in {elapsed_total:.0f}s")
    print(f"Players tracked: {len(metrics.player_data)}")
    print(f"{'=' * 50}")
    return True


def _send_stats(
    backend_url,
    token,
    match_id,
    team_id,
    metrics,
    event_detector,
    video_time,
    final=False,
):
    """Send player stats to backend API"""
    player_summaries = metrics.get_all_summaries()
    match_stats = metrics.get_match_stats()
    events = event_detector.get_recent_events(300)

    if not player_summaries:
        print("  No player data to send yet...")
        return

    data = {
        "match_id": match_id,
        "team_id": team_id,
        "timestamp": datetime.now().isoformat(),
        "elapsed_minutes": round(video_time / 60.0, 1),
        "players": player_summaries,
        "match_stats": match_stats,
        "events": events,
    }

    suffix = " (FINAL)" if final else ""
    print(
        f"\n  Sending stats{suffix}: {len(player_summaries)} players, "
        f"{match_stats.get('total_distance', 0):.0f}m total distance"
    )

    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        # Use test-stats endpoint which doesn't require team/match validation
        resp = requests.post(
            f"{backend_url}/api/ai/test-stats",
            json=data,
            headers=headers,
            timeout=15,
        )
        if resp.status_code == 200:
            print(f"  Stats sent successfully!")
        else:
            print(f"  Backend error: {resp.status_code} - {resp.text[:100]}")
    except Exception as e:
        print(f"  Send failed: {e}")


def process_youtube_url(url, backend_url, token, match_id=1, team_id=1):
    """Download YouTube video and process it"""
    # Download
    video_path, title, duration = download_youtube_video(url)

    if video_path is None or not os.path.exists(video_path):
        print(f"[ERROR] Download failed for: {url}")
        return False

    # Process
    return process_video(
        video_path=video_path,
        backend_url=backend_url,
        token=token,
        match_id=match_id,
        team_id=team_id,
        send_interval_seconds=30,
        max_duration_minutes=10,  # Process max 10 minutes for testing
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Process football video for player tracking"
    )
    parser.add_argument("source", help="YouTube URL or path to local video file")
    parser.add_argument(
        "--backend", default="http://localhost:5000", help="Backend URL"
    )
    parser.add_argument("--token", required=True, help="JWT auth token")
    parser.add_argument("--match", type=int, default=1, help="Match ID")
    parser.add_argument("--team", type=int, default=1, help="Team ID")
    parser.add_argument(
        "--max-minutes", type=float, default=10, help="Max minutes to process"
    )

    args = parser.parse_args()

    if args.source.startswith("http"):
        process_youtube_url(
            args.source, args.backend, args.token, args.match, args.team
        )
    else:
        process_video(
            args.source,
            args.backend,
            args.token,
            args.match,
            args.team,
            max_duration_minutes=args.max_minutes,
        )
