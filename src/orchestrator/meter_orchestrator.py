"""
Meter Orchestrator

Manages and coordinates multiple utility meters for simultaneous monitoring.
"""

import time
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

from meters import WaterMeter, ElectricMeter, GasMeter, BaseMeter
from utils.logging_utils import setup_logger, format_reading_summary


class MeterOrchestrator:
    """
    Orchestrates monitoring of multiple utility meters

    Manages meter instances, schedules readings, and coordinates data collection
    from multiple meters with different reading intervals.
    """

    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        """
        Initialize the orchestrator with configuration

        Args:
            config: Configuration dictionary containing meter configs
            logger: Optional logger instance (creates new one if not provided)
        """
        self.config = config
        self.logger = logger or setup_logger("orchestrator")
        self.meters: List[BaseMeter] = []
        self.threads: Dict[str, threading.Thread] = {}
        self.running = False
        self.stop_event = threading.Event()

        # Statistics
        self.total_readings = 0
        self.successful_readings = 0
        self.failed_readings = 0
        self.start_time = None

        # Initialize meters from config
        self._initialize_meters()

    def _initialize_meters(self) -> None:
        """Initialize meter instances from configuration"""
        meter_configs = self.config.get('meters', [])

        if not meter_configs:
            self.logger.warning("No meters configured")
            return

        for meter_config in meter_configs:
            try:
                meter = self._create_meter(meter_config)
                self.meters.append(meter)
                self.logger.info(f"Initialized {meter}")
            except Exception as e:
                self.logger.error(
                    f"Failed to initialize meter {meter_config.get('name', 'unknown')}: {e}"
                )

        self.logger.info(f"Initialized {len(self.meters)} meter(s)")

    def _create_meter(self, config: Dict[str, Any]) -> BaseMeter:
        """
        Create a meter instance based on configuration

        Args:
            config: Meter configuration dictionary

        Returns:
            Meter instance

        Raises:
            ValueError: If meter type is invalid
        """
        meter_type = config['type'].lower()

        # Map meter type to class
        meter_classes = {
            'water': WaterMeter,
            'electric': ElectricMeter,
            'gas': GasMeter
        }

        meter_class = meter_classes.get(meter_type)

        if not meter_class:
            raise ValueError(f"Invalid meter type: {meter_type}")

        return meter_class(config)

    def test_connections(self) -> Dict[str, bool]:
        """
        Test connectivity to all configured cameras

        Returns:
            Dictionary mapping meter names to connection status
        """
        results = {}

        self.logger.info("Testing camera connections...")

        for meter in self.meters:
            meter_name = meter.config.get('name', f'{meter.meter_type}_meter')
            self.logger.info(f"Testing {meter_name}...")

            try:
                success = meter.test_connection()
                results[meter_name] = success

                if success:
                    self.logger.info(f"  ✓ {meter_name} connection successful")
                else:
                    self.logger.error(f"  ✗ {meter_name} connection failed")

            except Exception as e:
                results[meter_name] = False
                self.logger.error(f"  ✗ {meter_name} connection error: {e}")

        # Summary
        successful = sum(1 for v in results.values() if v)
        total = len(results)
        self.logger.info(
            f"Connection test complete: {successful}/{total} successful"
        )

        return results

    def _monitor_meter(self, meter: BaseMeter) -> None:
        """
        Monitor a single meter (runs in separate thread)

        Args:
            meter: Meter instance to monitor
        """
        meter_name = meter.config.get('name', f'{meter.meter_type}_meter')
        interval = meter.get_reading_interval()

        self.logger.info(
            f"Starting monitoring for {meter_name} "
            f"(interval: {interval}s)"
        )

        while not self.stop_event.is_set():
            try:
                # Take reading
                self.logger.info(f"[{meter_name}] Taking reading...")
                reading = meter.process_reading()

                # Update statistics
                self.total_readings += 1

                if 'error' in reading:
                    self.failed_readings += 1
                    self.logger.error(
                        f"[{meter_name}] Reading failed: {reading['error']}"
                    )
                else:
                    self.successful_readings += 1
                    self.logger.info(
                        f"[{meter_name}] {format_reading_summary(reading)}"
                    )

            except Exception as e:
                self.failed_readings += 1
                self.logger.error(
                    f"[{meter_name}] Unexpected error: {e}",
                    exc_info=True
                )

            # Wait for next reading (with interruptible sleep)
            self.stop_event.wait(interval)

        self.logger.info(f"Stopped monitoring {meter_name}")

    def start(self) -> None:
        """Start monitoring all meters"""
        if self.running:
            self.logger.warning("Orchestrator is already running")
            return

        if not self.meters:
            self.logger.error("No meters configured. Cannot start.")
            return

        self.logger.info("Starting multi-meter orchestrator...")
        self.running = True
        self.start_time = datetime.now()
        self.stop_event.clear()

        # Start a monitoring thread for each meter
        for meter in self.meters:
            meter_name = meter.config.get('name', f'{meter.meter_type}_meter')
            thread = threading.Thread(
                target=self._monitor_meter,
                args=(meter,),
                name=f"monitor_{meter_name}",
                daemon=True
            )
            thread.start()
            self.threads[meter_name] = thread

        self.logger.info(
            f"Orchestrator started with {len(self.threads)} meter(s)"
        )

    def stop(self) -> None:
        """Stop monitoring all meters"""
        if not self.running:
            self.logger.warning("Orchestrator is not running")
            return

        self.logger.info("Stopping orchestrator...")
        self.running = False
        self.stop_event.set()

        # Wait for all threads to finish (with timeout)
        for name, thread in self.threads.items():
            self.logger.debug(f"Waiting for {name} thread to stop...")
            thread.join(timeout=5.0)

            if thread.is_alive():
                self.logger.warning(f"Thread {name} did not stop cleanly")

        self.threads.clear()
        self.logger.info("Orchestrator stopped")

    def run_once(self) -> Dict[str, Any]:
        """
        Take a single reading from all meters (synchronously)

        Returns:
            Dictionary mapping meter names to readings
        """
        self.logger.info("Taking single reading from all meters...")
        results = {}

        for meter in self.meters:
            meter_name = meter.config.get('name', f'{meter.meter_type}_meter')

            try:
                self.logger.info(f"[{meter_name}] Reading...")
                reading = meter.process_reading()

                results[meter_name] = reading

                if 'error' in reading:
                    self.logger.error(
                        f"[{meter_name}] Error: {reading['error']}"
                    )
                else:
                    self.logger.info(
                        f"[{meter_name}] {format_reading_summary(reading)}"
                    )

            except Exception as e:
                self.logger.error(f"[{meter_name}] Exception: {e}", exc_info=True)
                results[meter_name] = {
                    'error': str(e),
                    'meter_type': meter.meter_type,
                    'timestamp': datetime.now().isoformat()
                }

        return results

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get orchestrator statistics

        Returns:
            Dictionary with orchestrator statistics
        """
        uptime = None
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()

        return {
            'running': self.running,
            'num_meters': len(self.meters),
            'total_readings': self.total_readings,
            'successful_readings': self.successful_readings,
            'failed_readings': self.failed_readings,
            'success_rate': (
                self.successful_readings / self.total_readings * 100
                if self.total_readings > 0 else 0
            ),
            'uptime_seconds': uptime,
            'start_time': self.start_time.isoformat() if self.start_time else None
        }

    def get_meter_statistics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics from all meters

        Returns:
            Dictionary mapping meter names to their statistics
        """
        results = {}

        for meter in self.meters:
            meter_name = meter.config.get('name', f'{meter.meter_type}_meter')

            try:
                stats = meter.calculate_statistics()
                results[meter_name] = stats
            except Exception as e:
                self.logger.error(f"Error getting stats for {meter_name}: {e}")
                results[meter_name] = {'error': str(e)}

        return results

    def get_meter_summaries(self) -> Dict[str, Dict[str, Any]]:
        """
        Get usage summaries from all meters

        Returns:
            Dictionary mapping meter names to their usage summaries
        """
        results = {}

        for meter in self.meters:
            meter_name = meter.config.get('name', f'{meter.meter_type}_meter')

            try:
                summary = meter.get_usage_summary()
                results[meter_name] = summary
            except Exception as e:
                self.logger.error(f"Error getting summary for {meter_name}: {e}")
                results[meter_name] = {'error': str(e)}

        return results

    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()
        return False

    def __str__(self) -> str:
        """String representation"""
        return (
            f"MeterOrchestrator({len(self.meters)} meters, "
            f"running={self.running})"
        )
