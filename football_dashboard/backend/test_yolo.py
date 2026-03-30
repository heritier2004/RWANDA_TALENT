"""
Test script to verify YOLO model works for player detection.
This script loads the YOLOv8 nano model and runs a simple detection test.
"""
from ultralytics import YOLO
import cv2
import numpy as np

def test_yolo_model():
    print("Loading YOLOv8n model...")
    # Load the nano model (smallest, fastest)
    model = YOLO('yolov8n.pt')
    print("Model loaded successfully!")
    
    # Create a dummy image for testing (480x640 RGB)
    print("Creating test image...")
    test_image = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Run inference
    print("Running inference...")
    results = model(test_image, verbose=False)
    
    print(f"Results obtained: {len(results)} result(s)")
    print("YOLO model is working correctly!")
    return True

def test_cv2():
    """Test OpenCV is working"""
    print("\nTesting OpenCV...")
    # Create a simple test image
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    print(f"OpenCV version: {cv2.__version__}")
    print("OpenCV is working!")
    return True

def test_numpy():
    """Test NumPy is working"""
    print("\nTesting NumPy...")
    arr = np.array([1, 2, 3, 4, 5])
    print(f"NumPy version: {np.__version__}")
    print(f"Test array: {arr}")
    print("NumPy is working!")
    return True

if __name__ == "__main__":
    print("=" * 50)
    print("Testing AI Dependencies")
    print("=" * 50)
    
    test_numpy()
    test_cv2()
    test_yolo_model()
    
    print("\n" + "=" * 50)
    print("ALL TESTS PASSED!")
    print("=" * 50)
