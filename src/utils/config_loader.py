"""
Configuration Loader

Loads and validates YAML configuration files for multi-meter monitoring.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional


def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file

    Args:
        config_path: Path to configuration file (default: config/meters.yaml)

    Returns:
        Dictionary containing configuration

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid YAML
    """
    if config_path is None:
        # Default to config/meters.yaml in project root
        project_root = Path(__file__).parent.parent.parent
        config_path = project_root / "config" / "meters.yaml"

    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Expand environment variables in configuration
    config = expand_env_vars(config)

    # Validate configuration
    validate_config(config)

    return config


def expand_env_vars(config: Any) -> Any:
    """
    Recursively expand environment variables in configuration

    Supports ${VAR_NAME} and ${VAR_NAME:default_value} syntax

    Args:
        config: Configuration value (can be dict, list, str, etc.)

    Returns:
        Configuration with expanded environment variables
    """
    if isinstance(config, dict):
        return {k: expand_env_vars(v) for k, v in config.items()}
    elif isinstance(config, list):
        return [expand_env_vars(item) for item in config]
    elif isinstance(config, str):
        # Handle ${VAR_NAME:default} syntax
        import re

        def replace_env_var(match):
            var_expr = match.group(1)
            if ':' in var_expr:
                var_name, default = var_expr.split(':', 1)
                return os.getenv(var_name, default)
            else:
                return os.getenv(var_expr, match.group(0))

        return re.sub(r'\$\{([^}]+)\}', replace_env_var, config)
    else:
        return config


def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate configuration structure

    Args:
        config: Configuration dictionary to validate

    Raises:
        ValueError: If configuration is invalid
    """
    # Check for required top-level keys
    if 'meters' not in config:
        raise ValueError("Configuration must contain 'meters' section")

    meters = config['meters']

    if not isinstance(meters, list):
        raise ValueError("'meters' must be a list")

    if len(meters) == 0:
        raise ValueError("At least one meter must be configured")

    # Validate each meter configuration
    for i, meter in enumerate(meters):
        validate_meter_config(meter, i)

    # Validate optional sections
    if 'influxdb' in config:
        validate_influxdb_config(config['influxdb'])

    if 'mqtt' in config:
        validate_mqtt_config(config['mqtt'])


def validate_meter_config(meter: Dict[str, Any], index: int) -> None:
    """
    Validate individual meter configuration

    Args:
        meter: Meter configuration dictionary
        index: Index of meter in config (for error messages)

    Raises:
        ValueError: If meter configuration is invalid
    """
    required_fields = ['name', 'type', 'camera_ip']

    for field in required_fields:
        if field not in meter:
            raise ValueError(f"Meter {index}: Missing required field '{field}'")

    # Validate meter type
    valid_types = ['water', 'electric', 'gas']
    meter_type = meter['type']

    if meter_type not in valid_types:
        raise ValueError(
            f"Meter {index}: Invalid type '{meter_type}'. "
            f"Must be one of: {', '.join(valid_types)}"
        )

    # Validate camera configuration
    if 'camera_ip' in meter and not meter['camera_ip']:
        raise ValueError(f"Meter {index}: camera_ip cannot be empty")

    # Validate optional fields
    if 'reading_interval' in meter:
        interval = meter['reading_interval']
        if not isinstance(interval, int) or interval < 60:
            raise ValueError(
                f"Meter {index}: reading_interval must be an integer >= 60 seconds"
            )

    # Type-specific validation
    if meter_type == 'gas' and 'use_cubic_meters' in meter:
        if not isinstance(meter['use_cubic_meters'], bool):
            raise ValueError(
                f"Meter {index}: use_cubic_meters must be a boolean"
            )


def validate_influxdb_config(influxdb: Dict[str, Any]) -> None:
    """
    Validate InfluxDB configuration

    Args:
        influxdb: InfluxDB configuration dictionary

    Raises:
        ValueError: If InfluxDB configuration is invalid
    """
    required_fields = ['url', 'token', 'org', 'bucket']

    for field in required_fields:
        if field not in influxdb:
            raise ValueError(f"InfluxDB config: Missing required field '{field}'")
        if not influxdb[field]:
            raise ValueError(f"InfluxDB config: '{field}' cannot be empty")


def validate_mqtt_config(mqtt: Dict[str, Any]) -> None:
    """
    Validate MQTT configuration

    Args:
        mqtt: MQTT configuration dictionary

    Raises:
        ValueError: If MQTT configuration is invalid
    """
    if 'enabled' in mqtt and not isinstance(mqtt['enabled'], bool):
        raise ValueError("MQTT config: 'enabled' must be a boolean")

    if mqtt.get('enabled', False):
        required_fields = ['broker', 'port']

        for field in required_fields:
            if field not in mqtt:
                raise ValueError(f"MQTT config: Missing required field '{field}'")

        if not isinstance(mqtt['port'], int) or mqtt['port'] < 1 or mqtt['port'] > 65535:
            raise ValueError("MQTT config: 'port' must be between 1 and 65535")


def get_meter_configs(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract meter configurations from config

    Args:
        config: Full configuration dictionary

    Returns:
        List of meter configuration dictionaries
    """
    return config.get('meters', [])


def get_influxdb_config(config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract InfluxDB configuration from config

    Args:
        config: Full configuration dictionary

    Returns:
        InfluxDB configuration dictionary or None if not configured
    """
    return config.get('influxdb')


def get_mqtt_config(config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract MQTT configuration from config

    Args:
        config: Full configuration dictionary

    Returns:
        MQTT configuration dictionary or None if not configured
    """
    mqtt = config.get('mqtt')

    # Return None if MQTT is not enabled
    if mqtt and not mqtt.get('enabled', False):
        return None

    return mqtt


def merge_configs(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two configuration dictionaries (override takes precedence)

    Args:
        base: Base configuration
        override: Override configuration

    Returns:
        Merged configuration
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value

    return result
