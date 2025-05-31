#!/usr/bin/env python3
"""
Movement Detection System Setup Script

This script installs all required dependencies for the movement detection system
and checks that the environment is properly configured.

Usage:
    python setup.py

Author: Movement Detection Security System
"""

import os
import platform
import subprocess
import sys
from pathlib import Path
import socket

def print_step(step_num, message):
    """Print a formatted step message"""
    print(f"\n[{step_num}] {message}")
    print("=" * (len(message) + 5))

def run_command(command, description=None, exit_on_error=False):
    """Run a shell command and handle errors"""
    if description:
        print(f"{description}...")
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print(f"✅ Command completed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed with error code {e.returncode}")
        print(f"Error output: {e.stderr}")
        if exit_on_error:
            print("Exiting setup...")
            sys.exit(1)
        return None

def check_python_version():
    """Check if Python version meets requirements"""
    print_step(1, "Checking Python version")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print(f"❌ Python version {version.major}.{version.minor}.{version.micro} detected")
        print("❌ This project requires Python 3.7 or higher")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected (OK)")
    return True

def check_pip():
    """Check if pip is installed and working"""
    print_step(2, "Checking pip installation")
    
    try:
        import pip
        print(f"✅ pip version {pip.__version__} found (OK)")
        return True
    except ImportError:
        print("❌ pip not found. Installing pip...")
        run_command("python -m ensurepip --upgrade", "Installing pip")
        try:
            import pip
            print(f"✅ pip version {pip.__version__} installed successfully")
            return True
        except ImportError:
            print("❌ Failed to install pip. Please install pip manually.")
            return False

def install_requirements():
    """Install packages from requirements.txt"""
    print_step(3, "Installing required packages")
    
    requirements_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
    
    if not os.path.exists(requirements_path):
        print(f"❌ Requirements file not found at: {requirements_path}")
        return False
    
    print(f"📋 Installing dependencies from {requirements_path}")
    
    # Use python -m pip to ensure we use the correct pip version
    result = run_command(f"{sys.executable} -m pip install -r {requirements_path}",
                        "Installing dependencies")
    
    if result is not None:
        print("✅ All dependencies installed successfully")
        return True
    
    return False

def check_opencv():
    """Test OpenCV installation"""
    print_step(4, "Checking OpenCV installation")
    
    try:
        import cv2
        print(f"✅ OpenCV version {cv2.__version__} installed (OK)")
        return True
    except ImportError:
        print("❌ OpenCV not found. Please check installation.")
        return False

def check_pytorch():
    """Test PyTorch installation"""
    print_step(5, "Checking PyTorch installation")
    
    try:
        import torch
        print(f"✅ PyTorch version {torch.__version__} installed (OK)")
        
        if torch.cuda.is_available():
            print(f"✅ CUDA is available (GPU acceleration enabled)")
            print(f"   🖥️ GPU: {torch.cuda.get_device_name(0)}")
        else:
            print("⚠️ CUDA not available (using CPU mode)")
        
        return True
    except ImportError:
        print("❌ PyTorch not found. Please check installation.")
        return False

def check_flask():
    """Test Flask installation"""
    print_step(6, "Checking Flask installation")
    
    try:
        import flask
        print(f"✅ Flask version {flask.__version__} installed (OK)")
        return True
    except ImportError:
        print("❌ Flask not found. Please check installation.")
        return False

def check_network():
    """Check network configuration"""
    print_step(7, "Checking network configuration")
    
    # Get local IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        print(f"✅ Local IP address: {local_ip}")
        
        # Check if localhost resolves
        localhost_ip = socket.gethostbyname('localhost')
        print(f"✅ Localhost resolves to: {localhost_ip}")
        
        return True
    except Exception as e:
        print(f"❌ Network configuration error: {e}")
        return False

def setup_database():
    """Set up the database"""
    print_step(8, "Setting up database")
    
    # Check if we have psycopg2 installed
    try:
        import psycopg2
        print(f"✅ psycopg2 version {psycopg2.__version__} installed (OK)")
    except ImportError:
        print("❌ psycopg2 not found. Database functionality may be limited.")
        return False
    
    # Run database setup script if it exists
    setup_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                               "src", "database", "setup_database.py")
    
    if os.path.exists(setup_script):
        print(f"📊 Running database setup script...")
        run_command(f"{sys.executable} {setup_script}", "Setting up database")
        return True
    else:
        print("⚠️ Database setup script not found")
        return False

def print_summary(all_checks_passed):
    """Print summary of setup results"""
    print("\n" + "=" * 50)
    
    if all_checks_passed:
        print("✅ SETUP COMPLETED SUCCESSFULLY")
        print("\n🚀 You can now run the system using:")
        print(f"   {sys.executable} start_system.py --all")
        print("\n📱 Mobile device setup guide can be found in:")
        print("   MOBILE_SETUP_GUIDE.md")
    else:
        print("⚠️ SETUP COMPLETED WITH WARNINGS")
        print("\nPlease fix the issues mentioned above before running the system.")
    
    print("=" * 50)

def main():
    """Main setup function"""
    print("\n📊 MOVEMENT DETECTION SYSTEM SETUP")
    print("=" * 50)
    
    # Get system info
    system = platform.system()
    print(f"🖥️ System: {system} {platform.version()}")
    print(f"🐍 Python: {sys.version}")
    print("=" * 50)
    
    # Run all checks
    checks = [
        check_python_version(),
        check_pip(),
        install_requirements(),
        check_opencv(),
        check_pytorch(),
        check_flask(),
        check_network(),
        setup_database()
    ]
    
    all_checks_passed = all(checks)
    
    print_summary(all_checks_passed)
    
    return 0 if all_checks_passed else 1

if __name__ == "__main__":
    sys.exit(main())
