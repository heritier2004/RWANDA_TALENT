"""
Camera Module - Video Input Handler
Supports: webcam, video file, and stream URL (RTSP)
"""

import cv2
import numpy as np
from typing import Optional, Tuple


class VideoCapture:
    """Handle video input from various sources"""
    
    def __init__(self, source: str = "0", backend: str = "opencv"):
        """
        Initialize video capture
        
        Args:
            source: "0" for webcam, "path/to/video.mp4", or "rtsp://..."
            backend: Video backend to use
        """
        self.source = source
        self.backend = backend
        self.cap = None
        self.fps = 0
        self.frame_count = 0
        self.width = 0
        self.height = 0
        self.is_opened = False
        
    def open(self) -> bool:
        """
        Open video source
        
        Returns:
            bool: True if opened successfully
        """
        # Convert string source to int if it's a webcam
        if self.source.isdigit():
            self.cap = cv2.VideoCapture(int(self.source))
        else:
            self.cap = cv2.VideoCapture(self.source)
            
        if self.cap is None or not self.cap.isOpened():
            print(f"Error: Could not open video source: {self.source}")
            return False
            
        # Get video properties
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.is_opened = True
        
        print(f"Video opened: {self.width}x{self.height} @ {self.fps} FPS")
        return True
    
    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Read next frame
        
        Returns:
            Tuple of (success, frame)
        """
        if self.cap is None:
            return False, None
        return self.cap.read()
    
    def release(self):
        """Release video capture resources"""
        if self.cap is not None:
            self.cap.release()
            self.is_opened = False
            print("Video capture released")
    
    def get_frame_number(self) -> int:
        """Get current frame number"""
        if self.cap is not None:
            return int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
        return 0
    
    def get_timestamp(self) -> float:
        """Get current timestamp in milliseconds"""
        if self.cap is not None:
            return self.cap.get(cv2.CAP_PROP_POS_MSEC)
        return 0.0
    
    def get_elapsed_minutes(self) -> float:
        """Get elapsed time in minutes"""
        if self.fps > 0:
            frame = self.get_frame_number()
            return (frame / self.fps) / 60.0
        return 0.0
    
    def __enter__(self):
        """Context manager entry"""
        self.open()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.release()


def get_video_source(source_type: str, source_path: str = "") -> str:
    """
    Get video source based on type
    
    Args:
        source_type: "webcam", "file", or "stream"
        source_path: Path or URL for file/stream
    
    Returns:
        Source string for VideoCapture
    """
    if source_type == "webcam":
        return "0"  # Default webcam
    elif source_type == "file":
        return source_path
    elif source_type == "stream":
        return source_path
    else:
        return "0"


# Test function
if __name__ == "__main__":
    # Test webcam
    print("Testing webcam capture...")
    cam = VideoCapture("0")
    if cam.open():
        ret, frame = cam.read()
        if ret:
            print(f"Frame captured: {frame.shape}")
        cam.release()
    print("Camera test complete!")
