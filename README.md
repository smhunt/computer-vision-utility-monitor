# Water Meter Monitor with Computer Vision

Monitor your water meter automatically using a Wyze Cam V2 and Claude's vision AI.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export WYZE_CAM_IP=192.168.1.100        # Your camera IP
export WYZE_CAM_PASS=ismart12           # Your camera password
```

### 3. Run the Monitor

```bash
python wyze_cam_monitor.py
```

## What You Need

- **Wyze Cam V2** with [Dafang Hacks firmware](https://github.com/EliasKotlyar/Xiaomi-Dafang-Hacks)
- **Anthropic API key** (get one at https://console.anthropic.com/)
- **Python 3.8+**

## Project Structure

```
computer-vision-utility-monitor/
├── wyze_cam_monitor.py      # Main monitoring script
├── src/
│   └── llm_reader.py         # Claude vision API integration
├── logs/
│   └── readings.jsonl        # Reading history (auto-created)
├── requirements.txt          # Python dependencies
└── docs/
    ├── WYZE_QUICKSTART.md    # 30-minute setup guide
    ├── WYZE_CAM_V2_SETUP.md  # Detailed camera setup
    └── WYZE_CAM_V2_INTEGRATION.md
```

## Documentation

- **[WYZE_QUICKSTART.md](WYZE_QUICKSTART.md)** - Start here! 30-minute setup guide
- **[WYZE_CAM_V2_SETUP.md](WYZE_CAM_V2_SETUP.md)** - Complete camera setup documentation
- **[WYZE_CAM_V2_INTEGRATION.md](WYZE_CAM_V2_INTEGRATION.md)** - Integration details

## Features

- Automatic water meter reading using AI vision
- 10-minute reading intervals (configurable)
- Flow rate calculation and leak detection
- High flow alerts
- JSON logging of all readings
- Optional MQTT publishing for Home Assistant
- Works with both digital and analog dial meters

## Usage

### Test Camera Connection

```bash
curl --user root:ismart12 http://192.168.1.100/cgi-bin/currentpic.cgi -o test.jpg
open test.jpg
```

### Test Meter Reading

```bash
python src/llm_reader.py test.jpg
```

### Start Monitoring

```bash
python wyze_cam_monitor.py
```

## Cost

- **Hardware**: ~$5 (MicroSD card - you have the camera!)
- **Monthly**: ~$1 (power + API calls)
- **Year 1**: ~$17 total

## Support

Having issues? Check:
- Camera is powered and connected to WiFi
- Dafang Hacks firmware is installed
- Camera IP address is correct
- API key is set

## License

MIT
