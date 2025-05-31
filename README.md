# Motion Detection Security System

A real-time motion detection security system that uses your laptop camera to monitor for movement and send alerts.

## Features

- **Real-time Motion Detection**: Uses computer vision to detect movement in camera feed
- **Alert System**: Visual and audio notifications when motion is detected
- **Recording Capability**: Automatically records video when motion is detected
- **Sensitivity Controls**: Adjustable motion detection sensitivity
- **Multiple Alert Types**: Desktop notifications, sound alerts, and visual warnings
- **Security Dashboard**: Live camera feed with motion indicators
- **Wireless Camera Support**: Connect mobile phones as additional cameras
- **Network Access**: Monitor your security system from any device on the network
- **QR Code Connection**: Easily connect mobile devices using QR codes

## Installation

### Easy Installation (Recommended)

#### Windows:
1. Double-click `install_windows.bat`
2. Follow the on-screen instructions

#### Linux/macOS:
1. Open terminal in the project directory
2. Run: `chmod +x install_linux_mac.sh`
3. Run: `./install_linux_mac.sh`
4. Follow the on-screen instructions

### Manual Installation

1. Ensure Python 3.7+ is installed
2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Verify installation:
```bash
python verify_dependencies.py
```

4. Run the security system:
```bash
python start_system.py --all
```

## Network Access & Mobile Devices

You can access the security system from any device on your local network:

1. **Web Dashboard**: Access at `http://<your-ip-address>:5000`
2. **Mobile Camera Connection**: Connect your phone's camera at `http://<your-ip-address>:3000/camera`
3. **Wireless Camera Dashboard**: View all connected cameras at `http://<your-ip-address>:3000/viewer-with-qr`

To connect mobile devices:
- Ensure all devices are on the same WiFi network
- Scan the QR code from the wireless camera dashboard
- Grant camera permissions when prompted
- Keep the browser tab open to continue streaming

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
