#!/bin/bash
# Start the Meter Snapshot Viewer Web UI

echo "🚀 Starting Meter Snapshot Viewer..."
echo ""

python3 snapshot_viewer.py --port 5001

# Alternative: Run in background
# python3 snapshot_viewer.py --port 5001 > logs/viewer.log 2>&1 &
# echo "Viewer started in background. View logs with: tail -f logs/viewer.log"
# echo "Access at: http://127.0.0.1:5001"
