#!/usr/bin/env python3
"""
Wireless Camera Server for Motion Detection Security System

This server allows any device on the same WiFi network to contribute camera feeds
to the motion detection security system. Devices connect via web browser and
stream their camera feed to the server.

Features:
- Web interface for devices to enable their cameras
- Real-time image capture from browsers using WebRTC/getUserMedia
- Base64 image processing and PostgreSQL storage
- Device management and discovery
- Live updates to web viewer
- Security measures for camera connections
- Support for multiple simultaneous camera feeds

Author: Motion Detection Security System
"""

import asyncio
import base64
import json
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Set
import uuid
import socket
import cv2
import numpy as np
from flask import Flask, render_template, request, jsonify, Response
from flask_socketio import SocketIO, emit, join_room, leave_room
import psycopg2
from database_config import get_psycopg2_params, TABLES
from image_processor import ImageProcessor

# Initialize Flask app with SocketIO
app = Flask(__name__)
app.config['SECRET_KEY'] = 'wireless_camera_security_system_2025'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

class WirelessCameraServer:
    def __init__(self, host='localhost', port=3000):
        self.host = host
        self.port = port
        self.connected_devices = {}
        self.active_streams = {}
        self.motion_detection_enabled = False
        self.frame_buffer = {}
        self.image_processor = ImageProcessor()
        self.server_ip = self.get_local_ip()
        self.total_motion_alerts = 0
        
        print(f"🌐 Wireless Camera Server starting...")
        print(f"📡 Server IP: {self.server_ip}")
        print(f"🔌 Port: {self.port}")
        print(f"🌍 Access via: http://localhost:{self.port}")
        print(f"📱 Mobile QR Code available on dashboard")
        self.stats = {
            'total_devices': 0,
            'active_streams': 0,
            'frames_processed': 0,
            'motion_alerts': 0
        }
        
        # Motion detection parameters
        self.background_subtractor = cv2.createBackgroundSubtractorMOG2(
            detectShadows=True, varThreshold=50, history=500
        )
        self.min_contour_area = 500
        self.motion_threshold = 0.02
        
        # Security settings
        self.allowed_networks = ['192.168.', '10.0.', '172.16.']  # Common private networks
        self.max_connections_per_ip = 3
        self.connection_count = {}
        
        print(f"🌐 Wireless Camera Server initializing on {self.host}:{self.port}")

    def get_local_ip(self):
        """Get local IP address for device connections"""
        return "localhost"

    def get_server_ip(self):
        """Get server IP address for device connections (deprecated - use get_local_ip)"""
        return self.get_local_ip()

    def is_authorized_network(self, ip_address: str) -> bool:
        """Check if IP address is from allowed network"""
        return any(ip_address.startswith(network) for network in self.allowed_networks)

    def can_accept_connection(self, ip_address: str) -> bool:
        """Check if we can accept new connection from this IP"""
        current_count = self.connection_count.get(ip_address, 0)
        return current_count < self.max_connections_per_ip

    def register_device(self, device_id: str, device_info: dict, ip_address: str) -> bool:
        """Register a new device"""
        if not self.is_authorized_network(ip_address):
            print(f"❌ Unauthorized network: {ip_address}")
            return False
            
        if not self.can_accept_connection(ip_address):
            print(f"❌ Too many connections from: {ip_address}")
            return False

        self.connected_devices[device_id] = {
            'id': device_id,
            'ip': ip_address,
            'connected_at': datetime.now(),
            'last_frame': None,
            'frame_count': 0,
            'is_streaming': False,
            **device_info
        }
        
        # Update connection count
        self.connection_count[ip_address] = self.connection_count.get(ip_address, 0) + 1
        self.stats['total_devices'] += 1
        
        print(f"📱 Device registered: {device_id} from {ip_address}")
        return True

    def unregister_device(self, device_id: str):
        """Unregister a device"""
        if device_id in self.connected_devices:
            device = self.connected_devices[device_id]
            ip_address = device['ip']
            
            # Update connection count
            if ip_address in self.connection_count:
                self.connection_count[ip_address] -= 1
                if self.connection_count[ip_address] <= 0:
                    del self.connection_count[ip_address]
            
            # Stop streaming if active
            if device_id in self.active_streams:
                self.stop_device_stream(device_id)
            
            del self.connected_devices[device_id]
            print(f"📱 Device unregistered: {device_id}")

    def start_device_stream(self, device_id: str) -> bool:
        """Start streaming from a device"""
        if device_id not in self.connected_devices:
            return False
            
        self.active_streams[device_id] = {
            'started_at': datetime.now(),
            'frame_count': 0,
            'last_frame_time': None
        }
        
        self.connected_devices[device_id]['is_streaming'] = True
        self.stats['active_streams'] = len(self.active_streams)
        
        print(f"🎥 Stream started: {device_id}")
        return True

    def stop_device_stream(self, device_id: str):
        """Stop streaming from a device"""
        if device_id in self.active_streams:
            del self.active_streams[device_id]
            
        if device_id in self.connected_devices:
            self.connected_devices[device_id]['is_streaming'] = False
            
        if device_id in self.frame_buffer:
            del self.frame_buffer[device_id]
            
        self.stats['active_streams'] = len(self.active_streams)
        print(f"🛑 Stream stopped: {device_id}")

    def process_frame(self, device_id: str, frame_data: str) -> bool:
        """Process incoming frame from device"""
        try:
            # Decode base64 image
            image_data = base64.b64decode(frame_data.split(',')[1])  # Remove data:image/jpeg;base64,
            nparr = np.frombuffer(image_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None:
                return False
            
            # Update device info
            if device_id in self.connected_devices:
                self.connected_devices[device_id]['last_frame'] = datetime.now()
                self.connected_devices[device_id]['frame_count'] += 1
            
            if device_id in self.active_streams:
                self.active_streams[device_id]['frame_count'] += 1
                self.active_streams[device_id]['last_frame_time'] = datetime.now()
            
            # Store frame for motion detection
            self.frame_buffer[device_id] = frame
            self.stats['frames_processed'] += 1
            
            # Perform motion detection if enabled
            if self.motion_detection_enabled:
                self.detect_motion(device_id, frame)
            
            return True
            
        except Exception as e:
            print(f"❌ Frame processing error for {device_id}: {e}")
            return False

    def detect_motion(self, device_id: str, frame: np.ndarray):
        """Detect motion in frame and save alerts"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Apply background subtraction
            fg_mask = self.background_subtractor.apply(gray)
            
            # Find contours
            contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter significant contours
            motion_areas = [c for c in contours if cv2.contourArea(c) > self.min_contour_area]
            
            if len(motion_areas) > 0:
                # Calculate motion percentage
                motion_pixels = cv2.countNonZero(fg_mask)
                total_pixels = fg_mask.shape[0] * fg_mask.shape[1]
                motion_percentage = motion_pixels / total_pixels
                
                if motion_percentage > self.motion_threshold:
                    self.save_motion_alert(device_id, frame, motion_areas, motion_percentage)
                    
        except Exception as e:
            print(f"❌ Motion detection error for {device_id}: {e}")

    def save_motion_alert(self, device_id: str, frame: np.ndarray, motion_areas: List, motion_percentage: float):
        """Save motion alert to database"""
        try:
            timestamp = datetime.now()
            
            # Draw motion areas on frame
            alert_frame = frame.copy()
            for contour in motion_areas:
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(alert_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Add text overlay
            cv2.putText(alert_frame, f"MOTION DETECTED - {device_id}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(alert_frame, f"Areas: {len(motion_areas)} | Motion: {motion_percentage:.1%}", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Convert to base64
            success, buffer = cv2.imencode('.jpg', alert_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if success:
                image_base64 = base64.b64encode(buffer).decode('utf-8')
                
                # Save to database
                alert_id = self.image_processor.save_alert_with_image(
                    timestamp=timestamp,
                    image_base64=image_base64,
                    camera_source=f'wireless-{device_id}',
                    motion_confidence=motion_percentage,
                    motion_areas_count=len(motion_areas)
                )
                
                if alert_id:
                    self.stats['motion_alerts'] += 1
                    print(f"🚨 Motion alert saved: {device_id} (Areas: {len(motion_areas)})")
                    
                    # Notify connected web viewers
                    socketio.emit('motion_alert', {
                        'device_id': device_id,
                        'timestamp': timestamp.isoformat(),
                        'motion_areas': len(motion_areas),
                        'motion_percentage': motion_percentage,
                        'alert_id': alert_id
                    }, room='viewers')
                    
        except Exception as e:
            print(f"❌ Alert save error for {device_id}: {e}")

    def get_device_stats(self) -> dict:
        """Get server and device statistics"""
        return {
            'server': {
                'host': self.host,
                'port': self.port,
                'ip': self.get_server_ip(),
                'uptime': time.time(),
                **self.stats
            },
            'devices': self.connected_devices,
            'streams': self.active_streams,
            'motion_detection': self.motion_detection_enabled
        }

# Global server instance
camera_server = WirelessCameraServer()

# Flask Routes
@app.route('/')
def index():
    """Main dashboard"""
    server_ip = camera_server.get_server_ip()
    return render_template('wireless_dashboard.html', 
                         server_ip=server_ip, 
                         server_port=camera_server.port)

@app.route('/camera')
def camera_interface():
    """Camera interface for devices"""
    server_ip = camera_server.get_server_ip()
    return render_template('wireless_camera.html', 
                         server_ip=server_ip, 
                         server_port=camera_server.port)

@app.route('/test')
def camera_test():
    """Camera test and troubleshooting page"""
    return render_template('camera_test.html')

@app.route('/api/test-camera')
def api_test_camera():
    """API endpoint to test camera connectivity"""
    return jsonify({
        'server_status': 'online',
        'timestamp': datetime.now().isoformat(),
        'https_required': True,
        'supported_browsers': ['Chrome', 'Firefox', 'Safari', 'Edge']
    })

@app.route('/viewer')
def viewer_interface():
    """Live viewer interface"""
    return render_template('wireless_viewer.html')

@app.route('/api/stats')
def api_stats():
    """Get server statistics"""
    return jsonify(camera_server.get_device_stats())

@app.route('/api/devices')
def api_devices():
    """Get connected devices"""
    return jsonify({
        'devices': camera_server.connected_devices,
        'active_streams': camera_server.active_streams
    })

@app.route('/api/motion/toggle', methods=['POST'])
def api_toggle_motion():
    """Toggle motion detection"""
    camera_server.motion_detection_enabled = not camera_server.motion_detection_enabled
    return jsonify({
        'motion_detection': camera_server.motion_detection_enabled,
        'message': f"Motion detection {'enabled' if camera_server.motion_detection_enabled else 'disabled'}"
    })

# SocketIO Events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    client_ip = request.environ.get('REMOTE_ADDR', 'unknown')
    print(f"🔌 Client connected from {client_ip}")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    client_ip = request.environ.get('REMOTE_ADDR', 'unknown')
    print(f"🔌 Client disconnected from {client_ip}")

@socketio.on('register_device')
def handle_register_device(data):
    """Register a new camera device"""
    client_ip = request.environ.get('REMOTE_ADDR', 'unknown')
    device_id = data.get('device_id', str(uuid.uuid4()))
    device_info = data.get('device_info', {})
    
    success = camera_server.register_device(device_id, device_info, client_ip)
    
    emit('registration_response', {
        'success': success,
        'device_id': device_id,
        'message': 'Device registered successfully' if success else 'Registration failed'
    })

@socketio.on('unregister_device')
def handle_unregister_device(data):
    """Unregister a camera device"""
    device_id = data.get('device_id')
    if device_id:
        camera_server.unregister_device(device_id)
        emit('unregistration_response', {'success': True})

@socketio.on('start_stream')
def handle_start_stream(data):
    """Start camera stream from device"""
    device_id = data.get('device_id')
    if device_id:
        success = camera_server.start_device_stream(device_id)
        emit('stream_response', {
            'success': success,
            'streaming': success,
            'message': 'Stream started' if success else 'Failed to start stream'
        })

@socketio.on('stop_stream')
def handle_stop_stream(data):
    """Stop camera stream from device"""
    device_id = data.get('device_id')
    if device_id:
        camera_server.stop_device_stream(device_id)
        emit('stream_response', {
            'success': True,
            'streaming': False,
            'message': 'Stream stopped'
        })

@socketio.on('camera_frame')
def handle_camera_frame(data):
    """Process incoming camera frame"""
    device_id = data.get('device_id')
    frame_data = data.get('frame_data')
    
    if device_id and frame_data:
        success = camera_server.process_frame(device_id, frame_data)
        if not success:
            emit('frame_error', {'message': 'Frame processing failed'})

@socketio.on('join_viewers')
def handle_join_viewers():
    """Join viewers room for live updates"""
    join_room('viewers')
    emit('joined_viewers', {'message': 'Joined live updates'})

@socketio.on('leave_viewers')
def handle_leave_viewers():
    """Leave viewers room"""
    leave_room('viewers')

def run_server():
    """Run the wireless camera server"""
    try:
        server_ip = camera_server.get_server_ip()
        print(f"\n🌐 Wireless Camera Server Starting...")
        print(f"📱 Device Camera Interface: http://{server_ip}:{camera_server.port}/camera")
        print(f"👁️  Live Viewer Interface: http://{server_ip}:{camera_server.port}/viewer")
        print(f"📊 Dashboard: http://{server_ip}:{camera_server.port}/")
        print(f"\n📋 Setup Instructions:")
        print(f"   1. Connect devices to the same WiFi network")
        print(f"   2. Open camera interface on devices: http://{server_ip}:{camera_server.port}/camera")
        print(f"   3. Allow camera permissions and start streaming")
        print(f"   4. View live feeds: http://{server_ip}:{camera_server.port}/viewer")
        print(f"   5. Enable motion detection from dashboard")
        print(f"\n🔒 Security: Only devices on private networks can connect")
        print(f"🎯 Ready to accept wireless camera connections...\n")
        
        socketio.run(app, host=camera_server.host, port=camera_server.port, debug=False)
        
    except Exception as e:
        print(f"❌ Server error: {e}")

if __name__ == "__main__":
    run_server()
