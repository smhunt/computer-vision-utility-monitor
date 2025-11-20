# Database Integration Complete! 🎉

Your utility monitor now has **PostgreSQL** integrated alongside **InfluxDB** for a hybrid database architecture.

## What's New

### ✅ PostgreSQL Database
- **Location**: Docker container `utility-monitor-postgres`
- **Port**: 5432
- **Database**: `utility_monitor`
- **User**: `postgres`
- **Password**: `***REMOVED***` (configured in [.env](file:///Users/seanhunt/Code/computer-vision-utility-monitor/.env))

### ✅ Database Schema
7 tables created:
- `meters` - Meter configuration (name, type, camera settings)
- `snapshots` - Snapshot metadata and readings
- `bills` - Utility bill uploads and parsed data
- `rate_plans` - Pricing/rate information
- `alerts` - Alert rules configuration
- `alert_history` - Alert trigger history
- `user_settings` - Dashboard preferences

### ✅ Flask API Routes
New database-backed endpoints:
- `GET /api/db/meters` - List all meters
- `GET /api/db/meters/{id}` - Get specific meter
- `POST /api/db/meters` - Create new meter
- `PUT /api/db/meters/{id}` - Update meter
- `GET /api/db/snapshots/{meter_id}` - Get meter snapshots
- `POST /api/db/snapshots` - Create snapshot record
- `GET /api/db/bills/{meter_id}` - Get meter bills
- `POST /api/db/bills` - Create bill record
- `GET /api/db/health` - Database health check

### ✅ Sample Data
3 meters seeded:
- `water_main` (Basement, 10.10.10.207)
- `electric_main` (Garage, 10.10.10.208)
- `gas_main` (Exterior, 10.10.10.209)

---

## Quick Start

### 1. Start PostgreSQL

```bash
docker compose up -d postgres
```

### 2. View Meters in Database

```bash
# Via PostgreSQL CLI
docker exec utility-monitor-postgres psql -U postgres -d utility_monitor -c "SELECT * FROM meters;"

# Via Flask API (start server first)
curl http://localhost:2500/api/db/meters | jq
```

### 3. Start Flask Server

```bash
python3 meter_preview_ui.py --port 2500
```

Access:
- Main Dashboard: http://localhost:2500
- Database API: http://localhost:2500/api/db/meters

---

## IDE Integration

### VS Code Database Connection

1. **Install Extension**: [SQLTools](https://marketplace.visualstudio.com/items?itemName=mtxr.sqltools) + [SQLTools PostgreSQL Driver](https://marketplace.visualstudio.com/items?itemName=mtxr.sqltools-driver-pg)

2. **Connect**: Use the connection settings in [.vscode/settings.json](file:///Users/seanhunt/Code/computer-vision-utility-monitor/.vscode/settings.json)
   - Name: `Utility Monitor DB`
   - Host: `localhost`
   - Port: `5432`
   - Database: `utility_monitor`
   - User: `postgres`
   - Password: `***REMOVED***`

3. **Browse Tables**: Open SQLTools sidebar → Connect → Browse tables

---

## Architecture

### Hybrid Database Approach

```
┌─────────────────────────────────────────────────────────┐
│                  Flask Web Application                  │
│                (meter_preview_ui.py)                    │
└────────────────┬────────────────┬───────────────────────┘
                 │                │
    ┌────────────▼───────┐  ┌────▼──────────┐
    │   PostgreSQL       │  │   InfluxDB     │
    │                    │  │                │
    │ • Meters           │  │ • Time-series  │
    │ • Snapshots        │  │   readings     │
    │ • Bills            │  │ • Consumption  │
    │ • Rate Plans       │  │   metrics      │
    │ • Alerts           │  │                │
    │ • User Settings    │  │                │
    └────────────────────┘  └────────────────┘
```

**Why Both?**
- **PostgreSQL**: Structured data (configuration, bills, metadata)
- **InfluxDB**: Time-series data (meter readings over time, graphs)

---

## Common Tasks

### View All Meters

```bash
# PostgreSQL CLI
docker exec utility-monitor-postgres psql -U postgres -d utility_monitor

utility_monitor=# SELECT name, type, camera_ip, is_active FROM meters;

# Python
from src.database import get_db_session, Meter

with get_db_session() as session:
    meters = session.query(Meter).all()
    for meter in meters:
        print(f"{meter.name}: {meter.type}")
```

### Add a New Meter

```bash
# Via API
curl -X POST http://localhost:2500/api/db/meters \
  -H "Content-Type: application/json" \
  -d '{
    "name": "water_secondary",
    "type": "water",
    "unit": "m³",
    "location": "Garden",
    "camera_ip": "10.10.10.210",
    "reading_interval_minutes": 60
  }'

# Via Python
from src.database import get_db_session, Meter

with get_db_session() as session:
    meter = Meter(
        name='water_secondary',
        type='water',
        unit='m³',
        location='Garden',
        camera_ip='10.10.10.210'
    )
    session.add(meter)
    # Auto-commits on context exit
```

### Link Meter Click to Detail Page

When viewing meters in the UI, you can now click on a meter to see its details. The meter data comes from PostgreSQL:

1. **List View**: Queries `GET /api/db/meters` to display all meters
2. **Click Meter**: Navigates to `/meter/{meter_name}`
3. **Detail View**: Queries meter config from PostgreSQL, snapshots from InfluxDB

---

## Database Utilities

### Backup Database

```bash
# Full backup
docker exec utility-monitor-postgres pg_dump -U postgres utility_monitor > backup.sql

# Meters only
docker exec utility-monitor-postgres pg_dump -U postgres -t meters utility_monitor > meters_backup.sql
```

### Restore Database

```bash
docker exec -i utility-monitor-postgres psql -U postgres utility_monitor < backup.sql
```

### Reset Database

```bash
python3 -m src.database.connection --reset
```

⚠️ **Warning**: This will drop all tables and data!

### Migrate Existing Data

```bash
python3 database/migrate_to_postgres.py
```

Migrates:
- Meters from `config/meters.yaml`
- Snapshots from `logs/*_readings.jsonl`
- Bills from `config/pricing.json`

---

## Testing

### Integration Test

```bash
python3 database/test_integration.py
```

Tests all database models (CRUD operations).

### API Test

```bash
# Health check
curl http://localhost:2500/api/db/health

# Get meters
curl http://localhost:2500/api/db/meters | jq

# Get specific meter
curl http://localhost:2500/api/db/meters/2 | jq
```

---

## Next Steps

1. **Update Meter Reading Scripts**: Save snapshot metadata to PostgreSQL when capturing readings
2. **Dashboard Integration**: Display meters from PostgreSQL in React dashboard
3. **Bill Upload**: Store uploaded bills in PostgreSQL with AI-parsed data
4. **Alerts**: Configure alert rules in PostgreSQL
5. **Analytics**: Query both databases for comprehensive insights

---

## Troubleshooting

### PostgreSQL Not Running

```bash
docker compose ps postgres
docker compose logs postgres
docker compose restart postgres
```

### Connection Errors

Check environment variables in [.env](file:///Users/seanhunt/Code/computer-vision-utility-monitor/.env):
```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=utility_monitor
POSTGRES_USER=postgres
POSTGRES_PASSWORD=***REMOVED***
```

### API Routes Not Working

Ensure Flask server is running and database routes are registered:
```bash
python3 meter_preview_ui.py --port 2500
```

Look for: `✅ Database API routes registered`

---

## Documentation

- Database Schema: [database/init.sql](file:///Users/seanhunt/Code/computer-vision-utility-monitor/database/init.sql)
- Models: [src/database/models.py](file:///Users/seanhunt/Code/computer-vision-utility-monitor/src/database/models.py)
- API Routes: [src/api_routes.py](file:///Users/seanhunt/Code/computer-vision-utility-monitor/src/api_routes.py)
- Migration Script: [database/migrate_to_postgres.py](file:///Users/seanhunt/Code/computer-vision-utility-monitor/database/migrate_to_postgres.py)
- Full Guide: [database/README.md](file:///Users/seanhunt/Code/computer-vision-utility-monitor/database/README.md)

---

**Database integration complete! 🎉**

You now have a production-ready PostgreSQL database integrated with your utility monitor system.
