# Mobile Camera Setup Guide

## Overview
This guide helps you set up your mobile device (Android or iOS) as a security camera for the Motion Detection Security System. There are two methods:

1. **Wireless Web Browser Method** (Recommended) - Uses your phone's browser to stream camera feed over WiFi
2. **USB Debugging Method** - Uses ADB to connect Android phones via USB cable

## Method 1: Wireless Web Browser (All Devices)

This method works with any smartphone (Android or iOS) with a web browser and camera.

### Requirements

- Smartphone with working camera
- Modern web browser (Chrome, Safari, Firefox)
- Both computer and phone connected to the same WiFi network

### Setup Steps

1. **Start the wireless camera server** on your computer:

   ```bash
   python start_system.py --wireless
   ```

2. **Connect your mobile device**:
   
   **Option A: Scan QR Code** (Easiest)
   - On your computer, open the wireless camera dashboard: `http://<computer-ip>:3000/viewer-with-qr`
   - Use your phone's camera to scan the QR code
   - This will open the camera interface in your phone's browser
   
   **Option B: Enter URL Manually**
   - On your phone's browser, navigate to: `http://<computer-ip>:3000/camera`
   - Replace `<computer-ip>` with your computer's IP address on the WiFi network

3. **Allow camera permissions** when prompted by your browser

4. **Start the camera stream**:
   - Tap "Start Camera Stream" button on the phone interface
   - You can switch between front and rear cameras using the "Switch Camera" button

5. **View the camera feed** on your computer at:
   - `http://<computer-ip>:3000/viewer`
   - You should see your phone's camera listed among the active cameras

### Troubleshooting Wireless Connection

- **Camera Permission Denied**:  
  - Check your browser settings and ensure camera permissions are allowed
  - Try using a different browser
  - For iOS, ensure camera access is enabled in Settings

- **Cannot Connect**:  
  - Ensure both devices are on the same WiFi network
  - Try disabling any firewalls temporarily
  - Make sure you're using the correct IP address

- **Poor Performance**:  
  - Lower the resolution in the camera settings
  - Move closer to the WiFi router
  - Reduce the number of active camera streams

## Method 2: USB Debugging (Android Only)

### Prerequisites

#### 1. Android Phone Requirements
- Android 4.0+ (API level 14+)
- USB debugging capability
- USB cable for connection to PC

#### 2. PC Requirements
- Windows/Linux/macOS
- Python 3.7+
- ADB (Android Debug Bridge) installed
- USB drivers for your phone

### Step-by-Step Setup

#### Step 1: Install ADB (Android Debug Bridge)

