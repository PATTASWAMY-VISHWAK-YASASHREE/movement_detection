#!/usr/bin/env python3
"""
Motion Detection Security System

A real-time security system that uses computer vision to detect motion
and alert users through multiple notification methods.

Controls:
- SPACE: Start/Stop monitoring
- S: Save current frame
- R: Start/Stop recording
- +/-: Adjust sensitivity
- Q: Quit application

Author: Security System
Date: 2025
"""

import cv2
import time
import threading
from datetime import datetime
import numpy as np

from camera_handler import CameraHandler
from alert_system import AlertSystem
from object_detector import ObjectDetector
import config

class MotionDetectionSystem:
    def __init__(self):
        self.camera = CameraHandler()
        self.alerts = AlertSystem()
        self.object_detector = ObjectDetector()
        self.monitoring = False
        self.running = True
        self.sensitivity = config.SENSITIVITY
        self.last_motion_time = 0
        self.recording_thread = None
        self.frame_count = 0
        
        print("🔒 Motion Detection Security System with AI Object Recognition")
        print("=" * 60)
        print("Controls:")
        print("  SPACE: Start/Stop monitoring")
        print("  S: Save current frame")
        print("  R: Start/Stop recording")
        print("  +/-: Adjust sensitivity")
        print("  O: Toggle object detection")
        print("  D: Toggle detection display mode")
        print("  Q: Quit application")
        print("=" * 60)
        
        if self.object_detector.detection_enabled:
            print("🤖 AI Object Detection: ENABLED")
        else:
            print("⚠️ AI Object Detection: DISABLED (install ultralytics)")
        
    def adjust_sensitivity(self, increase=True):
        """Adjust motion detection sensitivity"""
        if increase:
            self.sensitivity = min(100, self.sensitivity + 5)
        else:
            self.sensitivity = max(1, self.sensitivity - 5)
              # Update the config values
        config.MOTION_THRESHOLD = int(10000 * (100 - self.sensitivity) / 100)
        config.MIN_CONTOUR_AREA = int(1000 * (100 - self.sensitivity) / 100)
        
        print(f"📊 Sensitivity: {self.sensitivity}% (Threshold: {config.MOTION_THRESHOLD})")
        
    def start_monitoring(self):
        """Start motion detection monitoring"""
        self.monitoring = True
        self.alerts.system_status_alert("started")
        print("🟢 Monitoring STARTED")
        
    def stop_monitoring(self):
        """Stop motion detection monitoring"""
        self.monitoring = False
        if self.camera.is_recording:        self.camera.stop_recording()
        print("🔴 Monitoring STOPPED")
    
    def handle_motion_detection(self, motion_areas, frame=None, detected_objects=None):
        """Handle detected motion with optional object detection"""
        current_time = time.time()
        self.last_motion_time = current_time

        # Determine if this is a significant detection
        significant_detection = False
        alert_reason = "Motion detected"

        if detected_objects and config.ENABLE_OBJECT_DETECTION:
            # Check for security-relevant objects
            should_alert, priority_objects = self.object_detector.should_trigger_alert(detected_objects)
            if should_alert:
                significant_detection = True
                object_summary = self.object_detector.get_detection_summary(priority_objects)
                alert_reason = f"Security Alert: {object_summary}"
            elif not config.PRIORITY_OBJECTS_ONLY:
                # Alert for any motion with object context
                significant_detection = True
                object_summary = self.object_detector.get_detection_summary(detected_objects)
                alert_reason = f"Motion with objects: {object_summary}"
        else:
            # Standard motion detection without objects
            significant_detection = len(motion_areas) > 0

        if not significant_detection:
            return

        # Save frame if configured
        frame_saved = None
        if config.SAVE_FRAMES and frame is not None:
            frame_saved = self.camera.save_frame(frame, "motion_alert")

        # Start recording if configured and not already recording
        if config.AUTO_RECORD_ON_MOTION and not self.camera.is_recording:
            self.camera.start_recording()
            self.alerts.recording_alert("started")

            # Stop recording after configured duration
            if self.recording_thread:
                self.recording_thread.cancel()
            self.recording_thread = threading.Timer(
                config.RECORDING_DURATION, 
                self.stop_auto_recording
            )
            self.recording_thread.start()

        # Send alerts with object information
        self.alerts.motion_detected_alert(
            motion_areas_count=len(motion_areas),
            frame_saved=frame_saved,
            alert_reason=alert_reason,
            detected_objects=detected_objects
        )
        
    def stop_auto_recording(self):
        """Stop automatic recording"""
        if self.camera.is_recording:
            self.camera.stop_recording()
            self.alerts.recording_alert("stopped")
    
    def process_frame(self, frame):
        """Process a single frame for motion detection and object recognition"""
        if not self.monitoring:
            return frame, False, []
            
        # Detect motion
        motion_detected, motion_areas, mask = self.camera.detect_motion(frame)
        
        # Object detection (run every N frames for performance)
        detected_objects = []
        if (config.ENABLE_OBJECT_DETECTION and 
            self.object_detector.detection_enabled and
            self.frame_count % config.OBJECT_DETECTION_INTERVAL == 0):
            detected_objects = self.object_detector.detect_objects(
                frame, config.OBJECT_DETECTION_CONFIDENCE
            )
        
        # Handle motion detection with object context
        if motion_detected and motion_areas:
            self.handle_motion_detection(motion_areas, frame, detected_objects)
            
            # Draw motion areas if configured
            if config.SHOW_MOTION_AREAS:
                frame = self.camera.draw_motion_areas(frame, motion_areas)
        
        # Draw object detections
        if detected_objects and config.ENABLE_OBJECT_DETECTION:
            if config.SHOW_ALL_DETECTIONS:
                frame = self.object_detector.draw_detections(frame, detected_objects)
            else:
                # Only show security-relevant objects
                security_objects = self.object_detector.filter_security_relevant(detected_objects)
                frame = self.object_detector.draw_detections(frame, security_objects)
                
        return frame, motion_detected, detected_objects
        
    def run(self):
        """Main application loop"""
        fps_counter = 0
        fps_start_time = time.time()
        current_fps = 0
        
        try:
            while self.running:
                # Get frame from camera
                frame = self.camera.get_frame()
                if frame is None:
                    print("❌ Error: Could not read from camera")
                    break
                      # Process frame for motion detection and object recognition
                frame, motion_detected, detected_objects = self.process_frame(frame)
                
                # Update frame counter
                self.frame_count += 1
                
                # Add overlay information
                frame = self.camera.add_overlay_info(frame, motion_detected, current_fps)
                
                # Record frame if recording
                if self.camera.is_recording:
                    self.camera.record_frame(frame)
                    
                # Calculate FPS
                fps_counter += 1
                if fps_counter >= 30:
                    current_fps = fps_counter / (time.time() - fps_start_time)
                    fps_counter = 0
                    fps_start_time = time.time()
                    
                # Display frame
                cv2.imshow('Motion Detection Security System', frame)
                
                # Show threshold view if configured
                if config.SHOW_THRESHOLD_VIEW and self.monitoring:
                    _, _, mask = self.camera.detect_motion(frame)
                    if mask is not None:
                        cv2.imshow('Motion Threshold', mask)
                
                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q') or key == 27:  # Q or ESC
                    break
                elif key == ord(' '):  # SPACE
                    if self.monitoring:
                        self.stop_monitoring()
                    else:
                        self.start_monitoring()
                elif key == ord('s'):  # S
                    self.camera.save_frame(frame, "manual_save")
                elif key == ord('r'):  # R
                    if self.camera.is_recording:
                        self.camera.stop_recording()
                        self.alerts.recording_alert("stopped")
                    else:
                        self.camera.start_recording()
                        self.alerts.recording_alert("started")
                elif key == ord('+') or key == ord('='):  # +
                    self.adjust_sensitivity(increase=True)
                elif key == ord('-'):  # -
                        self.adjust_sensitivity(increase=False)
                elif key == ord('h'):  # H for help
                        self.show_help()
                elif key == ord('o'):  # O for object detection toggle
                    config.ENABLE_OBJECT_DETECTION = not config.ENABLE_OBJECT_DETECTION
                    status = "ENABLED" if config.ENABLE_OBJECT_DETECTION else "DISABLED"
                    print(f"🤖 Object Detection: {status}")
                elif key == ord('d'):  # D for detection display toggle
                    config.SHOW_ALL_DETECTIONS = not config.SHOW_ALL_DETECTIONS
                    mode = "ALL objects" if config.SHOW_ALL_DETECTIONS else "SECURITY objects only"
                    print(f"👁️ Display Mode: {mode}")
                    
        except KeyboardInterrupt:
            print("\n🛑 System interrupted by user")
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            self.cleanup()
    def show_help(self):
        """Display help information"""
        print("\n" + "=" * 60)
        print("🔒 MOTION DETECTION SECURITY SYSTEM WITH AI HELP")
        print("=" * 60)
        print("Controls:")
        print("  SPACE: Start/Stop monitoring")
        print("  S: Save current frame")
        print("  R: Start/Stop recording")
        print("  +/-: Adjust sensitivity")
        print("  O: Toggle object detection ON/OFF")
        print("  D: Toggle detection display (All vs Security only)")
        print("  H: Show this help")
        print("  Q: Quit application")
        print("\nStatus:")
        print(f"  Monitoring: {'🟢 ON' if self.monitoring else '🔴 OFF'}")
        print(f"  Recording: {'🔴 ON' if self.camera.is_recording else '⚪ OFF'}")
        print(f"  Sensitivity: {self.sensitivity}%")
        print(f"  Object Detection: {'🤖 ON' if config.ENABLE_OBJECT_DETECTION else '❌ OFF'}")
        print(f"  Display Mode: {'👁️ All Objects' if config.SHOW_ALL_DETECTIONS else '🔒 Security Only'}")
        print(f"  AI Model: {'✅ Loaded' if self.object_detector.detection_enabled else '❌ Not Available'}")
        print("=" * 60 + "\n")
        
    def cleanup(self):
        """Clean up resources"""
        print("\n🧹 Cleaning up...")
        self.running = False
        
        if self.recording_thread:
            self.recording_thread.cancel()
            
        self.camera.cleanup()
        self.alerts.system_status_alert("stopped")
        self.alerts.cleanup_old_logs()
        
        print("✅ Cleanup complete")

def main():
    """Main entry point"""
    print("🚀 Starting Motion Detection Security System...")
    
    try:
        system = MotionDetectionSystem()
        system.run()
    except Exception as e:
        print(f"❌ Failed to start system: {e}")
        print("💡 Make sure your camera is connected and not being used by another application")

if __name__ == "__main__":
    main()
