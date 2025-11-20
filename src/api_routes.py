#!/usr/bin/env python3
"""
Flask API routes with PostgreSQL integration
Database-backed endpoints for meters, bills, and configuration
"""

from flask import jsonify, request
from datetime import datetime
from typing import Dict, Any
import traceback

# Import database models and connection
try:
    from src.database import (
        get_db_session,
        Meter,
        Snapshot,
        Bill,
        RatePlan,
        UserSettings
    )
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    print("Warning: Database module not available. Install: pip install sqlalchemy psycopg2-binary")


def register_api_routes(app):
    """Register all database-backed API routes"""

    if not DB_AVAILABLE:
        print("⚠️  Database routes not registered (database module not available)")
        return

    # ============================================================
    # METER CONFIGURATION ENDPOINTS
    # ============================================================

    @app.route('/api/db/meters', methods=['GET'])
    def api_db_get_meters():
        """Get all meters from database"""
        try:
            with get_db_session() as session:
                meters = session.query(Meter).filter_by(is_active=True).all()

                # Meter display configuration (icons, colors, labels)
                meter_display = {
                    'water': {
                        'icon': 'droplets',
                        'label': 'Water Meter',
                        'color': '#3b82f6',
                        'lightColor': '#eff6ff',
                        'darkColor': '#1e3a8a',
                    },
                    'electric': {
                        'icon': 'zap',
                        'label': 'Electric Meter',
                        'color': '#eab308',
                        'lightColor': '#fefce8',
                        'darkColor': '#713f12',
                    },
                    'gas': {
                        'icon': 'flame',
                        'label': 'Gas Meter',
                        'color': '#f97316',
                        'lightColor': '#fff7ed',
                        'darkColor': '#7c2d12',
                    }
                }

                meters_data = []
                for meter in meters:
                    meter_dict = meter.to_dict()
                    meter_dict['display'] = meter_display.get(meter.type, {})
                    meters_data.append(meter_dict)

                return jsonify({
                    'status': 'success',
                    'meters': meters_data,
                    'count': len(meters_data)
                })

        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e),
                'traceback': traceback.format_exc()
            }), 500

    @app.route('/api/db/meters/<int:meter_id>', methods=['GET'])
    def api_db_get_meter(meter_id):
        """Get specific meter by ID"""
        try:
            with get_db_session() as session:
                meter = session.query(Meter).filter_by(id=meter_id).first()

                if not meter:
                    return jsonify({
                        'status': 'error',
                        'message': f'Meter {meter_id} not found'
                    }), 404

                return jsonify({
                    'status': 'success',
                    'meter': meter.to_dict()
                })

        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/db/meters', methods=['POST'])
    def api_db_create_meter():
        """Create a new meter"""
        try:
            data = request.get_json()

            with get_db_session() as session:
                # Check if meter with same name exists
                existing = session.query(Meter).filter_by(name=data['name']).first()
                if existing:
                    return jsonify({
                        'status': 'error',
                        'message': f'Meter with name {data["name"]} already exists'
                    }), 400

                # Create new meter
                meter = Meter(
                    name=data['name'],
                    type=data['type'],
                    location=data.get('location'),
                    unit=data['unit'],
                    camera_ip=data.get('camera_ip'),
                    camera_user=data.get('camera_user'),
                    camera_preset=data.get('camera_preset'),
                    camera_enabled=data.get('camera_enabled', True),
                    reading_interval_minutes=data.get('reading_interval_minutes', 60),
                    confidence_threshold=data.get('confidence_threshold', 'medium')
                )

                session.add(meter)
                session.flush()

                return jsonify({
                    'status': 'success',
                    'meter': meter.to_dict(),
                    'message': f'Meter {meter.name} created successfully'
                }), 201

        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e),
                'traceback': traceback.format_exc()
            }), 500

    @app.route('/api/db/meters/<int:meter_id>', methods=['PUT'])
    def api_db_update_meter(meter_id):
        """Update an existing meter"""
        try:
            data = request.get_json()

            with get_db_session() as session:
                meter = session.query(Meter).filter_by(id=meter_id).first()

                if not meter:
                    return jsonify({
                        'status': 'error',
                        'message': f'Meter {meter_id} not found'
                    }), 404

                # Update fields
                for key, value in data.items():
                    if hasattr(meter, key) and key not in ['id', 'created_at', 'updated_at']:
                        setattr(meter, key, value)

                session.flush()

                return jsonify({
                    'status': 'success',
                    'meter': meter.to_dict(),
                    'message': f'Meter {meter.name} updated successfully'
                })

        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    # ============================================================
    # SNAPSHOT ENDPOINTS
    # ============================================================

    @app.route('/api/db/snapshots/<int:meter_id>', methods=['GET'])
    def api_db_get_snapshots(meter_id):
        """Get snapshots for a meter"""
        try:
            limit = request.args.get('limit', 100, type=int)
            processed_only = request.args.get('processed', 'true').lower() == 'true'

            with get_db_session() as session:
                query = session.query(Snapshot).filter_by(meter_id=meter_id)

                if processed_only:
                    query = query.filter_by(processed=True)

                snapshots = query.order_by(Snapshot.timestamp.desc()).limit(limit).all()

                return jsonify({
                    'status': 'success',
                    'snapshots': [s.to_dict() for s in snapshots],
                    'count': len(snapshots)
                })

        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/db/snapshots', methods=['POST'])
    def api_db_create_snapshot():
        """Create a new snapshot record"""
        try:
            data = request.get_json()

            with get_db_session() as session:
                snapshot = Snapshot(
                    meter_id=data['meter_id'],
                    timestamp=datetime.fromisoformat(data['timestamp']),
                    file_path=data['file_path'],
                    total_reading=data.get('total_reading'),
                    digital_reading=data.get('digital_reading'),
                    dial_reading=data.get('dial_reading'),
                    confidence=data.get('confidence'),
                    temperature_c=data.get('temperature_c'),
                    processed=data.get('processed', True),
                    processing_time_ms=data.get('processing_time_ms'),
                    api_model=data.get('api_model'),
                    api_tokens_input=data.get('api_tokens_input'),
                    api_tokens_output=data.get('api_tokens_output'),
                    api_cost_usd=data.get('api_cost_usd')
                )

                session.add(snapshot)
                session.flush()

                return jsonify({
                    'status': 'success',
                    'snapshot': snapshot.to_dict(),
                    'message': 'Snapshot created successfully'
                }), 201

        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e),
                'traceback': traceback.format_exc()
            }), 500

    # ============================================================
    # BILL ENDPOINTS
    # ============================================================

    @app.route('/api/db/bills/<int:meter_id>', methods=['GET'])
    def api_db_get_bills(meter_id):
        """Get bills for a meter"""
        try:
            with get_db_session() as session:
                bills = session.query(Bill).filter_by(meter_id=meter_id)\
                    .order_by(Bill.billing_period_start.desc()).all()

                return jsonify({
                    'status': 'success',
                    'bills': [b.to_dict() for b in bills],
                    'count': len(bills)
                })

        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/db/bills', methods=['POST'])
    def api_db_create_bill():
        """Create a new bill record"""
        try:
            data = request.get_json()

            with get_db_session() as session:
                bill = Bill(
                    meter_id=data['meter_id'],
                    account_number=data.get('account_number'),
                    provider=data.get('provider'),
                    billing_period_start=datetime.fromisoformat(data['billing_period_start']).date() if data.get('billing_period_start') else None,
                    billing_period_end=datetime.fromisoformat(data['billing_period_end']).date() if data.get('billing_period_end') else None,
                    billing_date=datetime.fromisoformat(data['billing_date']).date() if data.get('billing_date') else None,
                    due_date=datetime.fromisoformat(data['due_date']).date() if data.get('due_date') else None,
                    total_amount=data.get('total_amount'),
                    usage=data.get('usage'),
                    source_file=data.get('source_file'),
                    parsed_data=data.get('parsed_data'),
                    parsing_confidence=data.get('parsing_confidence'),
                    api_model=data.get('api_model')
                )

                session.add(bill)
                session.flush()

                return jsonify({
                    'status': 'success',
                    'bill': bill.to_dict(),
                    'message': 'Bill created successfully'
                }), 201

        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e),
                'traceback': traceback.format_exc()
            }), 500

    # ============================================================
    # USER SETTINGS ENDPOINTS
    # ============================================================

    @app.route('/api/db/settings/<user_id>', methods=['GET'])
    def api_db_get_settings(user_id):
        """Get user settings"""
        try:
            with get_db_session() as session:
                settings = session.query(UserSettings).filter_by(user_id=user_id).first()

                if not settings:
                    # Create default settings
                    settings = UserSettings(
                        user_id=user_id,
                        theme='auto',
                        timezone='America/Toronto',
                        preferences={'auto_refresh': True, 'refresh_interval': 60}
                    )
                    session.add(settings)
                    session.flush()

                return jsonify({
                    'status': 'success',
                    'settings': settings.to_dict()
                })

        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/db/settings/<user_id>', methods=['PUT'])
    def api_db_update_settings(user_id):
        """Update user settings"""
        try:
            data = request.get_json()

            with get_db_session() as session:
                settings = session.query(UserSettings).filter_by(user_id=user_id).first()

                if not settings:
                    settings = UserSettings(user_id=user_id)
                    session.add(settings)

                # Update fields
                for key, value in data.items():
                    if hasattr(settings, key) and key not in ['id', 'user_id', 'created_at', 'updated_at']:
                        setattr(settings, key, value)

                session.flush()

                return jsonify({
                    'status': 'success',
                    'settings': settings.to_dict(),
                    'message': 'Settings updated successfully'
                })

        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    # ============================================================
    # DATABASE HEALTH CHECK
    # ============================================================

    @app.route('/api/db/health', methods=['GET'])
    def api_db_health():
        """Database health check"""
        try:
            from src.database.connection import test_connection

            is_healthy = test_connection()

            return jsonify({
                'status': 'success' if is_healthy else 'error',
                'database': 'connected' if is_healthy else 'disconnected',
                'timestamp': datetime.utcnow().isoformat()
            })

        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    print("✓ Database API routes registered")
