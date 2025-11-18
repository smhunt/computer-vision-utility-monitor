# Multi-Utility Meter Monitoring System

Automatically monitor water, electric, and gas meters using Wyze Cam V2 cameras and Claude's vision AI.

**Project Status:** Week 1 Foundation (In Progress)
**Teams:** 4 development teams + DevOps
**Timeline:** 4 weeks to production

---

## 🚀 For All Teams - Start Here

### New to the Project?
1. Read [TEAM_KICKOFF.md](TEAM_KICKOFF.md) (30 min overview)
2. Read [COORDINATION_SUMMARY.md](COORDINATION_SUMMARY.md) (10 min status)
3. Read your team's tasks in [PROJECT_BOARD.md](PROJECT_BOARD.md)
4. Join daily standup at 9:00 AM

### Need Your Team's Specific Info?

**Team A (Code Refactoring):**
- Tasks: [PROJECT_BOARD.md](PROJECT_BOARD.md) → Team A
- Coordination: [AGENT_COORDINATION.md](AGENT_COORDINATION.md) → Team A section

**Team B (Configuration Management):**
- Tasks: [PROJECT_BOARD.md](PROJECT_BOARD.md) → Team B
- Coordination: [AGENT_COORDINATION.md](AGENT_COORDINATION.md) → Team B section

**Team C (Infrastructure & Database):**
- Tasks: [PROJECT_BOARD.md](PROJECT_BOARD.md) → Team C
- Setup: [docker-compose.yml](docker-compose.yml)
- Guide: [GRAFANA_SETUP.md](GRAFANA_SETUP.md)

**Team D (Orchestrator & Integration):**
- Tasks: [PROJECT_BOARD.md](PROJECT_BOARD.md) → Team D
- Architecture: [AGENT_COORDINATION.md](AGENT_COORDINATION.md) → Dependencies

### All Teams - Important
- **Communication:** [COMMUNICATION_PLAN.md](COMMUNICATION_PLAN.md)
- **Security:** [CREDENTIALS.md](CREDENTIALS.md) - READ THIS BEFORE YOUR FIRST COMMIT!
- **Blockers:** [BLOCKING_ISSUES.md](BLOCKING_ISSUES.md) - Report blockers immediately
- **Coordination:** [AGENT_COORDINATION.md](AGENT_COORDINATION.md) - Your daily reference

---

## 📊 Project Overview

### What We're Building
An enterprise-grade monitoring system for three utility meters:
- **Water Meter** ✅ (Already working - reference implementation)
- **Electric Meter** 🔄 (In design, Week 1-2)
- **Gas Meter** 🔄 (In design, Week 1-2)

**All flowing to:** InfluxDB → Grafana → Real-time dashboards with cost tracking

### How It Works
```
Camera (Wyze + Thingino)
  ↓ MJPEG Stream
Claude Vision API
  ↓ Meter Reading + Confidence
InfluxDB
  ↓ Time-series Data
Grafana
  ↓ Real-time Dashboards
User
```

### 4-Week Timeline
```
Week 1: Foundation (Code + Config + Infrastructure)
Week 2: Integration (Orchestrator, multi-meter coordination)
Week 3: Visualization (Dashboards, alerts, cost tracking)
Week 4: Finalization (Testing, security, production-ready)
```

---

## 🏃 Quick Start (For Water Meter Reference)

### 1. Flash Wyze Cam V2 Firmware

**Choose a firmware** (both work great!):
- **Thingino** (recommended) - Used in this project
- **OpenMiko** - Modern alternative
- **Dafang Hacks** - Feature-rich alternative

```bash
# Copy firmware to FAT32-formatted SD card
cp sd_card_ready/thingino/demo.bin /Volumes/YOUR_SD_CARD/
# OR
cp sd_card_ready/openmiko/demo.bin /Volumes/YOUR_SD_CARD/

# Follow flashing instructions in sd_card_ready/README.md
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Environment Variables

```bash
# Option A: Load from .env files
set -a && source .env && source .env.local && set +a

# Option B: Export individually
export ANTHROPIC_API_KEY=sk-ant-...
export WATER_CAM_IP=10.10.10.207         # Your camera IP
export WATER_CAM_USER=root               # Thingino default
export WATER_CAM_PASS=***REMOVED***    # Set in .env.local
```

### 4. Start Docker Services (InfluxDB + Grafana)

```bash
docker-compose up -d

