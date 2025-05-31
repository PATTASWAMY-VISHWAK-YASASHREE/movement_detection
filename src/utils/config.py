# Configuration settings for Motion Detection Security System

# Camera settings
CAMERA_INDEX = 0  # Default camera (usually laptop webcam)
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FPS = 30

# Mobile Camera settings (NEW)
USE_MOBILE_CAMERA = False  # Set to True to use mobile camera instead of webcam
MOBILE_CAMERA_MAX_RESOLUTION = (640, 480)  # 420p equivalent for performance
MOBILE_CAMERA_PREFERRED_METHOD = "auto"  # "auto", "scrcpy", "screenshot", "ip_webcam"
MOBILE_DEVICE_ID = None  # Specific device ID, or None for auto-detect

# Motion detection parameters
MOTION_THRESHOLD = 15000  # Minimum area for motion detection (increased)
SENSITIVITY = 30  # Motion detection sensitivity (1-100) (decreased for less sensitivity)
BLUR_SIZE = 25  # Gaussian blur kernel size (increased to filter more noise)
MIN_CONTOUR_AREA = 2000  # Minimum contour area to consider as motion (significantly increased)
MAX_CONTOUR_AREA = 50000  # Maximum contour area to avoid detecting entire frame
MIN_MOTION_WIDTH = 50  # Minimum width of motion area
MIN_MOTION_HEIGHT = 50  # Minimum height of motion area
MOTION_DENSITY_THRESHOLD = 0.3  # Minimum density of motion within bounding box

# Alert settings
ENABLE_SOUND_ALERTS = True
ENABLE_DESKTOP_NOTIFICATIONS = True
ENABLE_VISUAL_ALERTS = True
ALERT_COOLDOWN = 5  # Seconds between alerts

# Recording settings
AUTO_RECORD_ON_MOTION = True
RECORDING_DURATION = 10  # Seconds to record after motion detection
SAVE_FRAMES = True
MAX_RECORDINGS = 50  # Maximum number of recordings to keep

# File paths
RECORDINGS_DIR = "recordings"
ALERTS_DIR = "recordings/alerts"
BACKGROUND_UPDATE_RATE = 0.01  # Rate at which background model updates

# Display settings
SHOW_MOTION_AREAS = True
SHOW_THRESHOLD_VIEW = False
DISPLAY_FPS = True

# Object Detection settings
ENABLE_OBJECT_DETECTION = True
OBJECT_DETECTION_CONFIDENCE = 0.5  # Confidence threshold for object detection
OBJECT_DETECTION_INTERVAL = 3  # Analyze every N frames (for performance)
PRIORITY_OBJECTS_ONLY = True  # Only alert for high-priority security objects
SHOW_ALL_DETECTIONS = True  # Show all detected objects or only security-relevant ones
