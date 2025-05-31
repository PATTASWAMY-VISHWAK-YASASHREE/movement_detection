"""
Motion Detection Security System with Mobile Camera Integration

This script integrates the mobile camera handler with the existing motion detection
system, allowing you to use your Android phone as a security camera.

Features:
- Supports both webcam and mobile camera (Android via USB debugging)
- Database integration for storing alerts and images
- Web viewer for reviewing captured images
- Resolution optimization for mobile cameras (420p max)
- Multiple streaming methods for mobile devices

Author: Motion Detection Security System
"""

import cv2
import numpy as np
import time
import os
import threading
from datetime import datetime
import psycopg2
import base64
import json
import config
from mobile_camera_handler import MobileCameraHandler
from database_config import get_db_connection
from image_processor import ImageProcessor

class MotionDetectionMobile:
    def __init__(self):
        """Initialize Motion Detection with Mobile Camera Support"""
        self.background_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500, varThreshold=50, detectShadows=True
        )
        
        # Camera setup
        self.cap = None
        self.mobile_cam = None
        self.using_mobile = config.USE_MOBILE_CAMERA
        
        # Motion detection state
        self.last_alert_time = 0
        self.is_recording = False
        self.frame_count = 0
        
        # Database integration
        self.image_processor = ImageProcessor()
        
        # Statistics
        self.stats = {
            'total_frames': 0,
            'motion_detected': 0,
            'alerts_triggered': 0,
            'frames_saved': 0
        }
        
        print(f"🔧 Motion Detection initialized")
        print(f"📱 Mobile camera: {'Enabled' if self.using_mobile else 'Disabled'}")
        
    def initialize_camera(self):
        """Initialize camera (webcam or mobile)"""
        if self.using_mobile:
            return self._initialize_mobile_camera()
        else:
            return self._initialize_webcam()
    
    def _initialize_mobile_camera(self):
        """Initialize mobile camera via ADB"""
        print("📱 Initializing mobile camera...")
        
        self.mobile_cam = MobileCameraHandler(
            max_resolution=config.MOBILE_CAMERA_MAX_RESOLUTION
        )
        
        # Check for devices
        devices = self.mobile_cam.check_devices()
        if not devices:
            print("❌ No mobile devices found")
            print("📋 Please ensure:")
            print("   - USB debugging is enabled on your phone")
            print("   - Phone is connected via USB cable")
            print("   - ADB drivers are installed")
            return False
        
        # Connect to device
        if not self.mobile_cam.connect_device(config.MOBILE_DEVICE_ID):
            print("❌ Failed to connect to mobile device")
            return False
        
        # Start streaming
        if not self.mobile_cam.start_streaming():
            print("❌ Failed to start mobile camera stream")
            return False
        
        print("✅ Mobile camera initialized successfully")
        
        # Get device info
        info = self.mobile_cam.get_device_info()
        print(f"📱 Device: {info.get('model', 'Unknown')} ({info.get('device_id', 'Unknown')})")
        print(f"🎥 Resolution: {info.get('max_resolution', 'Unknown')}")
        
        return True
    
    def _initialize_webcam(self):
        """Initialize regular webcam"""
        print("🎥 Initializing webcam...")
        
        self.cap = cv2.VideoCapture(config.CAMERA_INDEX)
        if not self.cap.isOpened():
            print(f"❌ Failed to open camera {config.CAMERA_INDEX}")
            return False
        
        # Set camera properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, config.FPS)
        
        print("✅ Webcam initialized successfully")
        return True
    
    def read_frame(self):
        """Read frame from active camera source"""
        if self.using_mobile and self.mobile_cam:
            frame = self.mobile_cam.get_frame()
            return frame is not None, frame
        elif self.cap:
            return self.cap.read()
        else:
            return False, None
    
    def process_motion_detection(self, frame):
        """Process motion detection on frame"""
        if frame is None:
            return False, frame
        
        # Convert to grayscale for motion detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (config.BLUR_SIZE, config.BLUR_SIZE), 0)
        
        # Apply background subtraction
        fg_mask = self.background_subtractor.apply(gray)
        
        # Find contours
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        motion_detected = False
        motion_areas = []
        
        for contour in contours:
            area = cv2.contourArea(contour)
            
            # Filter by contour area
            if config.MIN_CONTOUR_AREA < area < config.MAX_CONTOUR_AREA:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Filter by motion size
                if w >= config.MIN_MOTION_WIDTH and h >= config.MIN_MOTION_HEIGHT:
                    motion_areas.append((x, y, w, h))
                    motion_detected = True
        
        # Draw motion areas if enabled
        if config.SHOW_MOTION_AREAS and motion_areas:
            for (x, y, w, h) in motion_areas:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, "MOTION", (x, y - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        return motion_detected, frame
    
    def handle_motion_alert(self, frame):
        """Handle motion detection alert"""
        current_time = time.time()
        
        # Check cooldown period
        if current_time - self.last_alert_time < config.ALERT_COOLDOWN:
            return
        
        self.last_alert_time = current_time
        self.stats['alerts_triggered'] += 1
        
        timestamp = datetime.now()
        print(f"🚨 MOTION DETECTED at {timestamp.strftime('%H:%M:%S')}")
        
        # Save alert to database
        if config.SAVE_FRAMES:
            self._save_alert_to_database(frame, timestamp)
        
        # Trigger other alerts if enabled
        if config.ENABLE_SOUND_ALERTS:
            self._play_alert_sound()
        
        if config.ENABLE_DESKTOP_NOTIFICATIONS:
            self._show_desktop_notification(timestamp)
    
    def _save_alert_to_database(self, frame, timestamp):
        """Save motion alert and frame to database"""
        try:
            # Create alert record
            alert_data = {
                'timestamp': timestamp,
                'motion_confidence': 0.8,  # Could be calculated based on motion area
                'camera_source': 'mobile' if self.using_mobile else 'webcam',
                'frame_count': self.frame_count
            }
            
            # Save frame as base64 image
            success, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if success:
                image_base64 = base64.b64encode(buffer).decode('utf-8')
                
                # Use image processor to save to database
                alert_id = self.image_processor.save_alert_with_image(
                    timestamp=timestamp,
                    image_base64=image_base64,
                    camera_source=alert_data['camera_source'],
                    motion_confidence=alert_data['motion_confidence']
                )
                
                if alert_id:
                    self.stats['frames_saved'] += 1
                    print(f"💾 Alert saved to database (ID: {alert_id})")
                else:
                    print("❌ Failed to save alert to database")
            
        except Exception as e:
            print(f"❌ Database error: {e}")
    
    def _play_alert_sound(self):
        """Play alert sound (simple beep)"""
        try:
            # Windows beep
            import winsound
            winsound.Beep(1000, 500)  # 1000Hz for 500ms
        except ImportError:
            # Linux/Mac beep
            print("\a")  # Terminal bell
    
    def _show_desktop_notification(self, timestamp):
        """Show desktop notification"""
        try:
            import plyer
            plyer.notification.notify(
                title="Motion Detected!",
                message=f"Security alert at {timestamp.strftime('%H:%M:%S')}",
                timeout=5
            )
        except ImportError:
            print(f"📢 DESKTOP ALERT: Motion detected at {timestamp.strftime('%H:%M:%S')}")
    
    def add_overlay_info(self, frame):
        """Add overlay information to frame"""
        if frame is None:
            return frame
        
        # Add timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cv2.putText(frame, timestamp, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Add camera source
        source = "Mobile Camera" if self.using_mobile else "Webcam"
        cv2.putText(frame, source, (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        # Add frame count and stats
        cv2.putText(frame, f"Frame: {self.frame_count}", (10, 90), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        cv2.putText(frame, f"Alerts: {self.stats['alerts_triggered']}", (10, 120), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Add resolution info
        height, width = frame.shape[:2]
        cv2.putText(frame, f"Resolution: {width}x{height}", (10, 150), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return frame
    
    def run(self):
        """Main motion detection loop"""
        print("🚀 Starting Motion Detection Security System")
        print("=" * 60)
        
        # Initialize camera
        if not self.initialize_camera():
            print("❌ Failed to initialize camera")
            return
        
        print("✅ Camera initialized successfully")
        print("🎥 Motion detection active")
        print("📱 Press 'q' to quit, 's' to show stats")
        print("=" * 60)
        
        try:
            while True:
                # Read frame
                ret, frame = self.read_frame()
                if not ret or frame is None:
                    print("⚠️  No frame received, retrying...")
                    time.sleep(0.1)
                    continue
                
                self.frame_count += 1
                self.stats['total_frames'] += 1
                
                # Process motion detection
                motion_detected, processed_frame = self.process_motion_detection(frame)
                
                if motion_detected:
                    self.stats['motion_detected'] += 1
                    self.handle_motion_alert(processed_frame)
                
                # Add overlay information
                display_frame = self.add_overlay_info(processed_frame)
                
                # Display frame
                cv2.imshow('Motion Detection Security System', display_frame)
                
                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("🛑 Quit requested")
                    break
                elif key == ord('s'):
                    self._print_stats()
                
                # Control frame rate
                time.sleep(0.03)  # ~30 FPS max
                
        except KeyboardInterrupt:
            print("\n🛑 Interrupted by user")
        except Exception as e:
            print(f"❌ Error in main loop: {e}")
        finally:
            self.cleanup()
    
    def _print_stats(self):
        """Print current statistics"""
        print("\n📊 STATISTICS")
        print("=" * 30)
        print(f"Total Frames: {self.stats['total_frames']}")
        print(f"Motion Detected: {self.stats['motion_detected']}")
        print(f"Alerts Triggered: {self.stats['alerts_triggered']}")
        print(f"Frames Saved: {self.stats['frames_saved']}")
        if self.stats['total_frames'] > 0:
            motion_rate = (self.stats['motion_detected'] / self.stats['total_frames']) * 100
            print(f"Motion Rate: {motion_rate:.2f}%")
        print("=" * 30)
    
    def cleanup(self):
        """Clean up resources"""
        print("🧹 Cleaning up resources...")
        
        # Stop mobile camera
        if self.mobile_cam:
            self.mobile_cam.stop_streaming()
            print("📱 Mobile camera stream stopped")
        
        # Release webcam
        if self.cap:
            self.cap.release()
            print("🎥 Webcam released")
        
        # Close windows
        cv2.destroyAllWindows()
        
        # Print final stats
        self._print_stats()
        print("✅ Cleanup completed")


def main():
    """Main function"""
    print("🔐 Motion Detection Security System with Mobile Camera")
    print("=" * 60)
    
    # Create and run motion detection system
    motion_detector = MotionDetectionMobile()
    motion_detector.run()


if __name__ == "__main__":
    main()
