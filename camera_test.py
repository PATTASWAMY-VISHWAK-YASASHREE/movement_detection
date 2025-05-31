#!/usr/bin/env python3
"""
Camera Test Utility

This utility helps debug camera access issues and find available cameras.
"""

import cv2
import sys

def test_multiple_cameras():
    """Test multiple camera indices to find available cameras"""
    print("🔍 Scanning for available cameras...")
    available_cameras = []
    
    for i in range(5):  # Test camera indices 0-4
        print(f"Testing camera index {i}...")
        cap = cv2.VideoCapture(i)
        
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                height, width = frame.shape[:2]
                print(f"✅ Camera {i}: Available ({width}x{height})")
                available_cameras.append(i)
            else:
                print(f"⚠️ Camera {i}: Opens but cannot read frames")
        else:
            print(f"❌ Camera {i}: Not available")
            
        cap.release()
        
    return available_cameras

def test_camera_detailed(camera_index=0):
    """Test camera with detailed information"""
    print(f"\n📹 Testing camera {camera_index} in detail...")
    
    cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        print(f"❌ Cannot open camera {camera_index}")
        return False
        
    # Get camera properties
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    print(f"📊 Camera properties:")
    print(f"   Resolution: {int(width)}x{int(height)}")
    print(f"   FPS: {fps}")
    
    # Try to read a frame
    ret, frame = cap.read()
    if ret:
        print("✅ Successfully read frame from camera")
        print(f"   Frame shape: {frame.shape}")
        
        # Show camera feed for 5 seconds
        print("📺 Displaying camera feed for 5 seconds (press 'q' to exit early)...")
        import time
        start_time = time.time()
        
        while time.time() - start_time < 5:
            ret, frame = cap.read()
            if ret:
                cv2.imshow(f'Camera {camera_index} Test', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            else:
                print("❌ Lost camera connection")
                break
                
        cv2.destroyAllWindows()
        cap.release()
        return True
    else:
        print("❌ Cannot read frame from camera")
        cap.release()
        return False

def main():
    """Main camera test function"""
    print("🎥 Camera Test Utility")
    print("=" * 50)
    
    # Test all cameras
    available_cameras = test_multiple_cameras()
    
    if not available_cameras:
        print("\n❌ No cameras found!")
        print("\n💡 Troubleshooting tips:")
        print("   1. Make sure your camera is connected")
        print("   2. Check if other applications are using the camera")
        print("   3. Try running as administrator")
        print("   4. Check camera permissions in Windows settings")
        return
        
    print(f"\n✅ Found {len(available_cameras)} available camera(s): {available_cameras}")
    
    # Test the first available camera in detail
    if available_cameras:
        test_camera_detailed(available_cameras[0])
        
        # Update config.py with the working camera index
        try:
            with open("config.py", "r") as f:
                config_content = f.read()
                
            # Replace camera index
            new_config = config_content.replace(
                f"CAMERA_INDEX = 0", 
                f"CAMERA_INDEX = {available_cameras[0]}"
            )
            
            with open("config.py", "w") as f:
                f.write(new_config)
                
            print(f"✅ Updated config.py to use camera index {available_cameras[0]}")
        except Exception as e:
            print(f"⚠️ Could not update config.py: {e}")

if __name__ == "__main__":
    main()
