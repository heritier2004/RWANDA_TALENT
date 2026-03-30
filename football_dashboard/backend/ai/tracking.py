"""
Tracking Module - ByteTracker Integration
Uses ByteTrack algorithm for robust multi-object tracking
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
import math

# Try to import ByteTracker
try:
    from bytetrack import ByteTracker as BT

    BYTETRACK_AVAILABLE = True
except ImportError:
    BYTETRACK_AVAILABLE = False
    print("ByteTracker not installed. Using simple centroid tracking.")


class PlayerTracker:
    """Track players across frames using ByteTracker algorithm"""

    def __init__(self, max_distance: float = 100.0, max_frames_to_skip: int = 30):
        """
        Initialize tracker

        Args:
            max_distance: Maximum distance to match detections (for fallback)
            max_frames_to_skip: Frames to keep track of lost players (for fallback)
        """
        self.max_distance = max_distance
        self.max_frames_to_skip = max_frames_to_skip

        # Try to use ByteTracker if available
        if BYTETRACK_AVAILABLE:
            self.use_bytetrack = True
            self.tracker = BT(
                track_thresh=0.5, track_buffer=30, match_thresh=0.8, frame_rate=30
            )
            print("Using ByteTracker for player tracking")
        else:
            self.use_bytetrack = False
            # Fallback: simple centroid tracking
            self.tracks = {}
            self.next_track_id = 1
            self.prev_positions = {}
            print("Using simple centroid tracking (fallback)")

    def update(self, detections: List[dict], frame_number: int = 0) -> List[dict]:
        """
        Update tracks with new detections

        Args:
            detections: List of detections from YOLO
            frame_number: Current frame number

        Returns:
            List of tracked objects with IDs
        """
        if self.use_bytetrack:
            return self._update_bytetrack(detections, frame_number)
        else:
            return self._update_centroid(detections, frame_number)

    def _update_bytetrack(
        self, detections: List[dict], frame_number: int
    ) -> List[dict]:
        """Update using ByteTracker algorithm"""
        if not detections:
            # Update tracker with no detections
            tracked_objects = self.tracker.update(np.empty((0, 6)), frame_number)
            return []

        # Convert detections to BYTETracker format [x1, y1, x2, y2, score, class]
        det_array = np.zeros((len(detections), 6))
        for i, det in enumerate(detections):
            bbox = det["bbox"]  # [x1, y1, x2, y2]
            det_array[i] = [
                bbox[0],
                bbox[1],
                bbox[2],
                bbox[3],
                det["confidence"],
                det.get("class", 0),
            ]

        # Update tracker
        tracked_objects = self.tracker.update(det_array, frame_number)

        # Convert results to our format
        results = []
        for obj in tracked_objects:
            results.append(
                {
                    "track_id": obj.track_id,
                    "bbox": [obj.x1, obj.y1, obj.x2, obj.y2],
                    "confidence": obj.score,
                    "class_id": int(obj.class_id),
                    "frame_id": frame_number,
                }
            )

        return results

    def _update_centroid(self, detections: List[dict], frame_number: int) -> List[dict]:
        """Fallback: simple centroid-based tracking"""
        if not detections:
            for track_id in self.tracks:
                self.tracks[track_id]["frames_missing"] += 1
            return []

        detection_centroids = [(i, det["centroid"]) for i, det in enumerate(detections)]
        matched_tracks = set()
        matched_detections = set()

        for det_idx, det_centroid in detection_centroids:
            if det_idx in matched_detections:
                continue

            min_dist = float("inf")
            best_track_id = None

            for track_id, track_data in self.tracks.items():
                if track_id in matched_tracks:
                    continue
                if track_data["frames_missing"] > self.max_frames_to_skip:
                    continue

                track_centroid = track_data["centroid"]
                dist = self._calculate_distance(det_centroid, track_centroid)

                if dist < min_dist and dist < self.max_distance:
                    min_dist = dist
                    best_track_id = track_id

            if best_track_id is not None:
                self.tracks[best_track_id]["centroid"] = det_centroid
                self.tracks[best_track_id]["frames_missing"] = 0
                matched_tracks.add(best_track_id)
                matched_detections.add(det_idx)

                # Calculate distance moved
                if best_track_id in self.prev_positions:
                    prev_centroid = self.prev_positions[best_track_id]
                    dist_moved = self._calculate_distance(det_centroid, prev_centroid)
                    self.tracks[best_track_id]["total_distance"] += dist_moved

                self.prev_positions[best_track_id] = det_centroid

        # Create new tracks for unmatched detections
        for det_idx, det_centroid in detection_centroids:
            if det_idx not in matched_detections:
                new_id = self.next_track_id
                self.next_track_id += 1
                self.tracks[new_id] = {
                    "centroid": det_centroid,
                    "frames_missing": 0,
                    "total_distance": 0,
                }
                self.prev_positions[new_id] = det_centroid

        # Remove stale tracks
        to_remove = []
        for track_id, track_data in self.tracks.items():
            if track_data["frames_missing"] > self.max_frames_to_skip:
                to_remove.append(track_id)

        for track_id in to_remove:
            del self.tracks[track_id]
            if track_id in self.prev_positions:
                del self.prev_positions[track_id]

        # Return active tracks
        results = []
        for track_id, track_data in self.tracks.items():
            if track_data["frames_missing"] == 0:
                x, y = track_data["centroid"]
                results.append(
                    {
                        "track_id": track_id,
                        "centroid": (x, y),
                        "total_distance": track_data["total_distance"],
                        "frames_missing": 0,
                    }
                )

        return results

    def _calculate_distance(self, p1: Tuple, p2: Tuple) -> float:
        """Calculate Euclidean distance between two points"""
        return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

    def reset(self):
        """Reset tracker state"""
        if self.use_bytetrack and hasattr(self, "tracker"):
            # Re-initialize ByteTracker
            self.tracker = BT(
                track_thresh=0.5, track_buffer=30, match_thresh=0.8, frame_rate=30
            )
        else:
            self.tracks = {}
            self.next_track_id = 1
            self.prev_positions = {}


def create_tracker(
    max_distance: float = 100.0, max_frames_to_skip: int = 30
) -> PlayerTracker:
    """Factory function to create player tracker"""
    return PlayerTracker(
        max_distance=max_distance, max_frames_to_skip=max_frames_to_skip
    )
