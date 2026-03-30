"""
Detection Module - YOLO Player Detection
Uses YOLOv8 for real-time object detection
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
import os


class YOLODetector:
    """YOLO-based object detector for football players"""
    
    def __init__(self, model_path: str = "yolov8n.pt", confidence: float = 0.5):
        """
        Initialize YOLO detector
        
        Args:
            model_path: Path to YOLO model file
            confidence: Minimum confidence threshold
        """
        self.model_path = model_path
        self.confidence = confidence
        self.model = None
        self.class_names = []
        self.load_model()
    
    def load_model(self):
        """Load YOLO model"""
        try:
            # Try to import ultralytics
            from ultralytics import YOLO
            print(f"Loading YOLO model: {self.model_path}")
            self.model = YOLO(self.model_path)
            print("YOLO model loaded successfully!")
        except ImportError:
            print("Ultralytics not installed. Using mock detection.")
            self.model = None
        except Exception as e:
            print(f"Error loading model: {e}")
            self.model = None
    
    def detect(self, frame: np.ndarray) -> List[dict]:
        """
        Detect objects in frame
        
        Args:
            frame: Input frame (BGR format)
            
        Returns:
            List of detections with bbox, confidence, class
        """
        if self.model is None:
            # Return mock detections for testing
            return self._mock_detect(frame)
        
        try:
            # Run inference
            results = self.model(frame, verbose=False)
            
            detections = []
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    # Get box coordinates
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    
                    # Filter by confidence
                    if conf < self.confidence:
                        continue
                    
                    # Filter for person class (class 0 in COCO)
                    if cls == 0:  # person
                        detections.append({
                            'bbox': [int(x1), int(y1), int(x2), int(y2)],
                            'confidence': conf,
                            'class': cls,
                            'centroid': ((x1 + x2) / 2, (y1 + y2) / 2)
                        })
            
            return detections
            
        except Exception as e:
            print(f"Detection error: {e}")
            return []
    
    def _mock_detect(self, frame: np.ndarray) -> List[dict]:
        """
        Mock detection for testing without YOLO model
        Simulates player detection
        """
        h, w = frame.shape[:2]
        
        # Generate random detections for testing
        import random
        detections = []
        
        # Simulate 2 teams (11 players each)
        num_players = random.randint(8, 14)
        
        for i in range(num_players):
            # Random position in lower half (pitch)
            x1 = random.randint(0, w - 100)
            y1 = random.randint(h // 2, h - 80)
            x2 = x1 + random.randint(40, 80)
            y2 = y1 + random.randint(60, 100)
            
            # Clamp to frame
            x2 = min(x2, w)
            y2 = min(y2, h)
            
            detections.append({
                'bbox': [x1, y1, x2, y2],
                'confidence': random.uniform(0.6, 0.95),
                'class': 0,  # person
                'centroid': ((x1 + x2) / 2, (y1 + y2) / 2)
            })
        
        return detections
    
    def draw_detections(self, frame: np.ndarray, detections: List[dict]) -> np.ndarray:
        """
        Draw bounding boxes on frame
        
        Args:
            frame: Input frame
            detections: List of detections
            
        Returns:
            Frame with drawn boxes
        """
        output = frame.copy()
        
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            conf = det['confidence']
            
            # Draw rectangle
            cv2.rectangle(output, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Draw label
            label = f"Player: {conf:.2f}"
            cv2.putText(output, label, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        return output


def get_detector(model_name: str = "yolov8n.pt") -> YOLODetector:
    """Factory function to create detector"""
    return YOLODetector(model_path=model_name)


# Test function
if __name__ == "__main__":
    print("Testing YOLO Detector...")
    
    # Create detector
    detector = YOLODetector()
    
    # Test with blank frame
    test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    detections = detector.detect(test_frame)
    print(f"Mock detections: {len(detections)}")
    
    for i, det in enumerate(detections[:3]):
        print(f"  Detection {i}: bbox={det['bbox']}, conf={det['confidence']:.2f}")
    
    print("Detection test complete!")