# Verify services
docker-compose ps
# Should show InfluxDB and Grafana running
```

### 5. Run the Water Meter Monitor

```bash
python wyze_cam_monitor.py

# View logs
python view_logs.py --latest 5
```

---

## 📚 Key Documentation

### For Project Managers/Owners
- [TEAM_KICKOFF.md](TEAM_KICKOFF.md) - Official launch document
- [COORDINATION_SUMMARY.md](COORDINATION_SUMMARY.md) - Current status
- [PROJECT_BOARD.md](PROJECT_BOARD.md) - Task tracking and timeline
- [BLOCKING_ISSUES.md](BLOCKING_ISSUES.md) - Issue tracker

### For Developers
- [AGENT_COORDINATION.md](AGENT_COORDINATION.md) - Daily coordination hub
- [COMMUNICATION_PLAN.md](COMMUNICATION_PLAN.md) - Communication protocols
- [CREDENTIALS.md](CREDENTIALS.md) - Security best practices ⚠️ READ BEFORE FIRST COMMIT
- [CREDENTIALS_QUICK_REF.txt](CREDENTIALS_QUICK_REF.txt) - Quick credential reference

### For DevOps/Infrastructure
- [GRAFANA_SETUP.md](GRAFANA_SETUP.md) - Dashboard configuration
- [docker-compose.yml](docker-compose.yml) - Infrastructure as code
- [SECURITY_SUMMARY.md](SECURITY_SUMMARY.md) - Security implementation

### For Reference (Water Meter)
- [WYZE_QUICKSTART.md](WYZE_QUICKSTART.md) - 30-minute setup guide
- [WYZE_CAM_V2_SETUP.md](WYZE_CAM_V2_SETUP.md) - Complete documentation
- [PROJECT_SETUP_COMPLETE.md](PROJECT_SETUP_COMPLETE.md) - System overview

---

## 🛠️ Project Structure

```
computer-vision-utility-monitor/
├── README.md                           # This file
├── TEAM_KICKOFF.md                     # Project launch document
├── COORDINATION_SUMMARY.md             # Current status overview
├── AGENT_COORDINATION.md               # Team coordination hub
├── COMMUNICATION_PLAN.md               # Communication protocols
├── PROJECT_BOARD.md                    # Task tracking (4 teams)
├── BLOCKING_ISSUES.md                  # Issue tracker
├── CREDENTIALS.md                      # Security best practices
├── SECURITY_SUMMARY.md                 # Security implementation
│
├── wyze_cam_monitor.py                 # Water meter monitor (reference)
├── meter_preview_ui.py                 # Web UI with camera controls
├── meter_preview_ui_v2.py              # Alternative UI implementation
├── camera_presets.py                   # Camera preset management
├── view_logs.py                        # Log viewer tool
│
├── src/
│   ├── meters/                         # Team A: Meter implementations
│   │   ├── __init__.py
│   │   ├── base_meter.py               # [To be created Week 1]
│   │   ├── water_meter.py              # [To be refactored Week 1]
│   │   ├── electric_meter.py           # [To be created Week 1]
│   │   └── gas_meter.py                # [To be created Week 1]
│   │
│   ├── core/
│   │   ├── llm_reader.py               # Claude vision integration
│   │   ├── camera_capture.py           # [To be created Week 1]
│   │   └── influxdb_writer.py          # Database integration
│   │
│   └── utils/
│       ├── config_loader.py            # [To be created Week 1]
│       └── logging_utils.py            # [To be created Week 1]
│
├── config/                             # Team B: Configuration
│   ├── meters.yaml                     # [To be created Week 1]
│   ├── prompts.yaml                    # [To be created Week 1]
│   └── examples/
│       ├── meters-water.yaml
│       ├── meters-electric.yaml
│       └── meters-gas.yaml
│
├── docker-compose.yml                  # Infrastructure (InfluxDB + Grafana)
├── grafana-provisioning/               # Team C: Grafana config
│   ├── datasources/
│   │   └── influxdb.yml
│   └── dashboards/
│       ├── dashboard.yml
│       └── water-meter-dashboard.json
│
├── logs/
│   ├── readings.jsonl                  # [Auto-created] Reading history
│   └── snapshots/                      # [Auto-created] Snapshot images
│
├── tests/                              # Unit tests
│   ├── test_camera_presets.py          # Camera preset tests
│   └── test_meter_preview_ui.py        # Web UI tests
│
├── sd_card_ready/                      # Firmware files (ready to flash)
│   ├── openmiko/demo.bin
│   ├── dafang/demo.bin
│   ├── thingino/demo.bin
│   ├── README.md
│   └── VERIFY.sh
│
├── firmware/                           # Firmware source
│   ├── README.md
│   └── prepare_sd_card.sh
│
├── requirements.txt                    # Python dependencies
├── .env                                # Public config (git-tracked)
├── .env.local                          # Private credentials (git-ignored) ⚠️
└── .gitignore                          # Git ignore patterns
```

---

## 🚀 Getting Started

### Step 1: Read Documentation
```bash
# All new team members should read these first:
1. README.md (this file)           # 5 min
2. TEAM_KICKOFF.md                 # 30 min
3. COORDINATION_SUMMARY.md         # 10 min
4. Your team's section of PROJECT_BOARD.md  # 10 min
5. CREDENTIALS.md                  # 20 min - CRITICAL!
```

### Step 2: Clone and Setup
```bash
git clone <repo>
cd computer-vision-utility-monitor
pip install -r requirements.txt
```

### Step 3: Configure Environment
```bash
# Copy template
cp .env.example .env

