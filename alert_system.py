import threading
import time
import os
from datetime import datetime
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    
try:
    from plyer import notification
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False

import config

class AlertSystem:
    def __init__(self):
        self.last_alert_time = 0
        self.setup_sound()
        
    def setup_sound(self):
        """Initialize pygame for sound alerts"""
        if PYGAME_AVAILABLE and config.ENABLE_SOUND_ALERTS:
            try:
                pygame.mixer.init()
                self.sound_initialized = True
            except:
                self.sound_initialized = False
                print("Warning: Could not initialize sound system")
        else:
            self.sound_initialized = False
            
    def can_send_alert(self):
        """Check if enough time has passed since last alert"""
        current_time = time.time()
        if current_time - self.last_alert_time >= config.ALERT_COOLDOWN:
            self.last_alert_time = current_time
            return True
        return False
        
    def play_alert_sound(self):
        """Play alert sound"""
        if not self.sound_initialized or not config.ENABLE_SOUND_ALERTS:
            return
            
        try:
            # Generate a simple beep sound
            sample_rate = 22050
            duration = 0.5
            frequency = 800
            
            # Create beep sound array
            import numpy as np
            frames = int(duration * sample_rate)
            arr = np.zeros(frames)
            
            for i in range(frames):
                arr[i] = np.sin(2 * np.pi * frequency * i / sample_rate)
            
            # Convert to pygame sound
            arr = (arr * 32767).astype(np.int16)
            stereo_arr = np.zeros((frames, 2), dtype=np.int16)
            stereo_arr[:, 0] = arr
            stereo_arr[:, 1] = arr
            
            sound = pygame.sndarray.make_sound(stereo_arr)
            sound.play()
            
        except Exception as e:
            print(f"Error playing sound: {e}")
            # Fallback to system beep
            print("\a")  # ASCII bell character
            
    def send_desktop_notification(self, title="Security Alert", message="Motion detected!"):
        """Send desktop notification"""
        if not PLYER_AVAILABLE or not config.ENABLE_DESKTOP_NOTIFICATIONS:
            print(f"ALERT: {title} - {message}")
            return
            
        try:
            notification.notify(
                title=title,
                message=message,
                app_name="Motion Security System",
                timeout=5
            )
        except Exception as e:
            print(f"Error sending notification: {e}")
            print(f"ALERT: {title} - {message}")
            
    def log_alert(self, alert_type="motion", details=""):
        """Log alert to file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {alert_type.upper()}: {details}\n"
        
        log_file = os.path.join(config.ALERTS_DIR, "security_log.txt")
        with open(log_file, "a") as f:
            f.write(log_entry)

    def motion_detected_alert(self, motion_areas_count=0, frame_saved=None, alert_reason="Motion detected", detected_objects=None):
        """Trigger all alerts for motion detection with optional object information"""
        if not self.can_send_alert():
            return
            
            # Prepare alert details
            details = f"{alert_reason}, Motion areas: {motion_areas_count}"
            if frame_saved:
                details += f", Frame saved: {frame_saved}"
            if detected_objects:
                object_count = len(detected_objects)
                details += f", Objects detected: {object_count}"
                
            # Log the alert
            self.log_alert("motion", details)
            
            # Visual alert (console)
            print(f"\n🚨 {alert_reason.upper()} 🚨")
            print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
            print(f"Motion Areas: {motion_areas_count}")
            
            if detected_objects:
                print(f"Objects Detected: {len(detected_objects)}")
                for obj in detected_objects[:3]:  # Show up to 3 objects
                    confidence = obj.get('confidence', 0)
                    class_name = obj.get('class_name', 'unknown')
                    print(f"  • {class_name} ({confidence:.2f})")
                if len(detected_objects) > 3:
                    print(f"  • ... and {len(detected_objects) - 3} more")
                    
            if frame_saved:
                print(f"Frame saved: {frame_saved}")
            print("-" * 50)
            
            # Sound alert
            if config.ENABLE_SOUND_ALERTS:
                threading.Thread(target=self.play_alert_sound, daemon=True).start()
                
            # Desktop notification
            if config.ENABLE_DESKTOP_NOTIFICATIONS:
                if detected_objects:
                    object_summary = ", ".join([obj['class_name'] for obj in detected_objects[:2]])
                    if len(detected_objects) > 2:
                        object_summary += f" (+{len(detected_objects)-2} more)"
                    message = f"{alert_reason} - Objects: {object_summary} at {datetime.now().strftime('%H:%M:%S')}"
                else:
                    message = f"{alert_reason} in {motion_areas_count} area(s) at {datetime.now().strftime('%H:%M:%S')}"
                    
                title = "🤖 AI Security Alert" if detected_objects else "🚨 Motion Alert"
                threading.Thread(
                    target=self.send_desktop_notification,
                    args=(title, message),
                    daemon=True
                ).start()
            
    def system_status_alert(self, status="started"):
        """Alert for system status changes"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if status == "started":
            message = f"Motion detection system started at {timestamp}"
            title = "🔒 Security System Active"
        elif status == "stopped":
            message = f"Motion detection system stopped at {timestamp}"
            title = "⏹️ Security System Stopped"
        else:
            message = f"System status: {status} at {timestamp}"
            title = "ℹ️ Security System Update"
            
        self.log_alert("system", f"Status: {status}")
        
        if config.ENABLE_DESKTOP_NOTIFICATIONS:
            threading.Thread(
                target=self.send_desktop_notification,
                args=(title, message),
                daemon=True
            ).start()
            
    def recording_alert(self, action="started", filename=None):
        """Alert for recording events"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if action == "started":
            message = f"Recording started at {timestamp}"
            if filename:
                message += f"\nFile: {os.path.basename(filename)}"
            title = "🔴 Recording Started"
        elif action == "stopped":
            message = f"Recording stopped at {timestamp}"
            title = "⏹️ Recording Stopped"
        else:
            message = f"Recording {action} at {timestamp}"
            title = "📹 Recording Update"
            
        details = f"Recording {action}"
        if filename:
            details += f", File: {filename}"
        self.log_alert("recording", details)
        
        print(f"📹 {message}")
        
    def cleanup_old_logs(self, max_age_days=30):
        """Clean up old log files"""
        try:
            log_file = os.path.join(config.ALERTS_DIR, "security_log.txt")
            if os.path.exists(log_file):
                # For simplicity, we'll just truncate if file gets too large
                if os.path.getsize(log_file) > 1024 * 1024:  # 1MB
                    with open(log_file, "w") as f:
                        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Log file reset - too large\n")
        except Exception as e:
            print(f"Error cleaning up logs: {e}")
