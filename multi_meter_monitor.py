#!/usr/bin/env python3
"""
Multi-Utility Meter Monitor

Monitors multiple utility meters (water, electric, gas) simultaneously using
Claude Vision API and Wyze cameras with custom firmware.

Usage:
    python multi_meter_monitor.py [config_file]
    python multi_meter_monitor.py --test-connections
    python multi_meter_monitor.py --run-once
    python multi_meter_monitor.py --statistics

Examples:
    # Run with default config (config/meters.yaml)
    python multi_meter_monitor.py

    # Run with custom config
    python multi_meter_monitor.py config/my-meters.yaml

    # Test camera connections
    python multi_meter_monitor.py --test-connections

    # Take a single reading from all meters
    python multi_meter_monitor.py --run-once

    # Show statistics for all meters
    python multi_meter_monitor.py --statistics

Environment:
    ANTHROPIC_API_KEY: Required - Claude API key
    See config/meters.yaml for camera and InfluxDB configuration
"""

import os
import sys
import argparse
import signal
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from orchestrator import MeterOrchestrator
    from utils.config_loader import load_config
    from utils.logging_utils import setup_logger, format_statistics, print_statistics
except ImportError as e:
    print(f"Error: Cannot import required module: {e}")
    print("Make sure you're running from the project root")
    sys.exit(1)


def check_api_key():
    """Check if ANTHROPIC_API_KEY is set"""
    if not os.getenv('ANTHROPIC_API_KEY'):
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        print("\nSet it with:")
        print("  export ANTHROPIC_API_KEY=sk-ant-...")
        print("\nOr add it to your .env.local file")
        sys.exit(1)


def test_connections(config_path: str) -> int:
    """
    Test camera connections for all configured meters

    Args:
        config_path: Path to configuration file

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    print("=" * 60)
    print("CAMERA CONNECTION TEST")
    print("=" * 60)

    try:
        config = load_config(config_path)
        logger = setup_logger("test", log_level="INFO")
        orchestrator = MeterOrchestrator(config, logger)

        results = orchestrator.test_connections()

        print("\n" + "=" * 60)
        print("RESULTS")
        print("=" * 60)

        all_successful = all(results.values())

        for name, success in results.items():
            status = "✓ SUCCESS" if success else "✗ FAILED"
            print(f"{name:20s} {status}")

        print("=" * 60)

        if all_successful:
            print("All camera connections successful!")
            return 0
        else:
            failed = sum(1 for v in results.values() if not v)
            print(f"Warning: {failed} camera(s) failed connection test")
            return 1

    except Exception as e:
        print(f"\nError during connection test: {e}")
        import traceback
        traceback.print_exc()
        return 1


def run_once(config_path: str) -> int:
    """
    Take a single reading from all meters

    Args:
        config_path: Path to configuration file

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    print("=" * 60)
    print("SINGLE READING FROM ALL METERS")
    print("=" * 60)

    try:
        config = load_config(config_path)
        logger = setup_logger("single_read", log_level="INFO")
        orchestrator = MeterOrchestrator(config, logger)

        results = orchestrator.run_once()

        print("\n" + "=" * 60)
        print("RESULTS")
        print("=" * 60)

        for name, reading in results.items():
            print(f"\n{name}:")
            if 'error' in reading:
                print(f"  ERROR: {reading['error']}")
            else:
                print(f"  Reading: {reading.get('total_reading', 'N/A')}")
                print(f"  Confidence: {reading.get('confidence', 'N/A')}")
                print(f"  Timestamp: {reading.get('timestamp', 'N/A')}")

        print("\n" + "=" * 60)

        # Check if any readings failed
        failures = sum(1 for r in results.values() if 'error' in r)
        if failures > 0:
            print(f"Warning: {failures} reading(s) failed")
            return 1

        print("All readings successful!")
        return 0

    except Exception as e:
        print(f"\nError during single reading: {e}")
        import traceback
        traceback.print_exc()
        return 1


def show_statistics(config_path: str) -> int:
    """
    Show statistics for all meters

    Args:
        config_path: Path to configuration file

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    print("=" * 60)
    print("METER STATISTICS")
    print("=" * 60)

    try:
        config = load_config(config_path)
        logger = setup_logger("stats", log_level="WARNING")
        orchestrator = MeterOrchestrator(config, logger)

        summaries = orchestrator.get_meter_summaries()

        for name, summary in summaries.items():
            if 'error' in summary:
                print(f"\n{name}: {summary['error']}")
            else:
                print_statistics(summary)

        return 0

    except Exception as e:
        print(f"\nError getting statistics: {e}")
        import traceback
        traceback.print_exc()
        return 1


def run_continuous(config_path: str) -> int:
    """
    Run continuous monitoring of all meters

    Args:
        config_path: Path to configuration file

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    print("=" * 60)
    print("MULTI-METER CONTINUOUS MONITORING")
    print("=" * 60)

    try:
        config = load_config(config_path)
        log_config = config.get('logging', {})
        logger = setup_logger(
            "monitor",
            log_level=log_config.get('level', 'INFO'),
            log_file='logs/monitor.log' if log_config.get('log_to_file', True) else None
        )

        orchestrator = MeterOrchestrator(config, logger)

        # Set up signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            logger.info(f"\nReceived signal {signum}, shutting down...")
            orchestrator.stop()

            # Show final statistics
            print("\n" + "=" * 60)
            print("FINAL STATISTICS")
            print("=" * 60)

            stats = orchestrator.get_statistics()
            print(f"Total readings: {stats['total_readings']}")
            print(f"Successful: {stats['successful_readings']}")
            print(f"Failed: {stats['failed_readings']}")
            print(f"Success rate: {stats['success_rate']:.1f}%")
            print(f"Uptime: {stats['uptime_seconds']:.0f} seconds")
            print("=" * 60)

            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Test connections first
        logger.info("Testing camera connections...")
        results = orchestrator.test_connections()

        failed = sum(1 for v in results.values() if not v)
        if failed > 0:
            logger.warning(
                f"{failed} camera(s) failed connection test. "
                "Continuing anyway..."
            )

        # Start continuous monitoring
        logger.info("Starting continuous monitoring...")
        logger.info("Press Ctrl+C to stop")

        orchestrator.start()

        # Keep main thread alive
        while orchestrator.running:
            try:
                import time
                time.sleep(1)
            except KeyboardInterrupt:
                signal_handler(signal.SIGINT, None)

        return 0

    except Exception as e:
        print(f"\nError during monitoring: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Multi-Utility Meter Monitor',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        'config',
        nargs='?',
        default='config/meters.yaml',
        help='Path to configuration file (default: config/meters.yaml)'
    )

    parser.add_argument(
        '--test-connections',
        action='store_true',
        help='Test camera connections and exit'
    )

    parser.add_argument(
        '--run-once',
        action='store_true',
        help='Take a single reading from all meters and exit'
    )

    parser.add_argument(
        '--statistics',
        action='store_true',
        help='Show statistics for all meters and exit'
    )

    args = parser.parse_args()

    # Check API key
    check_api_key()

    # Execute requested operation
    if args.test_connections:
        return test_connections(args.config)
    elif args.run_once:
        return run_once(args.config)
    elif args.statistics:
        return show_statistics(args.config)
    else:
        return run_continuous(args.config)


if __name__ == "__main__":
    sys.exit(main())
