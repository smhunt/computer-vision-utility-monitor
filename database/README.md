# Database Setup Guide

This directory contains PostgreSQL database schema and migration tools for the utility monitor.

## Architecture

The app uses a **hybrid database approach**:

- **InfluxDB** - Time-series meter readings (for dashboards and graphs)
- **PostgreSQL** - Relational data (meters, bills, snapshots metadata, settings)

## Quick Start

### 1. Start PostgreSQL

```bash
# From project root
docker-compose up -d postgres

# Verify it's running
docker-compose ps
```

### 2. Set Environment Variables

Add to your `.env` or `.env.local` file:

```bash
# PostgreSQL Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=utility_monitor
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password  # Change this!
```

### 3. Initialize Database

The database schema will be automatically created when the container starts (via `init.sql`).

To manually initialize or reset:

```bash
# Test connection
python -m src.database.connection

# Initialize schema (creates tables)
python -m src.database.connection --init

# Reset database (⚠️ DROPS ALL TABLES)
python -m src.database.connection --reset
```

### 4. Migrate Existing Data

If you have existing data in JSONL files or config files:

```bash
# Run migration script
python database/migrate_to_postgres.py
```

This will migrate:
- Meter configurations from YAML/JSON
- Snapshot data from JSONL files
- Bill data from pricing.json

## Database Schema

### Tables

1. **meters** - Meter configuration (name, type, location, camera settings)
2. **snapshots** - Snapshot metadata (timestamp, readings, confidence, API usage)
3. **bills** - Utility bills (parsed data, costs, usage)
4. **rate_plans** - Pricing/rate information (time-of-use, tiered rates)
5. **alerts** - Alert rules (thresholds, anomalies, leak detection)
6. **alert_history** - Alert trigger history
7. **user_settings** - Dashboard preferences (theme, timezone)

### Views

- **latest_snapshots** - Most recent snapshot per meter
- **active_alerts** - Currently active alerts with trigger counts

## API Endpoints

### Meters

```bash
# Get all meters
GET /api/db/meters

# Get specific meter
GET /api/db/meters/{meter_id}

# Create meter
POST /api/db/meters
{
  "name": "water_main",
  "type": "water",
  "unit": "m³",
  "location": "Basement",
  "camera_ip": "10.10.10.207"
}

# Update meter
PUT /api/db/meters/{meter_id}
```

### Snapshots

```bash
# Get snapshots for meter
GET /api/db/snapshots/{meter_id}?limit=100&processed=true

# Create snapshot
POST /api/db/snapshots
{
  "meter_id": 1,
  "timestamp": "2025-01-15T10:30:00Z",
  "file_path": "logs/snapshots/water_main/snapshot_001.jpg",
  "total_reading": 22.712,
  "confidence": "high"
}
```

### Bills

```bash
# Get bills for meter
GET /api/db/bills/{meter_id}

# Create bill
POST /api/db/bills
{
  "meter_id": 1,
  "billing_period_start": "2025-01-01",
  "billing_period_end": "2025-01-31",
  "total_amount": 85.50,
  "usage": 12.5,
  "parsed_data": {...}
}
```

### Settings

```bash
# Get user settings
GET /api/db/settings/{user_id}

# Update settings
PUT /api/db/settings/{user_id}
{
  "theme": "dark",
  "timezone": "America/Toronto"
}
```

### Health Check

```bash
# Database health
GET /api/db/health
```

## Usage in Python

### Basic Query

```python
from src.database import get_db_session, Meter

# Get all active meters
with get_db_session() as session:
    meters = session.query(Meter).filter_by(is_active=True).all()
    for meter in meters:
        print(f"{meter.name}: {meter.type}")
```

### Create Record

```python
from src.database import get_db_session, Meter

with get_db_session() as session:
    meter = Meter(
        name='water_main',
        type='water',
        unit='m³',
        location='Basement',
        camera_ip='10.10.10.207'
    )
    session.add(meter)
    # Commit happens automatically when context exits
```

### Create Snapshot

```python
from src.database import get_db_session, Snapshot
from datetime import datetime

with get_db_session() as session:
    snapshot = Snapshot(
        meter_id=1,
        timestamp=datetime.utcnow(),
        file_path='logs/snapshots/water_main/snapshot_001.jpg',
        total_reading=22.712,
        confidence='high',
        processed=True
    )
    session.add(snapshot)
```

## Backup & Restore

### Backup

```bash
# Backup entire database
docker exec utility-monitor-postgres pg_dump -U postgres utility_monitor > backup.sql

# Backup specific table
docker exec utility-monitor-postgres pg_dump -U postgres -t meters utility_monitor > meters_backup.sql
```

### Restore

```bash
# Restore from backup
docker exec -i utility-monitor-postgres psql -U postgres utility_monitor < backup.sql
```

## Monitoring

### Connect to PostgreSQL CLI

```bash
docker exec -it utility-monitor-postgres psql -U postgres -d utility_monitor
```

### Useful Queries

```sql
-- Count records per table
SELECT 'meters' as table, COUNT(*) FROM meters
UNION ALL
SELECT 'snapshots', COUNT(*) FROM snapshots
UNION ALL
SELECT 'bills', COUNT(*) FROM bills;

-- Latest snapshots per meter
SELECT * FROM latest_snapshots;

-- Meter reading statistics
SELECT
    m.name,
    COUNT(s.id) as snapshot_count,
    MAX(s.timestamp) as latest_reading,
    AVG(s.total_reading) as avg_reading
FROM meters m
LEFT JOIN snapshots s ON m.id = s.meter_id
GROUP BY m.id, m.name;

-- Active alerts
SELECT * FROM active_alerts;
```

## Troubleshooting

### Connection Refused

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres
```

### Permission Denied

```bash
# Ensure environment variables are set
echo $POSTGRES_PASSWORD

# Test connection manually
docker exec -it utility-monitor-postgres psql -U postgres -d utility_monitor
```

### Migration Errors

```bash
# Check database connection first
python -m src.database.connection

# Run migration with verbose output
python database/migrate_to_postgres.py
```

## Production Considerations

1. **Change default password** in docker-compose.yml
2. **Use environment variables** for credentials (never commit passwords)
3. **Enable SSL/TLS** for remote connections
4. **Set up regular backups** (pg_dump + cron)
5. **Configure connection pooling** in production
6. **Monitor query performance** (enable pg_stat_statements)
7. **Set up replication** for high availability

## Schema Updates

To update the schema:

1. Modify `init.sql`
2. Create migration script for existing data
3. Test on development database
4. Apply to production with backup

## React Dashboard Integration

The React dashboard (dashboard/) consumes these database APIs and displays the data using:
- **shadcn/ui** components (Card, Badge, Button, Separator)
- **TanStack Query** for API data fetching
- **TypeScript** for type-safe API consumption

The dashboard automatically fetches:
- Latest meter readings from `/api/db/meters`
- Historical data for charts
- Cost calculations from pricing configuration
- Alert information and triggers

See [dashboard/README.md](../dashboard/README.md) for more information.

## Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [Docker PostgreSQL](https://hub.docker.com/_/postgres)
- [shadcn/ui Documentation](https://ui.shadcn.com/)
