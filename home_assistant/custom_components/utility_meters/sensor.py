"""Sensor platform for Utility Meters Vision Monitor integration."""
from __future__ import annotations

from datetime import datetime
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfVolume, UnitOfEnergy
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_CAMERA_TAG,
    DEFAULT_CAMERA_TAG,
    DOMAIN,
    METER_CONFIG,
    METER_TYPE_ELECTRIC,
    METER_TYPE_GAS,
    METER_TYPE_WATER,
    METER_TYPES,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the utility meter sensors."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    camera_tag = config_entry.data.get(CONF_CAMERA_TAG, DEFAULT_CAMERA_TAG)

    # Create sensor entities for each meter type
    entities = []
    for meter_type in METER_TYPES:
        entities.append(UtilityMeterSensor(coordinator, meter_type, camera_tag))

    async_add_entities(entities)


class UtilityMeterSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Utility Meter sensor."""

    def __init__(self, coordinator, meter_type: str, camera_tag: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._meter_type = meter_type
        self._camera_tag = camera_tag
        self._attr_has_entity_name = True

        # Get meter configuration
        config = METER_CONFIG[meter_type]

        # Set unique ID
        self._attr_unique_id = f"{DOMAIN}_{meter_type}_{camera_tag}"

        # Set name
        self._attr_name = config["name"]

        # Set unit of measurement
        if meter_type == METER_TYPE_WATER:
            self._attr_native_unit_of_measurement = UnitOfVolume.GALLONS
        elif meter_type == METER_TYPE_ELECTRIC:
            self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        else:  # gas
            self._attr_native_unit_of_measurement = config["unit"]

        # Set device class
        if meter_type == METER_TYPE_WATER:
            self._attr_device_class = SensorDeviceClass.WATER
        elif meter_type == METER_TYPE_ELECTRIC:
            self._attr_device_class = SensorDeviceClass.ENERGY
        elif meter_type == METER_TYPE_GAS:
            self._attr_device_class = SensorDeviceClass.GAS

        # Set state class for statistics and energy dashboard
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING

        # Set icon
        self._attr_icon = config["icon"]

        # Device info for grouping sensors
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{camera_tag}_utility_meters")},
            name=f"Utility Meters ({camera_tag})",
            manufacturer="Computer Vision Utility Monitor",
            model="Vision Monitor",
            sw_version="1.0.0",
        )

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.data and self._meter_type in self.coordinator.data:
            meter_data = self.coordinator.data[self._meter_type]
            return meter_data.get("total_reading")
        return None

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and self._meter_type in self.coordinator.data
        )

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return additional state attributes."""
        if not self.coordinator.data or self._meter_type not in self.coordinator.data:
            return {}

        meter_data = self.coordinator.data[self._meter_type]
        attributes = {}

        # Add digital and dial readings
        if meter_data.get("digital_reading") is not None:
            attributes["digital_reading"] = meter_data["digital_reading"]
        if meter_data.get("dial_reading") is not None:
            attributes["dial_reading"] = round(meter_data["dial_reading"], 3)

        # Add confidence level
        if meter_data.get("confidence"):
            attributes["confidence"] = meter_data["confidence"]

        # Add camera tag
        if meter_data.get("camera"):
            attributes["camera"] = meter_data["camera"]
        else:
            attributes["camera"] = self._camera_tag

        # Add last reading timestamp
        if meter_data.get("timestamp"):
            timestamp = meter_data["timestamp"]
            if isinstance(timestamp, datetime):
                attributes["last_reading"] = timestamp.isoformat()
            else:
                attributes["last_reading"] = str(timestamp)

        # Add meter type
        attributes["meter_type"] = self._meter_type

        return attributes

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