##### Option A: Install Android SDK Platform Tools (Recommended)
1. Download from: https://developer.android.com/studio/releases/platform-tools
2. Extract to a folder (e.g., `C:\platform-tools\`)
3. Add the folder to your system PATH

##### Option B: Install via Package Manager
- **Windows (Chocolatey):** `choco install adb`
- **macOS (Homebrew):** `brew install android-platform-tools`
- **Ubuntu/Debian:** `sudo apt install android-tools-adb`

#### Step 2: Enable USB Debugging on Your Phone

1. **Enable Developer Options:**
   - Go to `Settings` > `About phone`
   - Tap `Build number` 7 times
   - You'll see "You are now a developer!"

2. **Enable USB Debugging:**
   - Go to `Settings` > `Developer options`
   - Enable `USB debugging`
   - Optionally enable `Stay awake` to keep screen on while charging

3. **Connect Phone:**
   - Connect your phone to PC via USB cable
   - When prompted, allow USB debugging for this computer
   - Check "Always allow from this computer"

#### Step 3: Test ADB Connection

Open terminal/command prompt and run:
```bash
adb devices
```

You should see your device listed like:
```
List of devices attached
ABC123DEF456    device
```

If you see "unauthorized", check your phone for the USB debugging permission dialog.

#### Step 4: Configure Motion Detection System

1. **Edit config.py:**
```python
# Enable mobile camera
USE_MOBILE_CAMERA = True

# Set resolution (420p max for performance)
MOBILE_CAMERA_MAX_RESOLUTION = (640, 480)

# Choose streaming method
MOBILE_CAMERA_PREFERRED_METHOD = "auto"  # "auto", "scrcpy", "screenshot", "ip_webcam"

# Optional: Specify device ID if you have multiple devices
MOBILE_DEVICE_ID = None  # or "ABC123DEF456"
```

2. **Install additional dependencies:**
```bash
pip install opencv-python numpy pillow requests
```

#### Step 5: Optional Enhancements

##### Install Scrcpy (Recommended for better performance)
1. Download from: https://github.com/Genymobile/scrcpy/releases
2. Extract and add to PATH
3. Test with: `scrcpy --version`

##### Install IP Webcam App (Alternative method)
1. Install "IP Webcam" from Google Play Store
2. Open app and tap "Start server"
3. Note the IP address shown (e.g., 192.168.1.100:8080)

### Usage

#### Basic Usage
```bash
python motion_detection_mobile.py
```

#### Test Mobile Camera Only
```bash
python mobile_camera_handler.py
```

#### Web Viewer for Alerts
```bash
python web_viewer_fixed.py
```
Then open: http://localhost:5000

### Troubleshooting

#### ADB Not Found
- **Error:** `ADB not found`
- **Solution:** Install Android SDK Platform Tools and add to PATH

#### No Devices Found
- **Error:** `No devices found`
- **Solutions:**
  - Enable USB debugging on phone
  - Try different USB cable
  - Install phone's USB drivers
  - Run `adb kill-server` then `adb start-server`

#### Device Unauthorized
- **Error:** `device unauthorized`
- **Solution:** Check phone for USB debugging permission dialog

#### Poor Performance
- **Solutions:**
  - Reduce resolution in config.py
  - Enable "Stay awake" in Developer options
  - Close other apps on phone
  - Use scrcpy method instead of screenshots

#### Connection Drops
- **Solutions:**
  - Use shorter USB cable
  - Enable "Stay awake" on phone
  - Disable USB power management on PC

## Performance Tips

1. **Resolution:** Lower resolution = better performance
   - 640x480 (420p) - Good balance
   - 480x320 (240p) - Better performance
   - 320x240 (144p) - Best performance

2. **Streaming Method Priority:**
   1. Scrcpy - Best performance, requires installation
   2. ADB Screenshots - Good compatibility, lower performance
   3. IP Webcam - Wireless option, requires app

3. **Phone Settings:**
   - Enable "Stay awake" in Developer options
   - Disable screen timeout while testing
   - Close unnecessary apps
   - Keep phone plugged in for power

## Security Considerations

1. **USB Debugging:** Only enable when needed, disable after use
2. **Network:** If using IP Webcam, ensure secure network
3. **Storage:** Alert images are stored in database, review regularly

## Advanced Configuration

### Multiple Devices
If you have multiple Android devices:
```python
# In config.py
MOBILE_DEVICE_ID = "specific_device_id"
```

### Custom Streaming Settings
```python
# Custom resolution for specific device
MOBILE_CAMERA_MAX_RESOLUTION = (800, 600)  # Higher resolution

# Force specific streaming method
MOBILE_CAMERA_PREFERRED_METHOD = "scrcpy"  # Force scrcpy
```

## File Structure
```
motion_detection_system/
├── config.py                     # Configuration
├── mobile_camera_handler.py      # Mobile camera integration
├── motion_detection_mobile.py    # Main script with mobile support
├── database_config.py            # Database connection
├── image_processor.py            # Image processing
├── web_viewer_fixed.py           # Web interface
└── requirements.txt              # Dependencies
```

## Support

If you encounter issues:
1. Check this troubleshooting guide
2. Test each component individually
3. Check phone and PC compatibility
4. Verify all dependencies are installed

## Next Steps

After setup:
1. Test mobile camera connection
2. Run motion detection system
3. Check database for stored alerts
4. Use web viewer to review captures
5. Adjust sensitivity settings as needed

Happy monitoring! 📱🔐
