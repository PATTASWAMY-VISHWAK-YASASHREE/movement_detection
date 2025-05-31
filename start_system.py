#!/usr/bin/env python3
"""
Movement Detection System Startup Script

This script provides a simple command-line interface to start the different
components of the movement detection system:
- Web viewer
- Wireless camera server
- Motion detection system

Author: Movement Detection Security System
"""

import argparse
import os
import socket
import subprocess
import sys
from pathlib import Path

def get_local_ip():
    """Get local IP address for display purposes"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"

def run_component(component_name, env=None, cwd=None):
    """Run a system component script"""
    if component_name == "web_viewer":
        script = "src/web/web_viewer_fixed.py"
        print("\n🚀 Starting Web Viewer on all network interfaces...")
    elif component_name == "wireless_camera":
        script = "src/web/wireless_camera_server_fixed.py"
        print("\n📱 Starting Wireless Camera Server...")
    elif component_name == "motion_detector":
        script = "src/detection/motion_detector.py"
        print("\n👁️ Starting Motion Detector...")
    elif component_name == "ai_motion_detector":
        script = "src/detection/motion_detector_ai.py"
        print("\n🧠 Starting AI-powered Motion Detector...")
    else:
        print(f"❌ Unknown component: {component_name}")
        return None
    
    # Get absolute path to script
    base_dir = Path(__file__).parent.absolute()
    script_path = base_dir / script
    
    if not script_path.exists():
        print(f"❌ Script not found: {script_path}")
        return None
    
    # Print access instructions
    local_ip = get_local_ip()
    if component_name == "web_viewer":
        print(f"📊 Access the web dashboard at: http://{local_ip}:5000")
        print("   This can be accessed from any device on your network.")
    elif component_name == "wireless_camera":
        print(f"📱 Connect mobile devices at: http://{local_ip}:3000/camera")
        print(f"🖥️ View all wireless cameras at: http://{local_ip}:3000/viewer")
        print(f"🔄 Access wireless camera dashboard at: http://{local_ip}:3000/viewer-with-qr")
    
    # Run the script as a subprocess
    try:
        if sys.platform == "win32":
            process = subprocess.Popen(
                [sys.executable, str(script_path)],
                env=env,
                cwd=cwd or str(base_dir)
            )
        else:  # Linux/Mac
            process = subprocess.Popen(
                [str(script_path)],
                env=env,
                cwd=cwd or str(base_dir)
            )
        return process
    except Exception as e:
        print(f"❌ Error starting {component_name}: {e}")
        return None

def main():
    """Main function to parse arguments and start system components"""
    parser = argparse.ArgumentParser(description="Start Movement Detection System Components")
    parser.add_argument('--all', action='store_true', help="Start all system components")
    parser.add_argument('--web', action='store_true', help="Start web viewer")
    parser.add_argument('--wireless', action='store_true', help="Start wireless camera server")
    parser.add_argument('--detector', action='store_true', help="Start motion detector")
    parser.add_argument('--ai-detector', action='store_true', help="Start AI-powered motion detector")
    
    args = parser.parse_args()
    
    # Check if no arguments provided, show help
    if not any(vars(args).values()):
        parser.print_help()
        print("\n🔍 Example: python start_system.py --all")
        print("🔍 Example: python start_system.py --web --wireless")
        return
    
    processes = []
    
    try:
        # Start components based on arguments
        if args.all or args.web:
            proc = run_component("web_viewer")
            if proc:
                processes.append(proc)
        
        if args.all or args.wireless:
            proc = run_component("wireless_camera")
            if proc:
                processes.append(proc)
        
        if args.all or args.detector:
            proc = run_component("motion_detector")
            if proc:
                processes.append(proc)
        
        if args.ai_detector:
            proc = run_component("ai_motion_detector")
            if proc:
                processes.append(proc)
        
        print("\n⚠️ Press Ctrl+C to stop all components and exit")
        
        # Wait for keyboard interrupt
        for proc in processes:
            proc.wait()
            
    except KeyboardInterrupt:
        print("\n⏹️ Stopping all components...")
        for proc in processes:
            if proc:
                proc.terminate()
        print("✅ All components stopped. System shutdown complete.")

if __name__ == "__main__":
    main()
