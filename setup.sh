#!/bin/bash
# Setup script for Water Meter Monitor

echo "=============================================="
echo "Water Meter Monitor - Setup"
echo "=============================================="
echo

# Check Python version
echo "Checking Python version..."
python3 --version
if [ $? -ne 0 ]; then
    echo "Error: Python 3 is not installed"
    exit 1
fi
echo "✓ Python 3 is installed"
echo

# Install dependencies
echo "Installing dependencies..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies"
    exit 1
fi
echo "✓ Dependencies installed"
echo

# Check for .env file
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env file created"
    echo
    echo "⚠️  IMPORTANT: Edit .env file and set your:"
    echo "   - ANTHROPIC_API_KEY"
    echo "   - WYZE_CAM_IP"
    echo "   - WYZE_CAM_PASS"
    echo
else
    echo "✓ .env file already exists"
    echo
fi

# Create logs directory if it doesn't exist
mkdir -p logs
echo "✓ Logs directory ready"
echo

echo "=============================================="
echo "Setup Complete!"
echo "=============================================="
echo
echo "Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Test camera: curl --user root:PASSWORD http://CAMERA_IP/cgi-bin/currentpic.cgi -o test.jpg"
echo "3. Run monitor: python3 wyze_cam_monitor.py"
echo
echo "Documentation:"
echo "- Quick Start: WYZE_QUICKSTART.md"
echo "- Full Setup: WYZE_CAM_V2_SETUP.md"
echo