# Create private credentials file (git-ignored)
cat > .env.local << 'EOF'
GRAFANA_USER=sean@ecoworks.ca
GRAFANA_PASSWORD=***REMOVED***
EOF

# Set permissions (critical for security)
chmod 600 .env.local

# Verify git ignore is working
git check-ignore .env .env.local
```

### Step 4: Start Services
```bash
# Start InfluxDB and Grafana
docker-compose up -d

# Verify they're running
docker-compose ps

# Access Grafana: http://localhost:3000
```

### Step 5: Run Water Meter Monitor (Reference)

**Option A: Command-line monitoring**
```bash
# Load environment
set -a && source .env && source .env.local && set +a

# Run the monitor
python wyze_cam_monitor.py

# View logs in another terminal
python view_logs.py --latest 10
python view_logs.py --tail  # Real-time monitoring
```

**Option B: Web UI with camera controls (recommended)**
```bash
# Start the web interface
python meter_preview_ui.py --port 5001

# Open in browser: http://localhost:5001
# Features:
# - Live MJPEG camera streams
# - Camera preset controls (day/night/optimal modes)
# - Trigger readings on-demand
# - View latest readings with confidence scores
```

---

## 📋 Features

### Current (Water Meter - Complete)
- ✅ MJPEG stream capture from Thingino firmware
- ✅ Claude Vision API meter reading
- ✅ Confidence scoring (high/medium/low)
- ✅ InfluxDB time-series storage
- ✅ Grafana real-time dashboard
- ✅ JSON logging with snapshots
- ✅ Enterprise-grade credential security
- ✅ Live camera preview with real-time MJPEG streams
- ✅ Camera preset system (day/night/optimal modes)
- ✅ Multi-camera support with per-camera configuration
- ✅ Web UI for camera controls and meter readings
- ✅ Unit tests for camera and UI components

### Planned (Week 1-4)
- 🔄 Electric meter reading (Week 1-2)
- 🔄 Gas meter reading (Week 1-2)
- 🔄 Multi-meter orchestrator (Week 2)
- 🔄 Advanced dashboards with cost tracking (Week 3)
- 🔄 Anomaly detection and alerts (Week 3)
- 🔄 Flow rate and leak detection (Week 3)

---

## 💰 Cost Analysis

### Hardware
- Wyze Cam V2: ~$25 (you likely have)
- MicroSD Card (32GB): ~$10
- Weatherproof housing (optional): ~$15
- **Total per meter:** ~$15-25

### Operational (Monthly)
- Claude API calls: ~$0.03 (3 meters, $0.01 per meter)
- Power (camera): ~$0.50
- Server/hosting: $0-5 (if using cloud)
- **Total monthly:** ~$1-5.50

### Year 1 Estimate
- Hardware (3 cameras): $50
- API (365 days × 3 meters): $11
- Power: $6
- **Total:** ~$67 for complete 3-meter system

---

## 🔐 Security Important!

⚠️ **Before your first commit:**

1. **Read [CREDENTIALS.md](CREDENTIALS.md)**
   - Understand credential management
   - Know what goes in .env vs .env.local
   - Learn security best practices

2. **Verify git-ignore is working**
   ```bash
   git check-ignore .env .env.local
   # Should output both filenames (meaning they're ignored)
   ```

3. **Set file permissions**
   ```bash
   chmod 600 .env .env.local
   # Only you can read these files
   ```

4. **Never commit secrets**
   ```bash
   git status  # Should NOT show .env.local
   ```

**Emergency:** If credentials are exposed, see CREDENTIALS.md → "Emergency: Leaked Credentials"

---

## 📊 Weekly Status

**Week 1:** Foundation setup
- Team A: Code structure
- Team B: Configuration system
- Team C: Infrastructure ready
- Team D: Planning

**Week 2:** Integration
- Orchestrator implementation
- Multi-meter coordination
- Database migration testing

**Week 3:** Visualization
- Advanced dashboards
- Cost tracking
- Alerts and anomaly detection

**Week 4:** Production-ready
- Security audit
- Final testing
- System optimization

---

## 📞 Support & Communication

### Daily Standup
**Time:** 9:00 AM (Slack status update)
**Format:** What you did, what you're doing, blockers

### Mid-Week Check-in
**Time:** Wednesday 2:00 PM (15 min video call)
**Topic:** Integration review, risk assessment

### End-of-Week Review
**Time:** Friday 4:00 PM (30 min video call)
**Topic:** Week summary, next week planning

### Blocking Issues
**Channel:** #blockers (get response in 30 min-1 hour)
**Format:** Use template in COMMUNICATION_PLAN.md

**Contact:** Sean Hunt (Project Owner)

---

## 🆘 Troubleshooting

### Camera Not Found
```bash
# Verify camera is powered and on WiFi
ping 10.10.10.207

