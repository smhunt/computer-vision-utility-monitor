"""
Logging Utilities

Provides logging utilities for the meter monitoring system.
"""

import logging
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


def setup_logger(
    name: str = "meter_monitor",
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    log_to_console: bool = True
) -> logging.Logger:
    """
    Set up a logger with console and/or file output

    Args:
        name: Logger name
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        log_to_console: Whether to log to console

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Clear existing handlers
    logger.handlers.clear()

    # Set log level
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(level)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Add console handler if requested
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # Add file handler if log_file is specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def log_reading(
    reading: Dict[str, Any],
    log_file: str = "logs/readings.jsonl"
) -> None:
    """
    Log a meter reading to a JSON Lines file

    Args:
        reading: Reading dictionary to log
        log_file: Path to JSONL log file
    """
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    with open(log_path, 'a') as f:
        f.write(json.dumps(reading) + '\n')


def get_recent_readings(
    log_file: str = "logs/readings.jsonl",
    limit: int = 10,
    meter_type: Optional[str] = None
) -> list:
    """
    Get recent readings from log file

    Args:
        log_file: Path to JSONL log file
        limit: Maximum number of readings to return
        meter_type: Filter by meter type (optional)

    Returns:
        List of reading dictionaries (most recent first)
    """
    log_path = Path(log_file)

    if not log_path.exists():
        return []

    readings = []

    with open(log_path, 'r') as f:
        for line in f:
            try:
                reading = json.loads(line.strip())

                # Filter by meter type if specified
                if meter_type and reading.get('meter_type') != meter_type:
                    continue

                readings.append(reading)
            except json.JSONDecodeError:
                continue

    # Return most recent readings first
    return readings[-limit:][::-1]


def format_reading_summary(reading: Dict[str, Any]) -> str:
    """
    Format a reading dictionary as a human-readable summary

    Args:
        reading: Reading dictionary

    Returns:
        Formatted summary string
    """
    if 'error' in reading:
        return (
            f"[{reading.get('meter_type', 'unknown').upper()}] "
            f"ERROR: {reading['error']}"
        )

    meter_type = reading.get('meter_type', 'unknown').upper()
    total = reading.get('total_reading', 0)
    confidence = reading.get('confidence', 'unknown')
    timestamp = reading.get('timestamp', 'unknown')

    # Format based on meter type
    if meter_type == 'WATER':
        return (
            f"[WATER] {total:.3f} m³ "
            f"(confidence: {confidence}) at {timestamp}"
        )
    elif meter_type == 'ELECTRIC':
        return (
            f"[ELECTRIC] {total:.2f} kWh "
            f"(confidence: {confidence}) at {timestamp}"
        )
    elif meter_type == 'GAS':
        unit = reading.get('unit', 'CCF')
        return (
            f"[GAS] {total:.2f} {unit} "
            f"(confidence: {confidence}) at {timestamp}"
        )
    else:
        return f"[{meter_type}] {total} (confidence: {confidence}) at {timestamp}"


def format_statistics(stats: Dict[str, Any]) -> str:
    """
    Format statistics dictionary as a human-readable summary

    Args:
        stats: Statistics dictionary

    Returns:
        Formatted summary string
    """
    if 'error' in stats:
        return f"Statistics Error: {stats['error']}"

    meter_type = stats.get('meter_type', 'unknown').upper()
    lines = [
        f"\n{meter_type} METER STATISTICS",
        "=" * 50,
        f"Number of readings: {stats.get('num_readings', 0)}",
        f"Duration: {stats.get('duration_hours', 0):.2f} hours",
        f"Start time: {stats.get('start_time', 'unknown')}",
        f"End time: {stats.get('end_time', 'unknown')}",
        f"Start reading: {stats.get('start_reading', 0):.3f}",
        f"End reading: {stats.get('end_reading', 0):.3f}",
    ]

    # Add meter-specific statistics
    if meter_type == 'WATER':
        lines.extend([
            f"Total usage: {stats.get('total_usage_m3', 0):.3f} m³",
            f"Total usage: {stats.get('total_usage_liters', 0):.1f} L",
            f"Total usage: {stats.get('total_usage_gallons', 0):.1f} gallons",
            f"Average rate: {stats.get('average_rate_m3_per_hour', 0):.3f} m³/hour",
            f"Current flow: {stats.get('current_flow_rate_lpm', 0):.2f} L/min",
            f"Leak detected: {stats.get('potential_leak', False)}"
        ])
    elif meter_type == 'ELECTRIC':
        lines.extend([
            f"Total usage: {stats.get('total_usage_kwh', 0):.2f} kWh",
            f"Average rate: {stats.get('average_rate_kwh_per_hour', 0):.3f} kWh/hour",
            f"Average daily: {stats.get('average_rate_kwh_per_day', 0):.2f} kWh/day",
            f"Current power: {stats.get('current_power_kw', 0):.3f} kW",
            f"Current power: {stats.get('current_power_watts', 0):.1f} W",
            f"Estimated monthly cost: ${stats.get('estimated_monthly_cost', 0):.2f}",
            f"High usage alert: {stats.get('high_usage_alert', False)}"
        ])
    elif meter_type == 'GAS':
        unit = stats.get('unit', 'CCF').lower()
        lines.extend([
            f"Total usage: {stats.get(f'total_usage_{unit}', 0):.2f} {stats.get('unit', 'CCF')}",
            f"Total usage: {stats.get('total_usage_therms', 0):.2f} therms",
            f"Average rate: {stats.get(f'average_rate_{unit}_per_hour', 0):.3f} {stats.get('unit', 'CCF')}/hour",
            f"Average daily: {stats.get(f'average_rate_{unit}_per_day', 0):.2f} {stats.get('unit', 'CCF')}/day",
            f"Current flow: {stats.get(f'current_flow_rate_{unit}_per_hour', 0):.3f} {stats.get('unit', 'CCF')}/hour",
            f"Estimated monthly cost: ${stats.get('estimated_monthly_cost', 0):.2f}",
            f"High usage alert: {stats.get('high_usage_alert', False)}"
        ])

    lines.append("=" * 50)
    return "\n".join(lines)


def print_reading_summary(reading: Dict[str, Any]) -> None:
    """
    Print a formatted reading summary to console

    Args:
        reading: Reading dictionary
    """
    print(format_reading_summary(reading))


def print_statistics(stats: Dict[str, Any]) -> None:
    """
    Print formatted statistics to console

    Args:
        stats: Statistics dictionary
    """
    print(format_statistics(stats))
