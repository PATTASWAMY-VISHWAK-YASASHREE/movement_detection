#!/usr/bin/env python3
"""
Mobile Camera Handler for Motion Detection Security System

Uses Android phone camera via ADB (USB Debugging) to capture video frames
for motion detection. Supports resolution limiting and mobile device management.

Requirements:
- Android phone with USB debugging enabled
- ADB (Android Debug Bridge) installed
- Phone connected via USB cable

Author: Motion Detection Security System
"""

import cv2
import numpy as np
import subprocess
import time
import os
import threading
from datetime import datetime
import json
import tempfile
import requests
from PIL import Image
import io

class MobileCameraHandler:
    def __init__(self, max_resolution=(640, 480)):
        """
        Initialize Mobile Camera Handler
        
        Args:
            max_resolution (tuple): Maximum resolution (width, height) - default 420p equivalent
        """
        self.max_resolution = max_resolution
        self.device_id = None
        self.is_connected = False
        self.is_streaming = False
        self.frame = None
        self.cap = None
        self.adb_path = self.find_adb()
        self.scrcpy_available = False
        self.temp_dir = tempfile.mkdtemp()
        
        print(f"🔧 Mobile Camera Handler initialized with max resolution: {max_resolution}")
        
    def find_adb(self):
        """Find ADB executable in system PATH or common locations"""
        common_paths = [
            "adb",  # If in PATH
            "C:\\platform-tools\\adb.exe",
            "C:\\Android\\Sdk\\platform-tools\\adb.exe",
            "C:\\Users\\%USERNAME%\\AppData\\Local\\Android\\Sdk\\platform-tools\\adb.exe",
            os.path.expandvars("C:\\Users\\%USERNAME%\\AppData\\Local\\Android\\Sdk\\platform-tools\\adb.exe")
        ]
        
        for path in common_paths:
            try:
                result = subprocess.run([path, "version"], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    print(f"✅ Found ADB at: {path}")
                    return path
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                continue
        
        print("⚠️  ADB not found. Please install Android SDK Platform Tools")
        print("📋 Download from: https://developer.android.com/studio/releases/platform-tools")
        return None
    
    def check_devices(self):
        """Check for connected Android devices"""
        if not self.adb_path:
            return []
        
        try:
            result = subprocess.run([self.adb_path, "devices"], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                devices = []
                for line in lines:
                    if line.strip() and '\tdevice' in line:
                        device_id = line.split('\t')[0]
                        devices.append(device_id)
                        print(f"📱 Found device: {device_id}")
                
                return devices
            else:
                print(f"❌ ADB error: {result.stderr}")
                return []
                
        except subprocess.TimeoutExpired:
            print("⏰ ADB command timed out")
            return []
        except Exception as e:
            print(f"❌ Error checking devices: {e}")
            return []
    
    def connect_device(self, device_id=None):
        """Connect to Android device"""
        devices = self.check_devices()
        
        if not devices:
            print("❌ No devices found. Please:")
            print("  1. Enable USB Debugging on your phone")
            print("  2. Connect phone via USB cable")
            print("  3. Accept USB debugging prompt on phone")
            print("  4. Run 'adb devices' to verify connection")
            return False
        
        if device_id and device_id in devices:
            self.device_id = device_id
        else:
            self.device_id = devices[0]  # Use first available device
        
        print(f"📱 Connected to device: {self.device_id}")
        self.is_connected = True
        
        # Check camera permissions and capabilities
        self.check_camera_permissions()
        return True
    
    def check_camera_permissions(self):
        """Check if camera permissions are available"""
        try:
            # Check if camera service is available
            result = subprocess.run([
                self.adb_path, "-s", self.device_id, "shell",
                "pm", "list", "features"
            ], capture_output=True, text=True, timeout=10)
            
            if "android.hardware.camera" in result.stdout:
                print("✅ Camera hardware detected")
                return True
            else:
                print("⚠️  Camera hardware not detected")
                return False
                
        except Exception as e:
            print(f"⚠️  Could not check camera permissions: {e}")
            return True  # Assume available
    
    def start_camera_stream_scrcpy(self):
        """Start camera stream using scrcpy (if available)"""
        try:
            # Try to use scrcpy for better performance
            scrcpy_result = subprocess.run(["scrcpy", "--version"], 
                                         capture_output=True, text=True, timeout=5)
            if scrcpy_result.returncode == 0:
                print("✅ Scrcpy available - using for video stream")
                self.scrcpy_available = True
                
                # Start scrcpy in background for video forwarding
                self.scrcpy_process = subprocess.Popen([
                    "scrcpy", 
                    "--serial", self.device_id,
                    "--video-codec", "h264",
                    "--max-size", "640",  # Limit resolution
                    "--bit-rate", "2M",
                    "--no-audio",
                    "--window-title", "Mobile Security Camera"
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return False
    
    def start_camera_stream_screenshot(self):
        """Start camera stream using screenshot method (fallback)"""
        print("📸 Using screenshot method for camera stream")
        
        def screenshot_loop():
            while self.is_streaming:
                try:
                    # Take screenshot
                    screenshot_path = f"{self.temp_dir}/screenshot.png"
                    result = subprocess.run([
                        self.adb_path, "-s", self.device_id, "exec-out",
                        "screencap", "-p"
                    ], capture_output=True, timeout=5)
                    
                    if result.returncode == 0:
                        # Convert screenshot to OpenCV format
                        nparr = np.frombuffer(result.stdout, np.uint8)
                        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                        
                        if frame is not None:
                            # Resize to max resolution
                            frame = self.resize_frame(frame)
                            self.frame = frame
                    
                    time.sleep(0.1)  # 10 FPS to avoid overloading
                    
                except Exception as e:
                    print(f"Screenshot error: {e}")
                    time.sleep(1)
        
        # Start screenshot thread
        self.screenshot_thread = threading.Thread(target=screenshot_loop, daemon=True)
        self.screenshot_thread.start()
        return True
    
    def start_camera_stream_ip_webcam(self):
        """Start camera stream using IP Webcam app (alternative method)"""
        print("📱 Attempting IP Webcam method...")
        print("💡 Install 'IP Webcam' app and start server on your phone")
        
        # Try to detect IP Webcam server
        try:
            # Get device IP
            result = subprocess.run([
                self.adb_path, "-s", self.device_id, "shell",
                "ip", "route", "get", "1"
            ], capture_output=True, text=True, timeout=5)
            
            # Common IP Webcam ports
            ports = [8080, 8081, 8888]
            
            for port in ports:
                try:
                    # Try to access IP Webcam stream
                    url = f"http://192.168.1.100:{port}/video"  # Adjust IP as needed
                    response = requests.get(url, timeout=2)
                    if response.status_code == 200:
                        print(f"✅ Found IP Webcam at port {port}")
                        self.ip_webcam_url = url
                        return self.start_ip_webcam_capture()
                except:
                    continue
                    
        except Exception as e:
            print(f"IP Webcam detection failed: {e}")
        
        return False
    
    def start_ip_webcam_capture(self):
        """Capture from IP Webcam stream"""
        try:
            self.cap = cv2.VideoCapture(self.ip_webcam_url)
            if self.cap.isOpened():
                print("✅ IP Webcam stream connected")
                return True
        except Exception as e:
            print(f"IP Webcam capture failed: {e}")
        
        return False
    
    def resize_frame(self, frame):
        """Resize frame to maximum resolution while maintaining aspect ratio"""
        if frame is None:
            return None
        
        height, width = frame.shape[:2]
        max_width, max_height = self.max_resolution
        
        # Calculate scaling factor
        scale_w = max_width / width
        scale_h = max_height / height
        scale = min(scale_w, scale_h)
        
        if scale < 1.0:  # Only downscale, never upscale
            new_width = int(width * scale)
            new_height = int(height * scale)
            frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        return frame
    
    def start_streaming(self):
        """Start mobile camera streaming"""
        if not self.is_connected:
            print("❌ No device connected")
            return False
        
        print("🎥 Starting mobile camera stream...")
        self.is_streaming = True
        
        # Try different streaming methods in order of preference
        methods = [
            self.start_camera_stream_ip_webcam,
            self.start_camera_stream_scrcpy,
            self.start_camera_stream_screenshot
        ]
        
        for method in methods:
            try:
                if method():
                    print(f"✅ Started streaming with {method.__name__}")
                    return True
            except Exception as e:
                print(f"❌ {method.__name__} failed: {e}")
                continue
        
        print("❌ All streaming methods failed")
        self.is_streaming = False
        return False
    
    def get_frame(self):
        """Get current frame from mobile camera"""
        if not self.is_streaming:
            return None
        
        if self.cap and self.cap.isOpened():
            # IP Webcam method
            ret, frame = self.cap.read()
            if ret:
                return self.resize_frame(frame)
        
        # Screenshot method
        return self.frame
    
    def stop_streaming(self):
        """Stop mobile camera streaming"""
        print("🛑 Stopping mobile camera stream...")
        self.is_streaming = False
        
        if hasattr(self, 'scrcpy_process'):
            try:
                self.scrcpy_process.terminate()
            except:
                pass
        
        if self.cap:
            self.cap.release()
        
        # Clean up temp files
        try:
            import shutil
            shutil.rmtree(self.temp_dir)
        except:
            pass
    
    def get_device_info(self):
        """Get information about connected device"""
        if not self.is_connected:
            return {}
        
        try:
            # Get device model
            model_result = subprocess.run([
                self.adb_path, "-s", self.device_id, "shell",
                "getprop", "ro.product.model"
            ], capture_output=True, text=True, timeout=5)
            
            # Get Android version
            version_result = subprocess.run([
                self.adb_path, "-s", self.device_id, "shell",
                "getprop", "ro.build.version.release"
            ], capture_output=True, text=True, timeout=5)
            
            # Get battery level
            battery_result = subprocess.run([
                self.adb_path, "-s", self.device_id, "shell",
                "dumpsys", "battery", "|", "grep", "level"
            ], capture_output=True, text=True, timeout=5)
            
            return {
                'device_id': self.device_id,
                'model': model_result.stdout.strip() if model_result.returncode == 0 else "Unknown",
                'android_version': version_result.stdout.strip() if version_result.returncode == 0 else "Unknown",
                'battery': battery_result.stdout.strip() if battery_result.returncode == 0 else "Unknown",
                'max_resolution': self.max_resolution,
                'streaming': self.is_streaming
            }
            
        except Exception as e:
            print(f"Error getting device info: {e}")
            return {'device_id': self.device_id, 'error': str(e)}


def test_mobile_camera():
    """Test mobile camera functionality"""
    print("🧪 Testing Mobile Camera Handler")
    print("=" * 50)
    
    # Initialize handler
    mobile_cam = MobileCameraHandler(max_resolution=(640, 480))
    
    # Check for devices
    devices = mobile_cam.check_devices()
    if not devices:
        print("❌ No devices found for testing")
        return False
    
    # Connect to device
    if not mobile_cam.connect_device():
        print("❌ Failed to connect to device")
        return False
    
    # Get device info
    info = mobile_cam.get_device_info()
    print(f"📱 Device Info: {json.dumps(info, indent=2)}")
    
    # Start streaming
    if not mobile_cam.start_streaming():
        print("❌ Failed to start streaming")
        return False
    
    print("✅ Mobile camera test successful!")
    print("🎥 Streaming for 10 seconds...")
    
    # Test frame capture
    for i in range(100):  # 10 seconds at 10 FPS
        frame = mobile_cam.get_frame()
        if frame is not None:
            print(f"📸 Frame {i+1}: {frame.shape}")
            
            # Save a test frame
            if i == 50:  # Save middle frame
                cv2.imwrite("mobile_test_frame.jpg", frame)
                print("💾 Saved test frame: mobile_test_frame.jpg")
        
        time.sleep(0.1)
    
    # Stop streaming
    mobile_cam.stop_streaming()
    print("✅ Mobile camera test completed!")
    return True


if __name__ == "__main__":
    # Run test if executed directly
    test_mobile_camera()
