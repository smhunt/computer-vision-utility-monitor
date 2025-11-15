# Grafana Dashboard Setup for Water Meter Monitoring

Real-time visualization of your water meter readings with automatic leak detection.

## Quick Start

### 1. Start Docker Services

```bash
cd /Users/seanhunt/Code/computer-vision-utility-monitor
docker-compose up -d
```

This starts:
- **InfluxDB** (time-series database) - http://localhost:8086
- **Grafana** (dashboards) - http://localhost:3000

### 2. Log In to Grafana

- **URL:** http://localhost:3000
- **Username:** admin
- **Password:** ***REMOVED***

### 3. View Dashboard

- Go to Dashboards → Browse
- Click "Water Meter Monitor" dashboard
- Graphs will populate as monitoring script runs

---

## What's Included

### Dashboard Panels

1. **Water Meter Reading (Last 7 Days)**
   - Line graph showing total consumption over time
   - Helps identify trends and anomalies
   - Smooth interpolation for easy visualization

2. **Current Reading (Stat)**
   - Large display of latest meter reading
   - Updates every 30 seconds
   - Color-coded for quick status check

3. **Flow Rate (Last 24 Hours)**
   - Bar chart showing water usage per hour
   - Alerts on abnormal flow (green → yellow → red)
   - Useful for leak detection

4. **Reading Count (24h)**
   - Number of readings in the last 24 hours
   - Confirms monitoring system is running

---

## Integration with Monitoring Script

The monitoring script automatically sends readings to InfluxDB:

```bash
# Start monitoring (writes to both logs and InfluxDB)
set -a && source .env && set +a
python3 wyze_cam_monitor.py
```

Each reading includes:
- Total consumption (m³)
- Digital display value
- Dial/fractional value
- Confidence level
- API token usage
- Timestamp

---

## Advanced: Custom Queries

Edit dashboard panels to customize queries. Example Flux queries:

### Last 7 days of readings
```flux
from(bucket:"water_meter")
  |> range(start:-7d)
  |> filter(fn:(r)=>r._measurement=="water_meter")
  |> filter(fn:(r)=>r._field=="total_reading")
```

### Flow rate calculation
```flux
from(bucket:"water_meter")
  |> range(start:-24h)
  |> filter(fn:(r)=>r._measurement=="water_meter")
  |> filter(fn:(r)=>r._field=="total_reading")
  |> derivative(unit:1h)
  |> map(fn:(r)=>({r with _value: r._value * 1000}))
```

### High flow alerts
```flux
from(bucket:"water_meter")
  |> range(start:-1h)
  |> filter(fn:(r)=>r._measurement=="water_meter")
  |> filter(fn:(r)=>r._field=="total_reading")
  |> derivative(unit:1h)
  |> filter(fn:(r)=>r._value > 10)
```

---

## Troubleshooting

### Grafana won't connect to InfluxDB
```bash
# Check InfluxDB is running
docker ps | grep influxdb

# View logs
docker logs water-meter-influxdb
```

### No data appearing in dashboard
1. Check monitoring script is running and writing readings
2. Wait 30 seconds for dashboard to refresh
3. Verify InfluxDB datasource is configured (Data Sources → InfluxDB)

### Stop Services
```bash
docker-compose down
```

### Remove All Data (Clean Reset)
```bash
docker-compose down -v
```

---

## Environment Variables

Add these to `.env` for custom configuration:

```bash
# InfluxDB configuration
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=test-token
```

---

## Next Steps

1. **Position your camera** at the water meter
2. **Start the monitoring script** (`python3 wyze_cam_monitor.py`)
3. **Open Grafana** and watch readings come in
4. **Set up alerts** for unusual water usage
5. **Export data** for analysis or billing

---

## Architecture

```
Water Meter (physical)
    ↓
Wyze Cam V2 (Thingino firmware)
    ↓
Camera → MJPEG Stream (10.10.10.207/mjpeg)
    ↓
Monitoring Script (wyze_cam_monitor.py)
    ↓
    ├→ Local Logs (logs/readings.jsonl + logs/snapshots/*.jpg)
    ├→ InfluxDB (time-series database)
    └→ Grafana (real-time dashboards)
```

---

**Your water meter is now fully monitored and visualized!** 💧📊
