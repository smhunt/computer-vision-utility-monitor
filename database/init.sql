-- Utility Monitor Database Schema
-- PostgreSQL initialization script

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- METERS TABLE
-- Stores meter configuration and metadata
-- ============================================================
CREATE TABLE meters (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('water', 'electric', 'gas')),
    location VARCHAR(200),
    unit VARCHAR(20) NOT NULL,

    -- Camera configuration
    camera_ip VARCHAR(45),
    camera_user VARCHAR(50),
    camera_preset VARCHAR(50),
    camera_enabled BOOLEAN DEFAULT TRUE,

    -- Meter reading configuration
    reading_interval_minutes INTEGER DEFAULT 60,
    confidence_threshold VARCHAR(20) DEFAULT 'medium',

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Index for faster lookups
CREATE INDEX idx_meters_type ON meters(type);
CREATE INDEX idx_meters_active ON meters(is_active);

-- ============================================================
-- SNAPSHOTS TABLE
-- Stores metadata about meter snapshots
-- ============================================================
CREATE TABLE snapshots (
    id SERIAL PRIMARY KEY,
    meter_id INTEGER NOT NULL REFERENCES meters(id) ON DELETE CASCADE,

    -- Snapshot information
    timestamp TIMESTAMP NOT NULL,
    file_path VARCHAR(500) NOT NULL,

    -- Reading data
    total_reading NUMERIC(12, 3),
    digital_reading NUMERIC(12, 3),
    dial_reading NUMERIC(12, 3),
    confidence VARCHAR(20) CHECK (confidence IN ('high', 'medium', 'low')),

    -- Environmental data
    temperature_c NUMERIC(5, 2),

    -- Processing status
    processed BOOLEAN DEFAULT FALSE,
    processing_time_ms INTEGER,
    error_message TEXT,

    -- API usage tracking
    api_model VARCHAR(50),
    api_tokens_input INTEGER,
    api_tokens_output INTEGER,
    api_cost_usd NUMERIC(10, 6),

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_snapshots_meter_id ON snapshots(meter_id);
CREATE INDEX idx_snapshots_timestamp ON snapshots(timestamp DESC);
CREATE INDEX idx_snapshots_processed ON snapshots(processed);

-- ============================================================
-- BILLS TABLE
-- Stores uploaded utility bills and AI-parsed data
-- ============================================================
CREATE TABLE bills (
    id SERIAL PRIMARY KEY,
    meter_id INTEGER NOT NULL REFERENCES meters(id) ON DELETE CASCADE,

    -- Bill identification
    account_number VARCHAR(100),
    provider VARCHAR(200),

    -- Billing period
    billing_period_start DATE,
    billing_period_end DATE,
    billing_date DATE,
    due_date DATE,

    -- Usage and cost
    total_amount NUMERIC(10, 2),
    usage NUMERIC(12, 3),

    -- File information
    source_file VARCHAR(500),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- AI-parsed data (stored as JSONB for flexibility)
    parsed_data JSONB,

    -- Processing metadata
    parsing_confidence VARCHAR(20),
    api_model VARCHAR(50),

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_bills_meter_id ON bills(meter_id);
CREATE INDEX idx_bills_billing_period ON bills(billing_period_start, billing_period_end);
CREATE INDEX idx_bills_parsed_data ON bills USING GIN (parsed_data);

-- ============================================================
-- RATE_PLANS TABLE
-- Stores pricing/rate information for cost calculations
-- ============================================================
CREATE TABLE rate_plans (
    id SERIAL PRIMARY KEY,
    meter_id INTEGER NOT NULL REFERENCES meters(id) ON DELETE CASCADE,

    -- Rate plan details
    name VARCHAR(200),
    effective_date DATE NOT NULL,
    end_date DATE,

    -- Rate structure (stored as JSONB for complex pricing)
    -- Example: time-of-use rates, tiered pricing, seasonal rates
    rate_data JSONB NOT NULL,

    -- Metadata
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_rate_plans_meter_id ON rate_plans(meter_id);
CREATE INDEX idx_rate_plans_effective ON rate_plans(effective_date DESC);
CREATE INDEX idx_rate_plans_active ON rate_plans(is_active);

-- ============================================================
-- ALERTS TABLE
-- Stores alert rules and notification history
-- ============================================================
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    meter_id INTEGER REFERENCES meters(id) ON DELETE CASCADE,

    -- Alert configuration
    name VARCHAR(200) NOT NULL,
    type VARCHAR(50) NOT NULL CHECK (type IN ('threshold', 'anomaly', 'leak', 'high_usage', 'custom')),

    -- Alert conditions (stored as JSONB)
    conditions JSONB NOT NULL,

    -- Notification settings
    notification_channels JSONB, -- email, sms, webhook, etc.

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    last_triggered TIMESTAMP,
    trigger_count INTEGER DEFAULT 0,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_alerts_meter_id ON alerts(meter_id);
CREATE INDEX idx_alerts_active ON alerts(is_active);

-- ============================================================
-- ALERT_HISTORY TABLE
-- Stores history of triggered alerts
-- ============================================================
CREATE TABLE alert_history (
    id SERIAL PRIMARY KEY,
    alert_id INTEGER NOT NULL REFERENCES alerts(id) ON DELETE CASCADE,
    meter_id INTEGER REFERENCES meters(id) ON DELETE SET NULL,

    -- Alert event details
    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    value NUMERIC(12, 3),
    threshold NUMERIC(12, 3),
    message TEXT,

    -- Notification status
    notification_sent BOOLEAN DEFAULT FALSE,
    notification_error TEXT,

    -- Resolution
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_at TIMESTAMP,
    acknowledged_by VARCHAR(100),
    notes TEXT
);

CREATE INDEX idx_alert_history_alert_id ON alert_history(alert_id);
CREATE INDEX idx_alert_history_triggered ON alert_history(triggered_at DESC);

-- ============================================================
-- USER_SETTINGS TABLE
-- Stores user preferences and dashboard settings
-- ============================================================
CREATE TABLE user_settings (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) UNIQUE NOT NULL, -- For future multi-user support

    -- Dashboard preferences
    theme VARCHAR(20) DEFAULT 'auto' CHECK (theme IN ('light', 'dark', 'auto')),
    timezone VARCHAR(50) DEFAULT 'America/Toronto',
    default_view VARCHAR(50) DEFAULT 'dashboard',

    -- Display preferences
    preferences JSONB,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- FUNCTIONS & TRIGGERS
-- ============================================================

-- Function to update 'updated_at' timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_meters_updated_at BEFORE UPDATE ON meters
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_bills_updated_at BEFORE UPDATE ON bills
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_rate_plans_updated_at BEFORE UPDATE ON rate_plans
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_alerts_updated_at BEFORE UPDATE ON alerts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_settings_updated_at BEFORE UPDATE ON user_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- INITIAL DATA
-- ============================================================

-- Insert default user settings
INSERT INTO user_settings (user_id, theme, timezone, preferences) VALUES
('default', 'auto', 'America/Toronto', '{"auto_refresh": true, "refresh_interval": 60}');

-- Insert example meters (commented out - uncomment to use)
-- INSERT INTO meters (name, type, location, unit, camera_ip, reading_interval_minutes) VALUES
-- ('water_main', 'water', 'Basement', 'm³', '10.10.10.207', 60),
-- ('electric_main', 'electric', 'Garage', 'kWh', '10.10.10.208', 15),
-- ('gas_main', 'gas', 'Exterior', 'm³', '10.10.10.209', 60);

-- ============================================================
-- VIEWS
-- ============================================================

-- View for latest snapshot per meter
CREATE VIEW latest_snapshots AS
SELECT DISTINCT ON (meter_id)
    s.*,
    m.name as meter_name,
    m.type as meter_type,
    m.unit as meter_unit
FROM snapshots s
JOIN meters m ON s.meter_id = m.id
WHERE s.processed = TRUE
ORDER BY meter_id, timestamp DESC;

-- View for active alerts
CREATE VIEW active_alerts AS
SELECT
    a.*,
    m.name as meter_name,
    m.type as meter_type,
    COUNT(ah.id) as trigger_count_24h
FROM alerts a
LEFT JOIN meters m ON a.meter_id = m.id
LEFT JOIN alert_history ah ON a.id = ah.alert_id
    AND ah.triggered_at > CURRENT_TIMESTAMP - INTERVAL '24 hours'
WHERE a.is_active = TRUE
GROUP BY a.id, m.name, m.type;

-- ============================================================
-- GRANTS (for application user)
-- ============================================================
-- CREATE USER utility_monitor_app WITH PASSWORD 'your_secure_password';
-- GRANT CONNECT ON DATABASE utility_monitor TO utility_monitor_app;
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO utility_monitor_app;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO utility_monitor_app;

-- ============================================================
-- COMPLETION
-- ============================================================
DO $$
BEGIN
    RAISE NOTICE 'Database schema initialized successfully!';
    RAISE NOTICE 'Created tables: meters, snapshots, bills, rate_plans, alerts, alert_history, user_settings';
    RAISE NOTICE 'Created views: latest_snapshots, active_alerts';
END $$;
