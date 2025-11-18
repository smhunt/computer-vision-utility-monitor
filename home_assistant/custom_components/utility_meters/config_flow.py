"""Config flow for Utility Meters Vision Monitor integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import (
    CONF_CAMERA_TAG,
    CONF_INFLUXDB_BUCKET,
    CONF_INFLUXDB_ORG,
    CONF_INFLUXDB_TOKEN,
    CONF_INFLUXDB_URL,
    CONF_SCAN_INTERVAL,
    DEFAULT_CAMERA_TAG,
    DEFAULT_INFLUXDB_BUCKET,
    DEFAULT_INFLUXDB_ORG,
    DEFAULT_INFLUXDB_URL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_INFLUXDB_URL, default=DEFAULT_INFLUXDB_URL): str,
        vol.Required(CONF_INFLUXDB_TOKEN): str,
        vol.Required(CONF_INFLUXDB_ORG, default=DEFAULT_INFLUXDB_ORG): str,
        vol.Required(CONF_INFLUXDB_BUCKET, default=DEFAULT_INFLUXDB_BUCKET): str,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            vol.Coerce(int), vol.Range(min=10, max=3600)
        ),
        vol.Optional(CONF_CAMERA_TAG, default=DEFAULT_CAMERA_TAG): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    try:
        from influxdb_client import InfluxDBClient
        from influxdb_client.client.exceptions import InfluxDBError
    except ImportError as err:
        raise CannotConnect("InfluxDB client library not installed") from err

    # Try to connect to InfluxDB
    try:
        client = InfluxDBClient(
            url=data[CONF_INFLUXDB_URL],
            token=data[CONF_INFLUXDB_TOKEN],
            org=data[CONF_INFLUXDB_ORG],
        )

        # Test the connection by checking if we can reach the API
        health = await hass.async_add_executor_job(client.health)

        if health.status != "pass":
            raise CannotConnect("InfluxDB is not healthy")

        # Test authentication by trying to list buckets
        buckets_api = client.buckets_api()
        await hass.async_add_executor_job(
            buckets_api.find_bucket_by_name, data[CONF_INFLUXDB_BUCKET]
        )

        client.close()

    except InfluxDBError as err:
        _LOGGER.error("InfluxDB authentication error: %s", err)
        raise InvalidAuth from err
    except Exception as err:
        _LOGGER.error("Cannot connect to InfluxDB: %s", err)
        raise CannotConnect from err

    # Return info that you want to store in the config entry.
    return {"title": "Utility Meters Vision Monitor"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Utility Meters Vision Monitor."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)

                # Check if already configured
                await self.async_set_unique_id(
                    f"{user_input[CONF_INFLUXDB_URL]}_{user_input[CONF_INFLUXDB_BUCKET]}"
                )
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=info["title"], data=user_input)

            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for the integration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            # Update the config entry with new options
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data={**self.config_entry.data, **user_input},
            )
            return self.async_create_entry(title="", data={})

        options_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=self.config_entry.data.get(
                        CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=10, max=3600)),
                vol.Optional(
                    CONF_CAMERA_TAG,
                    default=self.config_entry.data.get(
                        CONF_CAMERA_TAG, DEFAULT_CAMERA_TAG
                    ),
                ): str,
            }
        )

        return self.async_show_form(step_id="init", data_schema=options_schema)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
