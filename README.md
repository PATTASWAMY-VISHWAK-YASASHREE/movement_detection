# Motion Detection Security System

A real-time motion detection security system that uses your laptop camera to monitor for movement and send alerts.

## Features

- **Real-time Motion Detection**: Uses computer vision to detect movement in camera feed
- **Alert System**: Visual and audio notifications when motion is detected
- **Recording Capability**: Automatically records video when motion is detected
- **Sensitivity Controls**: Adjustable motion detection sensitivity
- **Multiple Alert Types**: Desktop notifications, sound alerts, and visual warnings
- **Security Dashboard**: Live camera feed with motion indicators

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Run the security system:
```bash
python motion_detector.py
```

## Controls

- **Space**: Start/Stop monitoring
- **S**: Save current frame
- **R**: Start/Stop recording
- **+/-**: Adjust sensitivity
- **Q**: Quit application

## Project Structure

```
motion-security-system/
├── motion_detector.py      # Main application
├── alert_system.py         # Notification handlers
├── camera_handler.py       # Camera operations
├── config.py              # Configuration settings
├── requirements.txt        # Dependencies
└── recordings/            # Saved recordings
    └── alerts/            # Motion detection alerts
```

## How It Works

1. **Camera Feed**: Captures live video from your laptop camera
2. **Background Subtraction**: Compares current frame with background model
3. **Motion Analysis**: Detects significant changes between frames
4. **Alert Triggering**: Sends notifications when motion exceeds threshold
5. **Recording**: Saves video clips of detected motion events
