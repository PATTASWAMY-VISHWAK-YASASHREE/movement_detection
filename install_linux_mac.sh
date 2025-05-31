#!/bin/bash

# Linux/macOS Installation Helper for Movement Detection System
# This script guides users through installing dependencies on Linux/macOS
# Author: Movement Detection Security System

echo ""
echo "========================================================"
echo "  Movement Detection System - Linux/macOS Installation  "
echo "========================================================"
echo ""

# Detect OS
if [[ "$(uname)" == "Darwin" ]]; then
    OS_NAME="macOS"
    echo "Detected macOS system"
elif [[ "$(uname)" == "Linux" ]]; then
    OS_NAME="Linux"
    echo "Detected Linux system"
    # Get distribution info
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo "Distribution: $NAME $VERSION_ID"
    fi
else
    OS_NAME="Unknown"
    echo "Warning: Unknown operating system"
fi

echo ""

# Check for Python installation
echo "Checking for Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "Python 3 not found!"
    echo "Please install Python 3.7 or newer before continuing."
    
    if [[ "$OS_NAME" == "macOS" ]]; then
        echo "On macOS, you can install Python using Homebrew:"
        echo "  brew install python"
    elif [[ "$OS_NAME" == "Linux" ]]; then
        echo "On Ubuntu/Debian, you can install Python using apt:"
        echo "  sudo apt update && sudo apt install python3 python3-pip"
        echo "On Fedora/RHEL/CentOS:"
        echo "  sudo dnf install python3 python3-pip"
    fi
    
    echo ""
    exit 1
fi

# Get Python version
PYTHON_VERSION=$(python3 --version 2>&1)
echo "Found $PYTHON_VERSION"

# Upgrade pip
echo ""
echo "Upgrading pip to the latest version..."
python3 -m pip install --user --upgrade pip

# Ask about virtual environment
echo ""
echo "Would you like to create a virtual environment? (Recommended)"
echo "This keeps the dependencies isolated from your system Python."
read -p "Create virtual environment? (y/n): " CREATE_VENV

if [[ "$CREATE_VENV" == "y" || "$CREATE_VENV" == "Y" ]]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m pip install --user --upgrade virtualenv
    python3 -m virtualenv venv
    
    echo ""
    echo "Activating virtual environment..."
    source venv/bin/activate
    
    if [ $? -ne 0 ]; then
        echo "Failed to create or activate virtual environment!"
        echo "Installation will continue using system Python."
    else
        echo "Virtual environment created and activated successfully."
        # Use python instead of python3 in virtual environment
        alias python=python3
    fi
else
    # If not using virtualenv, continue with system Python
    # For some systems, we might need to use python3 explicitly
    alias python=python3
fi

# Install dependencies
echo ""
echo "Installing required dependencies..."
python -m pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo ""
    echo "Error installing dependencies!"
    echo ""
    exit 1
fi

# Check for system dependencies (OpenCV may require additional libraries)
echo ""
echo "Checking for required system libraries..."

if [[ "$OS_NAME" == "Linux" ]]; then
    # On Linux, OpenCV may need additional libraries
    if ! python -c "import cv2" &> /dev/null; then
        echo "OpenCV installation may require additional system libraries."
        echo ""
        echo "On Ubuntu/Debian, you may need to install:"
        echo "  sudo apt install libsm6 libxext6 libxrender-dev libgl1-mesa-glx"
        echo ""
        echo "On Fedora/RHEL/CentOS:"
        echo "  sudo dnf install libglvnd-glx"
        echo ""
    fi
fi

# Verify installation
echo ""
echo "Verifying installation..."
python verify_dependencies.py

echo ""
echo "========================================================"
echo "     Installation complete!"
echo ""
echo "     Run the system using: python start_system.py --all"
echo "========================================================"
echo ""

# Remind about activating the virtual env in future sessions
if [[ "$CREATE_VENV" == "y" || "$CREATE_VENV" == "Y" ]]; then
    echo "Remember to activate the virtual environment in future sessions:"
    echo "  source venv/bin/activate"
    echo ""
fi
