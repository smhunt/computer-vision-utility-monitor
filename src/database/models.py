#!/usr/bin/env python3
"""
SQLAlchemy models for utility monitor database
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column, Integer, String, Boolean, Numeric, DateTime,
    ForeignKey, Text, Date, CheckConstraint, Index
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


class Meter(Base):
    """Meter configuration and metadata"""
    __tablename__ = 'meters'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    type = Column(String(20), nullable=False)
    location = Column(String(200))
    unit = Column(String(20), nullable=False)

    # Camera configuration
    camera_ip = Column(String(45))
    camera_user = Column(String(50))
    camera_preset = Column(String(50))
    camera_enabled = Column(Boolean, default=True)

    # Meter reading configuration
    reading_interval_minutes = Column(Integer, default=60)
    confidence_threshold = Column(String(20), default='medium')

    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    # Relationships
    snapshots = relationship("Snapshot", back_populates="meter", cascade="all, delete-orphan")
    bills = relationship("Bill", back_populates="meter", cascade="all, delete-orphan")
    rate_plans = relationship("RatePlan", back_populates="meter", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="meter", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(type.in_(['water', 'electric', 'gas']), name='check_meter_type'),
        Index('idx_meters_type', 'type'),
        Index('idx_meters_active', 'is_active'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'location': self.location,
            'unit': self.unit,
            'camera_ip': self.camera_ip,
            'camera_user': self.camera_user,
            'camera_preset': self.camera_preset,
            'camera_enabled': self.camera_enabled,
            'reading_interval_minutes': self.reading_interval_minutes,
            'confidence_threshold': self.confidence_threshold,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active,
        }


class Snapshot(Base):
    """Meter snapshot metadata"""
    __tablename__ = 'snapshots'

    id = Column(Integer, primary_key=True)
    meter_id = Column(Integer, ForeignKey('meters.id', ondelete='CASCADE'), nullable=False)

    # Snapshot information
    timestamp = Column(DateTime, nullable=False)
    file_path = Column(String(500), nullable=False)

    # Reading data
    total_reading = Column(Numeric(12, 3))
    digital_reading = Column(Numeric(12, 3))
    dial_reading = Column(Numeric(12, 3))
    confidence = Column(String(20))

    # Environmental data
    temperature_c = Column(Numeric(5, 2))

    # Processing status
    processed = Column(Boolean, default=False)
    processing_time_ms = Column(Integer)
    error_message = Column(Text)

    # API usage tracking
    api_model = Column(String(50))
    api_tokens_input = Column(Integer)
    api_tokens_output = Column(Integer)
    api_cost_usd = Column(Numeric(10, 6))

    # Metadata
    created_at = Column(DateTime, default=func.now())

    # Relationships
    meter = relationship("Meter", back_populates="snapshots")

    __table_args__ = (
        CheckConstraint(confidence.in_(['high', 'medium', 'low']), name='check_confidence'),
        Index('idx_snapshots_meter_id', 'meter_id'),
        Index('idx_snapshots_timestamp', 'timestamp', postgresql_using='btree', postgresql_ops={'timestamp': 'DESC'}),
        Index('idx_snapshots_processed', 'processed'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'meter_id': self.meter_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'file_path': self.file_path,
            'total_reading': float(self.total_reading) if self.total_reading else None,
            'digital_reading': float(self.digital_reading) if self.digital_reading else None,
            'dial_reading': float(self.dial_reading) if self.dial_reading else None,
            'confidence': self.confidence,
            'temperature_c': float(self.temperature_c) if self.temperature_c else None,
            'processed': self.processed,
            'processing_time_ms': self.processing_time_ms,
            'error_message': self.error_message,
            'api_model': self.api_model,
            'api_tokens_input': self.api_tokens_input,
            'api_tokens_output': self.api_tokens_output,
            'api_cost_usd': float(self.api_cost_usd) if self.api_cost_usd else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Bill(Base):
    """Utility bill uploads and parsed data"""
    __tablename__ = 'bills'

    id = Column(Integer, primary_key=True)
    meter_id = Column(Integer, ForeignKey('meters.id', ondelete='CASCADE'), nullable=False)

    # Bill identification
    account_number = Column(String(100))
    provider = Column(String(200))

    # Billing period
    billing_period_start = Column(Date)
    billing_period_end = Column(Date)
    billing_date = Column(Date)
    due_date = Column(Date)

    # Usage and cost
    total_amount = Column(Numeric(10, 2))
    usage = Column(Numeric(12, 3))

    # File information
    source_file = Column(String(500))
    uploaded_at = Column(DateTime, default=func.now())

    # AI-parsed data (stored as JSONB for flexibility)
    parsed_data = Column(JSONB)

    # Processing metadata
    parsing_confidence = Column(String(20))
    api_model = Column(String(50))

    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    meter = relationship("Meter", back_populates="bills")

    __table_args__ = (
        Index('idx_bills_meter_id', 'meter_id'),
        Index('idx_bills_billing_period', 'billing_period_start', 'billing_period_end'),
        Index('idx_bills_parsed_data', 'parsed_data', postgresql_using='gin'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'meter_id': self.meter_id,
            'account_number': self.account_number,
            'provider': self.provider,
            'billing_period_start': self.billing_period_start.isoformat() if self.billing_period_start else None,
            'billing_period_end': self.billing_period_end.isoformat() if self.billing_period_end else None,
            'billing_date': self.billing_date.isoformat() if self.billing_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'total_amount': float(self.total_amount) if self.total_amount else None,
            'usage': float(self.usage) if self.usage else None,
            'source_file': self.source_file,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'parsed_data': self.parsed_data,
            'parsing_confidence': self.parsing_confidence,
            'api_model': self.api_model,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class RatePlan(Base):
    """Utility rate plans for cost calculations"""
    __tablename__ = 'rate_plans'

    id = Column(Integer, primary_key=True)
    meter_id = Column(Integer, ForeignKey('meters.id', ondelete='CASCADE'), nullable=False)

    # Rate plan details
    name = Column(String(200))
    effective_date = Column(Date, nullable=False)
    end_date = Column(Date)

    # Rate structure (JSONB for complex pricing)
    rate_data = Column(JSONB, nullable=False)

    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    meter = relationship("Meter", back_populates="rate_plans")

    __table_args__ = (
        Index('idx_rate_plans_meter_id', 'meter_id'),
        Index('idx_rate_plans_effective', 'effective_date', postgresql_using='btree', postgresql_ops={'effective_date': 'DESC'}),
        Index('idx_rate_plans_active', 'is_active'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'meter_id': self.meter_id,
            'name': self.name,
            'effective_date': self.effective_date.isoformat() if self.effective_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'rate_data': self.rate_data,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class Alert(Base):
    """Alert rules configuration"""
    __tablename__ = 'alerts'

    id = Column(Integer, primary_key=True)
    meter_id = Column(Integer, ForeignKey('meters.id', ondelete='CASCADE'))

    # Alert configuration
    name = Column(String(200), nullable=False)
    type = Column(String(50), nullable=False)

    # Alert conditions (JSONB)
    conditions = Column(JSONB, nullable=False)

    # Notification settings
    notification_channels = Column(JSONB)

    # Status
    is_active = Column(Boolean, default=True)
    last_triggered = Column(DateTime)
    trigger_count = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    meter = relationship("Meter", back_populates="alerts")
    history = relationship("AlertHistory", back_populates="alert", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(
            type.in_(['threshold', 'anomaly', 'leak', 'high_usage', 'custom']),
            name='check_alert_type'
        ),
        Index('idx_alerts_meter_id', 'meter_id'),
        Index('idx_alerts_active', 'is_active'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'meter_id': self.meter_id,
            'name': self.name,
            'type': self.type,
            'conditions': self.conditions,
            'notification_channels': self.notification_channels,
            'is_active': self.is_active,
            'last_triggered': self.last_triggered.isoformat() if self.last_triggered else None,
            'trigger_count': self.trigger_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class AlertHistory(Base):
    """History of triggered alerts"""
    __tablename__ = 'alert_history'

    id = Column(Integer, primary_key=True)
    alert_id = Column(Integer, ForeignKey('alerts.id', ondelete='CASCADE'), nullable=False)
    meter_id = Column(Integer, ForeignKey('meters.id', ondelete='SET NULL'))

    # Alert event details
    triggered_at = Column(DateTime, default=func.now())
    value = Column(Numeric(12, 3))
    threshold = Column(Numeric(12, 3))
    message = Column(Text)

    # Notification status
    notification_sent = Column(Boolean, default=False)
    notification_error = Column(Text)

    # Resolution
    acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime)
    acknowledged_by = Column(String(100))
    notes = Column(Text)

    # Relationships
    alert = relationship("Alert", back_populates="history")

    __table_args__ = (
        Index('idx_alert_history_alert_id', 'alert_id'),
        Index('idx_alert_history_triggered', 'triggered_at', postgresql_using='btree', postgresql_ops={'triggered_at': 'DESC'}),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'alert_id': self.alert_id,
            'meter_id': self.meter_id,
            'triggered_at': self.triggered_at.isoformat() if self.triggered_at else None,
            'value': float(self.value) if self.value else None,
            'threshold': float(self.threshold) if self.threshold else None,
            'message': self.message,
            'notification_sent': self.notification_sent,
            'notification_error': self.notification_error,
            'acknowledged': self.acknowledged,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'acknowledged_by': self.acknowledged_by,
            'notes': self.notes,
        }


class UserSettings(Base):
    """User preferences and dashboard settings"""
    __tablename__ = 'user_settings'

    id = Column(Integer, primary_key=True)
    user_id = Column(String(100), unique=True, nullable=False)

    # Dashboard preferences
    theme = Column(String(20), default='auto')
    timezone = Column(String(50), default='America/Toronto')
    default_view = Column(String(50), default='dashboard')

    # Display preferences (JSONB)
    preferences = Column(JSONB)

    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint(theme.in_(['light', 'dark', 'auto']), name='check_theme'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'theme': self.theme,
            'timezone': self.timezone,
            'default_view': self.default_view,
            'preferences': self.preferences,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
