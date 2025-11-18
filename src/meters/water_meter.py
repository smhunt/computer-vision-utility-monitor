"""
Water Meter Implementation

Implements water meter specific logic for reading and validating
water meter measurements in cubic meters (m³).
"""

from typing import Dict, Any
from datetime import datetime
from .base_meter import BaseMeter


class WaterMeter(BaseMeter):
    """Water meter implementation for monitoring water usage"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize water meter

        Args:
            config: Configuration dictionary (see BaseMeter for required keys)
        """
        # Ensure meter_type is set
        config["meter_type"] = "water"
        super().__init__(config)

        # Water-specific configuration
        self.unit = "m³"  # cubic meters
        self.max_change_per_reading = config.get("max_change_per_reading", 10.0)  # m³

    def get_claude_prompt(self) -> str:
        """
        Get Claude API prompt for water meter reading

        Returns:
            Prompt string customized for water meters
        """
        return """You are analyzing a water meter image. Please identify and read both components:

1. **Digital Display**: The main numerical display showing cubic meters (usually 4-5 digits)
2. **Dial/Analog Component**: The circular dial with a needle (shows fractional cubic meters, usually 0.000-0.999)

Please provide:
- The complete digital reading (integer part)
- The dial reading (fractional part to 3 decimal places)
- Total reading (digital + dial)
- Confidence level (high/medium/low)
- Any issues or concerns

Return your response in JSON format:
{
    "digital_reading": <integer>,
    "dial_reading": <float, 0.000-0.999>,
    "total_reading": <float>,
    "confidence": "high|medium|low",
    "notes": "any observations or concerns"
}

If you cannot read the meter clearly, explain why in the notes field and set confidence to "low".
"""

    def parse_reading(self, claude_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Claude API response for water meter

        Args:
            claude_response: Raw response from Claude API

        Returns:
            Standardized reading dictionary
        """
        # Water meter reading is already in the format we expect
        # Just add the meter type if not present
        if "meter_type" not in claude_response:
            claude_response["meter_type"] = "water"

        # Ensure timestamp is present
        if "timestamp" not in claude_response:
            claude_response["timestamp"] = datetime.now().isoformat()

        # Ensure all required fields are present
        required_fields = ["digital_reading", "dial_reading", "total_reading", "confidence"]
        for field in required_fields:
            if field not in claude_response:
                raise ValueError(f"Missing required field: {field}")

        return claude_response

    def validate_reading(self, reading: Dict[str, Any]) -> bool:
        """
        Validate water meter reading for plausibility

        Args:
            reading: Parsed meter reading

        Returns:
            True if reading is valid, False otherwise
        """
        try:
            total = reading.get("total_reading")
            digital = reading.get("digital_reading")
            dial = reading.get("dial_reading")

            # Check that all values are present
            if total is None or digital is None or dial is None:
                print(f"  ⚠️  Validation failed: Missing values")
                return False

            # Check that total = digital + dial (within tolerance)
            expected_total = digital + dial
            if abs(total - expected_total) > 0.01:
                print(f"  ⚠️  Validation failed: Total mismatch ({total} != {expected_total})")
                return False

            # Check that dial is in valid range [0, 1)
            if dial < 0 or dial >= 1.0:
                print(f"  ⚠️  Validation failed: Dial out of range ({dial})")
                return False

            # Check that digital reading is non-negative
            if digital < 0:
                print(f"  ⚠️  Validation failed: Negative digital reading ({digital})")
                return False

            # Check if change from last reading is reasonable (if we have history)
            if len(self.readings) > 0:
                last_reading = self.readings[-1]["total_reading"]
                change = total - last_reading

                # Water meters should only increase (or stay same)
                if change < 0:
                    print(f"  ⚠️  Validation failed: Reading decreased ({change:.3f} m³)")
                    return False

                # Check for unreasonable increase
                if change > self.max_change_per_reading:
                    print(f"  ⚠️  Validation failed: Excessive change ({change:.3f} m³)")
                    return False

            # All validation checks passed
            return True

        except Exception as e:
            print(f"  ⚠️  Validation error: {e}")
            return False

    def calculate_flow_rate(self) -> float:
        """
        Calculate current flow rate in liters per minute

        Returns:
            Flow rate in L/min, or 0 if insufficient data
        """
        if len(self.readings) < 2:
            return 0.0

        # Get last two readings
        current = self.readings[-1]
        previous = self.readings[-2]

        # Calculate time difference in minutes
        current_time = datetime.fromisoformat(current["timestamp"])
        previous_time = datetime.fromisoformat(previous["timestamp"])
        time_diff_minutes = (current_time - previous_time).total_seconds() / 60

        if time_diff_minutes <= 0:
            return 0.0

        # Calculate volume difference in cubic meters
        volume_diff = current["total_reading"] - previous["total_reading"]

        # Convert to liters per minute (1 m³ = 1000 L)
        flow_rate = (volume_diff * 1000) / time_diff_minutes

        return flow_rate

    def check_for_leak(self, threshold: float = 0.5) -> bool:
        """
        Check if there might be a leak based on continuous low flow

        Args:
            threshold: Minimum flow rate (L/min) to consider as potential leak

        Returns:
            True if potential leak detected, False otherwise
        """
        flow_rate = self.calculate_flow_rate()

        # If there's continuous low flow, it might be a leak
        # (assuming normal usage would be higher flow rates)
        if 0 < flow_rate < threshold:
            return True

        return False

    def get_usage_summary(self) -> Dict[str, Any]:
        """
        Get water usage summary

        Returns:
            Dictionary with usage statistics in water-specific units
        """
        stats = self.calculate_statistics()

        if stats is None:
            return {
                "error": "Insufficient data for usage summary"
            }

        # Convert to water-specific units
        return {
            "meter_type": "water",
            "num_readings": stats["num_readings"],
            "duration_hours": stats["duration_hours"],
            "total_usage_m3": stats["total_usage"],
            "total_usage_liters": stats["total_usage"] * 1000,
            "total_usage_gallons": stats["total_usage"] * 264.172,  # US gallons
            "average_rate_m3_per_hour": stats["average_rate"],
            "average_rate_liters_per_hour": stats["average_rate"] * 1000,
            "average_rate_gallons_per_hour": stats["average_rate"] * 264.172,
            "start_reading": stats["start_reading"],
            "end_reading": stats["end_reading"],
            "start_time": stats["start_time"],
            "end_time": stats["end_time"],
            "current_flow_rate_lpm": self.calculate_flow_rate(),
            "potential_leak": self.check_for_leak()
        }

    def __str__(self) -> str:
        """String representation"""
        return f"Water Meter @ {self.camera_ip} (Unit: {self.unit})"
