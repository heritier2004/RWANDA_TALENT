"""
AI Module - Football Player Tracking System
"""

from .camera import VideoCapture, get_video_source
from .detection import YOLODetector, get_detector
from .tracking import PlayerTracker, create_tracker
from .metrics import PlayerMetrics, create_metrics_calculator
from .event import EventDetector, create_event_detector
from .run_ai import AIRunner, run_ai_pipeline

__all__ = [
    'VideoCapture',
    'get_video_source',
    'YOLODetector',
    'get_detector',
    'PlayerTracker',
    'create_tracker',
    'PlayerMetrics',
    'create_metrics_calculator',
    'EventDetector',
    'create_event_detector',
    'AIRunner',
    'run_ai_pipeline'
]

__version__ = '1.0.0'
