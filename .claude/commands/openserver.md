---
description: Check if web server is running and open it in browser
---

Check if the meter preview web server is running, start it if needed, and open it in your default browser.

## Implementation

### Step 1: Check if server is already running

```bash
if curl -s --max-time 2 http://127.0.0.1:2500/ > /dev/null 2>&1; then
    echo "✅ Server is already running at http://127.0.0.1:2500"
    SERVER_RUNNING=true
else
    echo "⚠️  Server is not running"
    SERVER_RUNNING=false
fi
```

### Step 2: Start server if not running

```bash
if [ "$SERVER_RUNNING" = false ]; then
    echo "🚀 Starting meter preview server..."
    python3 meter_preview_ui.py --host 127.0.0.1 --port 2500 > /tmp/meter_ui.log 2>&1 &
    SERVER_PID=$!
    echo "   PID: $SERVER_PID"

    # Wait for server to start
    echo "   Waiting for server to start..."
    for i in {1..10}; do
        sleep 1
        if curl -s --max-time 1 http://127.0.0.1:2500/ > /dev/null 2>&1; then
            echo "✅ Server started successfully!"
            break
        fi
        if [ $i -eq 10 ]; then
            echo "❌ Server failed to start. Check /tmp/meter_ui.log for errors:"
            tail -20 /tmp/meter_ui.log
            exit 1
        fi
    done
fi
```

### Step 3: Open browser

```bash
echo ""
echo "🌐 Opening http://127.0.0.1:2500 in your browser..."
open http://127.0.0.1:2500

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✨ Meter Preview Dashboard"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "URL:  http://127.0.0.1:2500"
echo "Log:  /tmp/meter_ui.log"
echo ""
echo "To stop the server:"
echo "  pkill -f meter_preview_ui.py"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
```

## Usage Notes

- Server runs on http://127.0.0.1:2500 by default
- Logs are saved to /tmp/meter_ui.log
- To stop the server: `pkill -f meter_preview_ui.py`
- To check server status: `curl http://127.0.0.1:2500/`
- Server runs Flask in development mode (not for production use)

## Troubleshooting

If server fails to start:
1. Check log file: `cat /tmp/meter_ui.log`
2. Check if port 2500 is already in use: `lsof -ti:2500`
3. Kill existing process: `kill $(lsof -ti:2500)`
4. Check Python dependencies: `pip3 install flask pyyaml`
