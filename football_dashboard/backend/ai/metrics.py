"""
Metrics Module - Player Statistics Calculator
Calculates distance, speed, and performance metrics
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
import math
import time


class PlayerMetrics:
    """Calculate and track player performance metrics"""
    
    def __init__(self, pixels_per_meter: float = 50.0):
        """
        Initialize metrics calculator
        
        Args:
            pixels_per_meter: Conversion factor from pixels to meters
        """
        self.pixels_per_meter = pixels_per_meter
        
        # Player data: {track_id: {'positions': [], 'distances': [], 'speeds': [], 'times': []}}
        self.player_data = {}
        
        # Speed thresholds
        self.sprint_threshold = 7.0  # m/s (approx 25 km/h)
        self.high_speed_threshold = 5.0  # m/s
        
        # Timing
        self.start_time = None
        self.last_update_time = None
        
    def update(self, tracked_objects: List[dict], frame_time: float, fps: float) -> Dict[int, dict]:
        """
        Update metrics for tracked players
        
        Args:
            tracked_objects: List of tracked player objects
            frame_time: Current frame timestamp in seconds
            fps: Frames per second
            
        Returns:
            Updated player metrics
        """
        if self.start_time is None:
            self.start_time = frame_time
            self.last_update_time = frame_time
        
        current_players = {}
        
        for obj in tracked_objects:
            track_id = obj['track_id']
            centroid = obj['centroid']
            
            # Initialize player data if new
            if track_id not in self.player_data:
                self.player_data[track_id] = {
                    'positions': [],
                    'distances': [],
                    'speeds': [],
                    'times': [],
                    'sprint_count': 0,
                    'high_speed_count': 0,
                    'total_distance': 0.0,
                    'avg_speed': 0.0,
                    'max_speed': 0.0
                }
            
            player = self.player_data[track_id]
            
            # Add position
            player['positions'].append(centroid)
            player['times'].append(frame_time)
            
            # Calculate distance and speed if we have previous position
            if len(player['positions']) > 1:
                prev_pos = player['positions'][-2]
                prev_time = player['times'][-2]
                
                # Distance in pixels
                dist_pixels = math.sqrt(
                    (centroid[0] - prev_pos[0])**2 + 
                    (centroid[1] - prev_pos[1])**2
                )
                
                # Convert to meters
                dist_meters = dist_pixels / self.pixels_per_meter
                
                # Time difference
                dt = frame_time - prev_time if frame_time > prev_time else (1.0 / fps)
                
                # Speed in m/s
                speed = dist_meters / dt if dt > 0 else 0
                
                player['distances'].append(dist_meters)
                player['speeds'].append(speed)
                player['total_distance'] += dist_meters
                
                # Count sprints and high speed moments
                if speed >= self.sprint_threshold:
                    player['sprint_count'] += 1
                if speed >= self.high_speed_threshold:
                    player['high_speed_count'] += 1
                
                # Update max speed
                if speed > player['max_speed']:
                    player['max_speed'] = speed
            
            # Keep only last 1000 entries to save memory
            if len(player['positions']) > 1000:
                player['positions'] = player['positions'][-500:]
                player['times'] = player['times'][-500:]
                player['distances'] = player['distances'][-500:]
                player['speeds'] = player['speeds'][-500:]
            
            # Calculate averages
            if player['speeds']:
                player['avg_speed'] = sum(player['speeds']) / len(player['speeds'])
            
            # Get elapsed time in minutes
            elapsed = frame_time - self.start_time if self.start_time else 0
            minutes = elapsed / 60.0
            
            current_players[track_id] = {
                'track_id': track_id,
                'total_distance': player['total_distance'],
                'avg_speed': player['avg_speed'],
                'max_speed': player['max_speed'],
                'sprint_count': player['sprint_count'],
                'high_speed_count': player['high_speed_count'],
                'minutes': minutes,
                'performance_score': self._calculate_performance_score(player, minutes)
            }
        
        self.last_update_time = frame_time
        
        return current_players
    
    def _calculate_performance_score(self, player_data: dict, minutes: float) -> float:
        """
        Calculate overall performance score (0-100)
        
        Args:
            player_data: Player's metrics
            minutes: Minutes played
            
        Returns:
            Performance score
        """
        if minutes <= 0:
            return 0.0
        
        # Weight factors
        distance_score = min(player_data['total_distance'] / 100.0, 1.0) * 30  # Max 30 points
        speed_score = min(player_data['avg_speed'] / 6.0, 1.0) * 25  # Max 25 points
        sprint_score = min(player_data['sprint_count'] / 10.0, 1.0) * 25  # Max 25 points
        max_speed_score = min(player_data['max_speed'] / 10.0, 1.0) * 20  # Max 20 points
        
        total = distance_score + speed_score + sprint_score + max_speed_score
        
        return round(total, 1)
    
    def get_player_summary(self, track_id: int) -> Optional[dict]:
        """Get summary for a specific player"""
        if track_id not in self.player_data:
            return None
        
        player = self.player_data[track_id]
        elapsed = (self.last_update_time - self.start_time) if self.start_time and self.last_update_time else 0
        minutes = elapsed / 60.0
        
        return {
            'track_id': track_id,
            'total_distance_meters': round(player['total_distance'], 2),
            'total_distance_km': round(player['total_distance'] / 1000, 3),
            'avg_speed_mps': round(player['avg_speed'], 2),
            'avg_speed_kmh': round(player['avg_speed'] * 3.6, 2),
            'max_speed_mps': round(player['max_speed'], 2),
            'max_speed_kmh': round(player['max_speed'] * 3.6, 2),
            'sprint_count': player['sprint_count'],
            'high_speed_count': player['high_speed_count'],
            'minutes_played': round(minutes, 1),
            'performance_score': self._calculate_performance_score(player, minutes)
        }
    
    def get_all_summaries(self) -> List[dict]:
        """Get summaries for all tracked players"""
        summaries = []
        for track_id in self.player_data:
            summary = self.get_player_summary(track_id)
            if summary:
                summaries.append(summary)
        return summaries
    
    def get_top_players(self, limit: int = 5) -> List[dict]:
        """Get top performing players"""
        all_players = self.get_all_summaries()
        sorted_players = sorted(all_players, key=lambda x: x['performance_score'], reverse=True)
        return sorted_players[:limit]
    
    def get_match_stats(self) -> dict:
        """Get overall match statistics"""
        all_players = self.get_all_summaries()
        
        if not all_players:
            return {
                'total_players': 0,
                'total_distance': 0,
                'avg_distance': 0,
                'total_sprints': 0,
                'match_duration_minutes': 0
            }
        
        elapsed = (self.last_update_time - self.start_time) if self.start_time and self.last_update_time else 0
        
        return {
            'total_players': len(all_players),
            'total_distance': sum(p['total_distance_meters'] for p in all_players),
            'avg_distance': sum(p['total_distance_meters'] for p in all_players) / len(all_players),
            'total_sprints': sum(p['sprint_count'] for p in all_players),
            'match_duration_minutes': round(elapsed / 60.0, 1)
        }
    
    def reset(self):
        """Reset all metrics"""
        self.player_data = {}
        self.start_time = None
        self.last_update_time = None


def create_metrics_calculator(pixels_per_meter: float = 50.0) -> PlayerMetrics:
    """Factory function to create metrics calculator"""
    return PlayerMetrics(pixels_per_meter=pixels_per_meter)


# Test function
if __name__ == "__main__":
    print("Testing Player Metrics...")
    
    metrics = PlayerMetrics()
    
    # Simulate tracked players
    test_tracks = [
        [{'track_id': 1, 'centroid': (100, 200)}, {'track_id': 2, 'centroid': (300, 250)}],
        [{'track_id': 1, 'centroid': (105, 205)}, {'track_id': 2, 'centroid': (310, 255)}],
        [{'track_id': 1, 'centroid': (110, 210)}, {'track_id': 2, 'centroid': (320, 260)}],
    ]
    
    for i, tracks in enumerate(test_tracks):
        frame_time = i * 0.5  # 2 fps simulation
        player_metrics = metrics.update(tracks, frame_time, 2.0)
        print(f"Frame {i}:")
        for pid, data in player_metrics.items():
            print(f"  Player {pid}: dist={data['total_distance']:.1f}m, speed={data['avg_speed']:.1f}m/s, score={data['performance_score']}")
    
    print("\nTop players:", metrics.get_top_players())
    print("Metrics test complete!")
