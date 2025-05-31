import cv2
import numpy as np
import threading
import time
from datetime import datetime
import os
import config

class CameraHandler:
    def __init__(self):
        self.cap = None
        self.background_subtractor = None
        self.is_recording = False
        self.video_writer = None
        self.frame_count = 0
        self.setup_camera()
        self.setup_directories()
        
    def setup_camera(self):
        """Initialize camera and background subtractor"""
        self.cap = cv2.VideoCapture(config.CAMERA_INDEX)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, config.FPS)
        
        # Create background subtractor for motion detection
        self.background_subtractor = cv2.createBackgroundSubtractorMOG2(
            detectShadows=True, history=500, varThreshold=16
        )
        
    def setup_directories(self):
        """Create necessary directories for recordings"""
        os.makedirs(config.RECORDINGS_DIR, exist_ok=True)
        os.makedirs(config.ALERTS_DIR, exist_ok=True)
        
    def get_frame(self):
        """Capture a frame from camera"""
        ret, frame = self.cap.read()
        if ret:
            self.frame_count += 1
            return frame
        return None
        
    def detect_motion(self, frame):
        """Detect motion in the current frame"""
        # Convert to grayscale and blur
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (config.BLUR_SIZE, config.BLUR_SIZE), 0)
        
        # Apply background subtraction
        fg_mask = self.background_subtractor.apply(blurred)
        
        # Remove noise and fill holes
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        motion_detected = False
        motion_areas = []
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > config.MIN_CONTOUR_AREA:
                motion_detected = True
                x, y, w, h = cv2.boundingRect(contour)
                motion_areas.append((x, y, w, h))
                
        return motion_detected, motion_areas, fg_mask
        
    def start_recording(self, filename=None):
        """Start recording video"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{config.RECORDINGS_DIR}/motion_detected_{timestamp}.avi"
            
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.video_writer = cv2.VideoWriter(
            filename, fourcc, config.FPS, 
            (config.FRAME_WIDTH, config.FRAME_HEIGHT)
        )
        self.is_recording = True
        print(f"Started recording: {filename}")
        
    def stop_recording(self):
        """Stop recording video"""
        if self.is_recording and self.video_writer:
            self.video_writer.release()
            self.video_writer = None
            self.is_recording = False
            print("Recording stopped")
            
    def record_frame(self, frame):
        """Record a single frame"""
        if self.is_recording and self.video_writer:
            self.video_writer.write(frame)
            
    def save_frame(self, frame, prefix="frame"):
        """Save a single frame as image"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{config.ALERTS_DIR}/{prefix}_{timestamp}.jpg"
        cv2.imwrite(filename, frame)
        print(f"Frame saved: {filename}")
        return filename
        
    def draw_motion_areas(self, frame, motion_areas):
        """Draw rectangles around detected motion areas"""
        for (x, y, w, h) in motion_areas:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, "MOTION", (x, y - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        return frame
        
    def add_overlay_info(self, frame, motion_detected, fps=0):
        """Add information overlay to frame"""
        height, width = frame.shape[:2]
        
        # Status indicator
        status_color = (0, 255, 0) if motion_detected else (255, 255, 255)
        status_text = "MOTION DETECTED" if motion_detected else "MONITORING"
        cv2.putText(frame, status_text, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 2)
        
        # Recording indicator
        if self.is_recording:
            cv2.circle(frame, (width - 30, 30), 10, (0, 0, 255), -1)
            cv2.putText(frame, "REC", (width - 60, 35), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        
        # FPS display
        if config.DISPLAY_FPS:
            cv2.putText(frame, f"FPS: {fps:.1f}", (10, height - 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, timestamp, (10, height - 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame
        
    def cleanup(self):
        """Clean up camera resources"""
        if self.is_recording:
            self.stop_recording()
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
