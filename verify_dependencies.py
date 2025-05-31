#!/usr/bin/env python3
"""
Dependency Verification Script

This script verifies that all required dependencies are installed and functioning
correctly. It imports each required library and checks its version.

Run this script if you're having issues with the movement detection system:
    python verify_dependencies.py

Author: Movement Detection Security System
"""

import importlib
import sys
import pkg_resources

def print_header(text):
    """Print formatted header text"""
    print(f"\n{text}")
    print("=" * len(text))

def check_dependency(module_name, min_version=None, extra_check=None):
    """Check if dependency is installed and meets version requirements"""
    try:
        # Try to import the module
        module = importlib.import_module(module_name)
        
        # Get version (different libraries store versions differently)
        version = None
        for attr in ['__version__', 'version', 'VERSION']:
            if hasattr(module, attr):
                version = getattr(module, attr)
                if callable(version):
                    version = version()
                break
        
        # If we couldn't find version in module, try pkg_resources
        if version is None:
            try:
                version = pkg_resources.get_distribution(module_name).version
            except:
                version = "unknown"
        
        # Check minimum version if specified
        if min_version and version != "unknown":
            if pkg_resources.parse_version(version) < pkg_resources.parse_version(min_version):
                print(f"⚠️  {module_name}: version {version} found (Minimum required: {min_version})")
                return False
        
        print(f"✅ {module_name}: version {version}")
        
        # Run extra check if provided
        if extra_check and callable(extra_check):
            return extra_check(module)
        
        return True
        
    except ModuleNotFoundError:
        print(f"❌ {module_name}: Not found")
        return False
    except Exception as e:
        print(f"❌ {module_name}: Error - {str(e)}")
        return False

def check_opencv(cv2):
    """Additional checks for OpenCV"""
    try:
        # Check if we can access a camera (without actually opening it)
        backends = []
        if hasattr(cv2, 'getBuildInformation'):
            info = cv2.getBuildInformation()
            if 'Video I/O' in info:
                io_section = info.split('Video I/O')[1].split('\n\n')[0]
                backends = [line.strip().split(':')[0] for line in io_section.split('\n') 
                           if ':' in line and 'YES' in line]
        
        print(f"  ↳ Video backends: {', '.join(backends) if backends else 'Unknown'}")
        
        # Check if we have GPU support
        has_cuda = 'cuda' in cv2.getBuildInformation().lower() if hasattr(cv2, 'getBuildInformation') else False
        if has_cuda:
            print("  ↳ CUDA support: Available")
        else:
            print("  ↳ CUDA support: Not available (CPU mode)")
            
        return True
    except Exception as e:
        print(f"  ↳ Error during extended checks: {e}")
        return False

def check_torch(torch):
    """Additional checks for PyTorch"""
    try:
        # Check CUDA availability
        if torch.cuda.is_available():
            device_count = torch.cuda.device_count()
            device_name = torch.cuda.get_device_name(0) if device_count > 0 else "Unknown"
            print(f"  ↳ CUDA: Available (Devices: {device_count}, GPU: {device_name})")
        else:
            print("  ↳ CUDA: Not available (CPU mode)")
        
        return True
    except Exception as e:
        print(f"  ↳ Error during extended checks: {e}")
        return False

def check_flask(flask):
    """Additional checks for Flask"""
    try:
        # Check if we have the requirements for our app
        has_socketio = False
        try:
            import flask_socketio
            has_socketio = True
        except ImportError:
            pass
            
        if has_socketio:
            print(f"  ↳ Flask-SocketIO: Available")
        else:
            print(f"  ↳ Flask-SocketIO: Not available (required for wireless cameras)")
            
        return True
    except Exception as e:
        print(f"  ↳ Error during extended checks: {e}")
        return False

def main():
    """Run dependency checks"""
    print_header("Movement Detection System - Dependency Verification")
    print("Python version:", sys.version)
    
    print_header("Core Dependencies")
    opencv_ok = check_dependency("cv2", "4.5.0", check_opencv)
    numpy_ok = check_dependency("numpy", "1.20.0")
    
    print_header("Machine Learning Dependencies")
    torch_ok = check_dependency("torch", "1.7.0", check_torch)
    torchvision_ok = check_dependency("torchvision", "0.8.0")
    ultralytics_ok = check_dependency("ultralytics", "8.0.0")
    
    print_header("Web Dependencies")
    flask_ok = check_dependency("flask", "2.0.0", check_flask)
    socketio_ok = check_dependency("flask_socketio", "5.0.0")
    
    print_header("Database Dependencies")
    psycopg2_ok = check_dependency("psycopg2", "2.9.0")
    
    print_header("Image Processing")
    pillow_ok = check_dependency("PIL", "8.0.0")
    qrcode_ok = check_dependency("qrcode", "7.0.0")
    
    print_header("Other Dependencies")
    requests_ok = check_dependency("requests", "2.25.0")
    
    # Display summary
    all_dependencies = [
        opencv_ok, numpy_ok, torch_ok, torchvision_ok, 
        ultralytics_ok, flask_ok, socketio_ok, psycopg2_ok,
        pillow_ok, qrcode_ok, requests_ok
    ]
    
    success_count = sum(1 for dep in all_dependencies if dep)
    total_count = len(all_dependencies)
    
    print_header("Summary")
    print(f"✅ Successfully verified: {success_count}/{total_count} dependencies")
    
    if success_count < total_count:
        missing_count = total_count - success_count
        print(f"❌ Missing or problematic: {missing_count} dependencies")
        print("\nTo install missing dependencies, run:")
        print("    python setup.py")
        return 1
    else:
        print("\nAll dependencies are installed correctly!")
        return 0

if __name__ == "__main__":
    sys.exit(main())
