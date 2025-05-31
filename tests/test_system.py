#!/usr/bin/env python3
"""
Demo script to test the Motion Detection Security System

This script will help you test if all components are working properly.
"""

import cv2
import sys
import os

def test_camera():
    """Test camera access"""
    print("🔍 Testing camera access...")
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ Error: Cannot access camera")
        return False
        
    ret, frame = cap.read()
    if not ret:
        print("❌ Error: Cannot read from camera")
        cap.release()
        return False
        
    print("✅ Camera test passed")
    cap.release()
    return True

def test_imports():
    """Test all required imports"""
    print("📦 Testing imports...")
    
    try:
        import cv2
        print("✅ OpenCV imported successfully")
    except ImportError:
        print("❌ OpenCV not available")
        return False
        
    try:
        import numpy as np
        print("✅ NumPy imported successfully")
    except ImportError:
        print("❌ NumPy not available")
        return False
        
    try:
        import pygame
        print("✅ Pygame imported successfully")
    except ImportError:
        print("⚠️ Pygame not available (sound alerts disabled)")
        
    try:
        from plyer import notification
        print("✅ Plyer imported successfully")
    except ImportError:
        print("⚠️ Plyer not available (desktop notifications disabled)")
        
    return True

def test_directories():
    """Test directory structure"""
    print("📁 Testing directories...")
    
    dirs = ["recordings", "recordings/alerts"]
    for dir_path in dirs:
        if os.path.exists(dir_path):
            print(f"✅ Directory exists: {dir_path}")
        else:
            print(f"❌ Directory missing: {dir_path}")
            return False
            
    return True

def main():
    """Run all tests"""
    print("🧪 Motion Detection Security System - Test Suite")
    print("=" * 60)
    
    tests = [
        ("Import Test", test_imports),
        ("Directory Test", test_directories),
        ("Camera Test", test_camera),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔬 Running {test_name}...")
        if test_func():
            passed += 1
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")
            
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! You can now run the security system.")
        print("\n🚀 To start the system, run:")
        print("   python motion_detector.py")
    else:
        print("⚠️ Some tests failed. Please check the requirements.")
        
    print("=" * 60)

if __name__ == "__main__":
    main()