# Test connection manually
curl -u root:***REMOVED*** http://10.10.10.207/mjpeg
```

### Web UI Not Loading
```bash
# Check if the server is running
python meter_preview_ui.py --port 5001

# Test with different port if 5001 is busy
python meter_preview_ui.py --port 5002

# Access in browser
open http://localhost:5001
```

### Camera Preset Not Applying
```bash
# Test preset directly
python camera_presets.py day_clear

# Check available presets
python camera_presets.py --list

# Verify camera is accessible
ping <camera_ip>
```

### Docker Services Not Starting
```bash
# Check logs
docker-compose logs influxdb
docker-compose logs grafana

# Restart services
docker-compose restart
docker-compose ps  # Verify both are running
```

### API Calls Failing
```bash
# Verify API key is set
echo $ANTHROPIC_API_KEY  # Should show sk-ant-...

# Check recent logs
python view_logs.py --tail
```

### Credentials Not Loading
```bash
# Verify .env.local exists
ls -la .env.local  # Should show -rw------- (600 permissions)

# Verify source command works
source .env.local
echo $GRAFANA_PASSWORD  # Should show password
```

---

## 📖 Additional Resources

- [Claude API Docs](https://docs.anthropic.com/) - Vision API usage
- [InfluxDB Docs](https://docs.influxdata.com/) - Time-series database
- [Grafana Docs](https://grafana.com/docs/) - Dashboards
- [Thingino Firmware](https://github.com/ThingIno/ThingIno) - Camera firmware
- [Wyze Cam V2](https://wyze.com/) - Hardware info

---

## 📝 License

MIT

---

## 🎯 Success Criteria

### Week 1
- ✅ All coordination documents created
- ✅ Team assignments made
- ✅ Code structure ready
- ✅ Configuration system designed
- ✅ Infrastructure provisioned
- ⏳ 95%+ test coverage

### Week 2
- ⏳ 3 meters monitored simultaneously
- ⏳ Multi-meter orchestrator working
- ⏳ InfluxDB populated with real data

### Week 3
- ⏳ Real-time dashboards complete
- ⏳ Cost tracking working
- ⏳ Alerts configured

### Week 4
- ⏳ Production-ready system
- ⏳ Team trained
- ⏳ Documentation complete

---

**Last Updated:** November 18, 2025
**Status:** Week 1 Foundation In Progress - Camera Controls Complete
**Next Update:** Friday EOD, Week 1
**Owner:** Sean Hunt
