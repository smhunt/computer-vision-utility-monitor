"""The Utility Meters Vision Monitor integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_INFLUXDB_BUCKET,
    CONF_INFLUXDB_ORG,
    CONF_INFLUXDB_TOKEN,
    CONF_INFLUXDB_URL,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    INFLUXDB_QUERY_TEMPLATE,
    METER_TYPES,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Utility Meters Vision Monitor from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Create coordinator for data updates
    coordinator = UtilityMeterDataCoordinator(
        hass,
        entry.data[CONF_INFLUXDB_URL],
        entry.data[CONF_INFLUXDB_TOKEN],
        entry.data[CONF_INFLUXDB_ORG],
        entry.data[CONF_INFLUXDB_BUCKET],
        entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Setup platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Setup options update listener
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


class UtilityMeterDataCoordinator(DataUpdateCoordinator):
    """Class to manage fetching utility meter data from InfluxDB."""

    def __init__(
        self,
        hass: HomeAssistant,
        influxdb_url: str,
        influxdb_token: str,
        influxdb_org: str,
        influxdb_bucket: str,
        scan_interval: int,
    ) -> None:
        """Initialize the coordinator."""
        self.influxdb_url = influxdb_url
        self.influxdb_token = influxdb_token
        self.influxdb_org = influxdb_org
        self.influxdb_bucket = influxdb_bucket

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self):
        """Fetch data from InfluxDB."""
        try:
            from influxdb_client import InfluxDBClient

            # Run InfluxDB queries in executor to avoid blocking
            return await self.hass.async_add_executor_job(
                self._fetch_meter_data,
            )
        except Exception as err:
            _LOGGER.error("Error fetching meter data: %s", err)
            raise UpdateFailed(f"Error communicating with InfluxDB: {err}") from err

    def _fetch_meter_data(self):
        """Fetch meter data from InfluxDB (runs in executor)."""
        try:
            client = InfluxDBClient(
                url=self.influxdb_url,
                token=self.influxdb_token,
                org=self.influxdb_org,
            )

            query_api = client.query_api()
            data = {}

            for meter_type in METER_TYPES:
                try:
                    # Build query for this meter type
                    query = INFLUXDB_QUERY_TEMPLATE.format(
                        bucket=self.influxdb_bucket,
                        meter_type=meter_type,
                    )

                    # Execute query
                    tables = query_api.query(query, org=self.influxdb_org)

                    # Process results
                    meter_data = {
                        "total_reading": None,
                        "digital_reading": None,
                        "dial_reading": None,
                        "confidence": None,
                        "timestamp": None,
                        "camera": None,
                    }

                    for table in tables:
                        for record in table.records:
                            field = record.get_field()
                            value = record.get_value()

                            if field == "value" or field == "total_reading":
                                meter_data["total_reading"] = value
                                meter_data["timestamp"] = record.get_time()
                            elif field == "digital_reading":
                                meter_data["digital_reading"] = value
                            elif field == "dial_reading":
                                meter_data["dial_reading"] = value

                            # Get tags
                            if "confidence" in record.values:
                                meter_data["confidence"] = record.values["confidence"]
                            if "camera" in record.values:
                                meter_data["camera"] = record.values["camera"]

                    # Only add to data if we got a reading
                    if meter_data["total_reading"] is not None:
                        data[meter_type] = meter_data
                        _LOGGER.debug(
                            "Fetched %s meter data: %s", meter_type, meter_data
                        )
                    else:
                        _LOGGER.warning("No data found for %s meter", meter_type)

                except Exception as err:
                    _LOGGER.error("Error fetching %s meter data: %s", meter_type, err)
                    # Continue to next meter type
                    continue

            client.close()

            if not data:
                _LOGGER.warning("No meter data retrieved from InfluxDB")

            return data

        except Exception as err:
            _LOGGER.error("Error connecting to InfluxDB: %s", err)
            raise
