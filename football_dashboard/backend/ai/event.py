"""
Event Detection Module
Detects important events like goals, key actions
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
import time


class EventDetector:
    """Detect important events in football match"""
    
    def __init__(self, frame_width: int = 640, frame_height: int = 480):
        """
        Initialize event detector
        
        Args:
            frame_width: Width of video frame
            frame_height: Height of video frame
        """
        self.frame_width = frame_width
        self.frame_height = frame_height
        
        # Goal positions (can be adjusted based on actual pitch)
        self.goal_width = 80
        self.goal_top_y = frame_height // 2 - 40
        self.goal_bottom_y = frame_height // 2 + 40
        
        # Event history
        self.events = []
        
        # Thresholds
        self.goal_detection_distance = 50  # pixels
        
        # Timing
        self.last_goal_time = 0
        self.goal_cooldown = 5.0  # seconds between goals
        
        # Team colors (would be detected in real system)
        self.team_a_positions = []
        self.team_b_positions = []
        
    def detect_events(self, tracked_objects: List[dict], frame_time: float) -> List[dict]:
        """
        Detect events from tracked objects
        
        Args:
            tracked_objects: List of tracked player objects
            frame_time: Current frame timestamp
            
        Returns:
            List of detected events
        """
        detected_events = []
        
        # Check for ball near goal (simplified goal detection)
        # In a real system, we would track the ball specifically
        
        # For now, simulate goal detection based on player positions
        # (Real implementation would use ball tracking)
        
        current_time = time.time()
        
        # Check for goal opportunity (players near goal area)
        for obj in tracked_objects:
            centroid = obj['centroid']
            
            # Check left goal
            if centroid[0] < self.goal_detection_distance:
                if self.goal_top_y < centroid[1] < self.goal_bottom_y:
                    # Possible goal - left side
                    if current_time - self.last_goal_time > self.goal_cooldown:
                        event = {
                            'type': 'goal_opportunity',
                            'team': 'team_a',
                            'timestamp': frame_time,
                            'position': centroid,
                            'track_id': obj.get('track_id')
                        }
                        detected_events.append(event)
                        self.events.append(event)
            
            # Check right goal
            if centroid[0] > self.frame_width - self.goal_detection_distance:
                if self.goal_top_y < centroid[1] < self.goal_bottom_y:
                    # Possible goal - right side
                    if current_time - self.last_goal_time > self.goal_cooldown:
                        event = {
                            'type': 'goal_opportunity',
                            'team': 'team_b',
                            'timestamp': frame_time,
                            'position': centroid,
                            'track_id': obj.get('track_id')
                        }
                        detected_events.append(event)
                        self.events.append(event)
        
        # Detect high activity areas (potential key actions)
        key_actions = self._detect_key_actions(tracked_objects, frame_time)
        detected_events.extend(key_actions)
        
        return detected_events
    
    def _detect_key_actions(self, tracked_objects: List[dict], frame_time: float) -> List[dict]:
        """Detect key actions like sprints, tackles"""
        events = []
        
        # Count players in different zones
        center_players = 0
        attacking_players = 0
        
        for obj in tracked_objects:
            centroid = obj['centroid']
            
            # Center zone (0.3 to 0.7 of width)
            if self.frame_width * 0.3 < centroid[0] < self.frame_width * 0.7:
                center_players += 1
            
            # Attacking zones (near goals)
            if centroid[0] < self.frame_width * 0.15 or centroid[0] > self.frame_width * 0.85:
                attacking_players += 1
        
        # Generate events based on zones
        if center_players >= 8:
            event = {
                'type': 'midfield_battle',
                'timestamp': frame_time,
                'player_count': center_players
            }
            events.append(event)
            self.events.append(event)
        
        if attacking_players >= 3:
            event = {
                'type': 'attacking_play',
                'timestamp': frame_time,
                'player_count': attacking_players
            }
            events.append(event)
            self.events.append(event)
        
        return events
    
    def get_goal_events(self) -> List[dict]:
        """Get all goal-related events"""
        return [e for e in self.events if e['type'] == 'goal_opportunity']
    
    def get_recent_events(self, seconds: int = 60) -> List[dict]:
        """Get events from last N seconds"""
        current_time = time.time()
        return [e for e in self.events if current_time - e['timestamp'] < seconds]
    
    def get_all_events(self) -> List[dict]:
        """Get all detected events"""
        return self.events.copy()
    
    def get_event_summary(self) -> dict:
        """Get summary of all events"""
        event_types = {}
        for event in self.events:
            event_type = event['type']
            event_types[event_type] = event_types.get(event_type, 0) + 1
        
        return {
            'total_events': len(self.events),
            'event_types': event_types,
            'goals': len(self.get_goal_events())
        }
    
    def reset(self):
        """Reset event detector"""
        self.events = []
        self.last_goal_time = 0


def create_event_detector(frame_width: int = 640, frame_height: int = 480) -> EventDetector:
    """Factory function to create event detector"""
    return EventDetector(frame_width=frame_width, frame_height=frame_height)


# Test function
if __name__ == "__main__":
    print("Testing Event Detector...")
    
    detector = EventDetector()
    
    # Simulate tracked players
    test_tracks = [
        [{'track_id': 1, 'centroid': (30, 240)}, {'track_id': 2, 'centroid': (300, 250)}],
        [{'track_id': 1, 'centroid': (610, 240)}, {'track_id': 2, 'centroid': (310, 255)}],
    ]
    
    for i, tracks in enumerate(test_tracks):
        frame_time = i * 1.0
        events = detector.detect_events(tracks, frame_time)
        print(f"Frame {i}: {len(events)} events")
        for event in events:
            print(f"  {event['type']}")
    
    print("\nEvent summary:", detector.get_event_summary())
    print("Event detector test complete!")
