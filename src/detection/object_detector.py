import cv2
import numpy as np
import threading
import time
from datetime import datetime
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("⚠️ YOLO not available. Object detection disabled.")

import config

class ObjectDetector:
    def __init__(self):
        self.model = None
        self.detection_enabled = False
        self.setup_yolo()
        
        # COCO class names that YOLO can detect
        self.class_names = [
            'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck',
            'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench',
            'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra',
            'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee',
            'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove',
            'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup',
            'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange',
            'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
            'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse',
            'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink',
            'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier',
            'toothbrush'
        ]
        
        # High priority objects for security alerts
        self.security_objects = {
            'person': {'priority': 'high', 'color': (0, 0, 255)},      # Red
            'car': {'priority': 'medium', 'color': (0, 165, 255)},     # Orange
            'truck': {'priority': 'medium', 'color': (0, 165, 255)},   # Orange
            'motorcycle': {'priority': 'medium', 'color': (0, 165, 255)}, # Orange
            'bicycle': {'priority': 'low', 'color': (0, 255, 255)},    # Yellow
            'dog': {'priority': 'low', 'color': (255, 0, 255)},        # Magenta
            'cat': {'priority': 'low', 'color': (255, 0, 255)},        # Magenta
            'bird': {'priority': 'low', 'color': (255, 255, 0)},       # Cyan
        }
        
    def setup_yolo(self):
        """Initialize YOLO model"""
        if not YOLO_AVAILABLE:
            return
            
        try:
            print("🤖 Loading YOLO model... (this may take a moment)")
            # Use YOLOv8 nano model for speed (you can change to 's', 'm', 'l', 'x' for better accuracy)
            self.model = YOLO('yolov8n.pt')  # Downloads automatically if not present
            self.detection_enabled = True
            print("✅ YOLO model loaded successfully")
        except Exception as e:
            print(f"❌ Error loading YOLO model: {e}")
            self.detection_enabled = False
            
    def detect_objects(self, frame, confidence_threshold=0.5):
        """Detect objects in frame using YOLO"""
        if not self.detection_enabled or self.model is None:
            return []
            
        try:
            # Run YOLO detection
            results = self.model(frame, conf=confidence_threshold, verbose=False)
            
            detected_objects = []
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Get box coordinates
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        confidence = box.conf[0].cpu().numpy()
                        class_id = int(box.cls[0].cpu().numpy())
                        
                        # Get class name
                        if class_id < len(self.class_names):
                            class_name = self.class_names[class_id]
                            
                            detected_objects.append({
                                'class_name': class_name,
                                'confidence': confidence,
                                'bbox': (int(x1), int(y1), int(x2), int(y2)),
                                'class_id': class_id
                            })
                            
            return detected_objects
            
        except Exception as e:
            print(f"Error in object detection: {e}")
            return []
            
    def draw_detections(self, frame, detections):
        """Draw detection boxes and labels on frame"""
        for detection in detections:
            class_name = detection['class_name']
            confidence = detection['confidence']
            x1, y1, x2, y2 = detection['bbox']
            
            # Get color based on object type
            if class_name in self.security_objects:
                color = self.security_objects[class_name]['color']
                priority = self.security_objects[class_name]['priority']
            else:
                color = (0, 255, 0)  # Green for other objects
                priority = 'info'
                
            # Draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Prepare label
            label = f"{class_name}: {confidence:.2f}"
            if priority == 'high':
                label = f"🚨 {label}"
            elif priority == 'medium':
                label = f"⚠️ {label}"
                
            # Draw label background
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            cv2.rectangle(frame, (x1, y1 - label_size[1] - 10), 
                         (x1 + label_size[0], y1), color, -1)
            
            # Draw label text
            cv2.putText(frame, label, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                       
        return frame
        
    def filter_security_relevant(self, detections):
        """Filter detections for security-relevant objects"""
        security_detections = []
        
        for detection in detections:
            class_name = detection['class_name']
            if class_name in self.security_objects:
                detection['priority'] = self.security_objects[class_name]['priority']
                security_detections.append(detection)
                
        return security_detections
        
    def get_detection_summary(self, detections):
        """Get summary of detected objects"""
        if not detections:
            return "No objects detected"
            
        summary = {}
        for detection in detections:
            class_name = detection['class_name']
            if class_name in summary:
                summary[class_name] += 1
            else:
                summary[class_name] = 1
                
        # Create summary string
        items = []
        for obj_type, count in summary.items():
            if count > 1:
                items.append(f"{count} {obj_type}s")
            else:
                items.append(f"{count} {obj_type}")
                
        return ", ".join(items)
        
    def should_trigger_alert(self, detections):
        """Determine if detections should trigger security alert"""
        high_priority_objects = []
        
        for detection in detections:
            class_name = detection['class_name']
            if class_name in self.security_objects:
                priority = self.security_objects[class_name]['priority']
                if priority == 'high':
                    high_priority_objects.append(detection)
                    
        return len(high_priority_objects) > 0, high_priority_objects
