# Meter Snapshot Archive System

**Complete system for archiving, managing, and viewing meter snapshots with metadata**

Last Updated: 2025-11-19

## Overview

This system automatically archives every meter snapshot with metadata including:
- Meter readings (digital, dial, total)
- Confidence levels
- Temperature data (when available)
- Timestamps
- Camera information
- API usage statistics

## Components

### 1. Snapshot Manager (`src/snapshot_manager.py`)
Core module for managing snapshot archives.

**Features:**
- Timestamped file naming
- Organized directory structure
- Metadata management (JSON sidecar files)
- Reading history queries
- Latest snapshot retrieval

**Usage:**
```python
from snapshot_manager import SnapshotManager

manager = SnapshotManager()
archived_path = manager.save_snapshot(
    "/tmp/meter_snapshot.jpg",
    "water_main"
)
```

### 2. Metadata Worker (`src/snapshot_metadata_worker.py`)
Processes snapshots and adds comprehensive metadata.

**Features:**
- Analyzes meter readings with Claude Vision API
- Captures temperature data (when SSH available)
- Creates metadata JSON files
- Can watch directories for new snapshots
- Single-shot or continuous processing

**Usage:**

**Process a single snapshot:**
```bash
python3 src/snapshot_metadata_worker.py process \
    --snapshot /tmp/meter_snapshot_water_main.jpg \
    --meter water_main
```

**Watch directory for new snapshots:**
```bash
python3 src/snapshot_metadata_worker.py watch \
    --watch-dir /tmp \
    --meter water_main \
    --interval 5
```

### 3. Web Viewer (`snapshot_viewer.py`)
Beautiful web interface for viewing snapshot history.

**Features:**
- Browse all archived snapshots
- View readings over time
- Click to enlarge images
- See confidence levels and temperature
- Responsive design
- REST API endpoints

**Start the viewer:**
```bash
./start_snapshot_viewer.sh
# Or manually:
python3 snapshot_viewer.py --port 5001
```

Then open: http://127.0.0.1:5001

### 4. Temperature Reader (`src/temperature_reader.py`)
Captures temperature from camera SoC (when SSH available).

**Features:**
- Multiple temperature source support
- Graceful fallback when unavailable
- Future: Weather API, external sensors

## Directory Structure

```
logs/meter_snapshots/
├── water_main/
│   ├── water_main_20251119_120820.jpg      # Snapshot image
│   ├── water_main_20251119_120820.json     # Metadata
│   ├── water_main_20251119_130530.jpg
│   ├── water_main_20251119_130530.json
│   └── ...
└── [other_meters]/
```

## Metadata Format

Each snapshot has a JSON metadata file:

```json
{
  "snapshot": {
    "filename": "water_main_20251119_120820.jpg",
    "timestamp": "2025-11-19T12:08:20.174865",
    "path": "logs/meter_snapshots/water_main/water_main_20251119_120820.jpg"
  },
  "meter_reading": {
    "digital_reading": 22,
    "dial_reading": 0.315,
    "total_reading": 22.315,
    "confidence": "medium",
    "notes": "The digital display clearly shows..."
  },
  "api_usage": {
    "input_tokens": 1796,
    "output_tokens": 213
  },
  "temperature": {
    "celsius": 45.2,
    "fahrenheit": 113.4,
    "source": "camera",
    "available": true
  },
  "camera": {
    "source_file": "meter_snapshot_water_main.jpg",
    "model": "Wyze Cam V2 (Thingino)",
    "ip": "10.10.10.207"
  }
}
```

## Workflow

### Manual Workflow

1. **Capture snapshot:**
   ```bash
   /takemetersnapshot
   ```
   This creates `/tmp/meter_snapshot_water_main.jpg`

2. **Process and archive:**
   ```bash
   python3 src/snapshot_metadata_worker.py process \
       --snapshot /tmp/meter_snapshot_water_main.jpg \
       --meter water_main
   ```

3. **View in browser:**
   ```bash
   ./start_snapshot_viewer.sh
   ```
   Open http://127.0.0.1:5001

### Automated Workflow

**Option 1: Watch Mode**
Run the worker in watch mode to automatically process new snapshots:
```bash
python3 src/snapshot_metadata_worker.py watch \
    --watch-dir /tmp \
    --meter water_main \
    --interval 5
```

**Option 2: Cron Job**
Set up a cron job to capture and process snapshots:
```bash
# Every 10 minutes
*/10 * * * * cd /path/to/project && /takemetersnapshot && python3 src/snapshot_metadata_worker.py process --snapshot /tmp/meter_snapshot_water_main.jpg --meter water_main
```

## API Endpoints

The web viewer exposes REST API endpoints:

### Get meter history
```bash
curl http://127.0.0.1:5001/api/meter/water_main/history?limit=50
```

### Get latest reading
```bash
curl http://127.0.0.1:5001/api/meter/water_main/latest
```

### View image
```
http://127.0.0.1:5001/image/water_main/water_main_20251119_120820.jpg
```

## Integration with Existing System

### Updated `/takemetersnapshot` Command
The command now:
1. Captures snapshot from camera
2. Attempts temperature capture (graceful fallback)
3. Analyzes meter reading with Claude
4. **Archives snapshot with metadata** (NEW!)
5. Shows summary with link to web viewer

### Compatible with Existing Tools
- Works with existing `meter_preview_ui.py`
- Compatible with `camera_presets.py`
- Integrates with temperature capture system

## Benefits

✅ **Complete History**: Never lose a meter reading
✅ **Metadata Rich**: Every snapshot includes full context
✅ **Visual Timeline**: See readings over time
✅ **API Access**: Programmatic access to data
✅ **Temperature Tracking**: Correlate readings with temperature
✅ **Audit Trail**: Full record for analysis and debugging
✅ **Beautiful UI**: Easy to use web interface

## Future Enhancements

- [ ] Graph/chart view of readings over time
- [ ] Export to CSV/Excel
- [ ] Anomaly detection (unusual reading changes)
- [ ] Email/SMS alerts for threshold violations
- [ ] Mobile app integration
- [ ] Multi-meter comparison views
- [ ] Automated reporting

## Troubleshooting

### Snapshots not appearing in viewer
- Check directory: `ls logs/meter_snapshots/water_main/`
- Ensure metadata worker processed the snapshot
- Restart viewer: `./start_snapshot_viewer.sh`

### Temperature always unavailable
- SSH needs to be configured on camera
- See [THINGINO_CAMERA_REFERENCE.md](THINGINO_CAMERA_REFERENCE.md)
- Alternative: Use weather API or external sensor

### Worker process errors
- Check Python dependencies: `pip install -r requirements.txt`
- Verify environment variables in `.env`
- Check API key is set: `echo $ANTHROPIC_API_KEY`

## Files Created

**New Modules:**
- `src/snapshot_manager.py` - Archive management
- `src/snapshot_metadata_worker.py` - Metadata processor
- `src/temperature_reader.py` - Temperature capture
- `snapshot_viewer.py` - Web UI server
- `start_snapshot_viewer.sh` - Launch script

**New Directories:**
- `logs/meter_snapshots/` - Snapshot archive
- `templates/` - HTML templates (auto-generated)

**Updated:**
- `.claude/commands/takemetersnapshot.md` - Updated workflow

## Quick Start

1. **Take a snapshot:**
   ```bash
   /takemetersnapshot
   ```

2. **Start the web viewer:**
   ```bash
   ./start_snapshot_viewer.sh
   ```

3. **Open in browser:**
   http://127.0.0.1:5001

4. **Enjoy!** 🎉
