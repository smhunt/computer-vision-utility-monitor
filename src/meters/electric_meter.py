"""
Electric Meter Implementation

Implements electric meter specific logic for reading and validating
electric meter measurements in kilowatt-hours (kWh).
"""

from typing import Dict, Any
from datetime import datetime
from .base_meter import BaseMeter


class ElectricMeter(BaseMeter):
    """Electric meter implementation for monitoring electricity usage"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize electric meter

        Args:
            config: Configuration dictionary (see BaseMeter for required keys)
        """
        # Ensure meter_type is set
        config["meter_type"] = "electric"
        super().__init__(config)

        # Electric-specific configuration
        self.unit = "kWh"  # kilowatt-hours
        self.max_change_per_reading = config.get("max_change_per_reading", 50.0)  # kWh

    def get_claude_prompt(self) -> str:
        """
        Get Claude API prompt for electric meter reading

        Returns:
            Prompt string customized for electric meters
        """
        return """You are analyzing an electric meter image. Please identify and read the meter display.

Electric meters can have different formats:
1. **Digital Display**: A digital LCD/LED showing kilowatt-hours (kWh)
2. **Mechanical Dial**: Multiple circular dials (usually 4-5 dials) that must be read from left to right
3. **Hybrid**: Both digital and dial components

Instructions for reading:
- For digital displays: Read the complete number including any decimal places
- For dial meters: Read each dial from left to right. If the pointer is between numbers, use the lower number
- Some meters may have a multiplier (e.g., ×10, ×100) - note this if present

Please provide:
- The complete meter reading in kWh
- The digital display reading (if present)
- The dial reading (if present, sum of all dials)
- Total reading in kWh
- Confidence level (high/medium/low)
- Any multiplier or special notes

Return your response in JSON format:
{
    "digital_reading": <float or 0 if not applicable>,
    "dial_reading": <float or 0 if not applicable>,
    "total_reading": <float in kWh>,
    "multiplier": <integer, default 1>,
    "confidence": "high|medium|low",
    "notes": "any observations, meter type, or concerns"
}

If you cannot read the meter clearly, explain why in the notes field and set confidence to "low".
"""

    def parse_reading(self, claude_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Claude API response for electric meter

        Args:
            claude_response: Raw response from Claude API

        Returns:
            Standardized reading dictionary
        """
        # Add meter type if not present
        if "meter_type" not in claude_response:
            claude_response["meter_type"] = "electric"

        # Ensure timestamp is present
        if "timestamp" not in claude_response:
            claude_response["timestamp"] = datetime.now().isoformat()

        # Apply multiplier if present
        multiplier = claude_response.get("multiplier", 1)
        if multiplier != 1:
            claude_response["total_reading"] = claude_response["total_reading"] * multiplier
            claude_response["notes"] = claude_response.get("notes", "") + f" (multiplier: ×{multiplier})"

        # Ensure all required fields are present
        required_fields = ["total_reading", "confidence"]
        for field in required_fields:
            if field not in claude_response:
                raise ValueError(f"Missing required field: {field}")

        # Set defaults for optional fields
        if "digital_reading" not in claude_response:
            claude_response["digital_reading"] = claude_response["total_reading"]
        if "dial_reading" not in claude_response:
            claude_response["dial_reading"] = 0.0

        return claude_response

    def validate_reading(self, reading: Dict[str, Any]) -> bool:
        """
        Validate electric meter reading for plausibility

        Args:
            reading: Parsed meter reading

        Returns:
            True if reading is valid, False otherwise
        """
        try:
            total = reading.get("total_reading")

            # Check that total is present
            if total is None:
                print(f"  ⚠️  Validation failed: Missing total reading")
                return False

            # Check that reading is non-negative
            if total < 0:
                print(f"  ⚠️  Validation failed: Negative reading ({total})")
                return False

            # Check if change from last reading is reasonable (if we have history)
            if len(self.readings) > 0:
                last_reading = self.readings[-1]["total_reading"]
                change = total - last_reading

                # Electric meters should only increase (or stay same)
                if change < 0:
                    print(f"  ⚠️  Validation failed: Reading decreased ({change:.2f} kWh)")
                    return False

                # Check for unreasonable increase
                if change > self.max_change_per_reading:
                    print(f"  ⚠️  Validation failed: Excessive change ({change:.2f} kWh)")
                    return False

            # All validation checks passed
            return True

        except Exception as e:
            print(f"  ⚠️  Validation error: {e}")
            return False

    def calculate_power_consumption(self) -> float:
        """
        Calculate current power consumption in kilowatts (kW)

        Returns:
            Power consumption in kW, or 0 if insufficient data
        """
        if len(self.readings) < 2:
            return 0.0

        # Get last two readings
        current = self.readings[-1]
        previous = self.readings[-2]

        # Calculate time difference in hours
        current_time = datetime.fromisoformat(current["timestamp"])
        previous_time = datetime.fromisoformat(previous["timestamp"])
        time_diff_hours = (current_time - previous_time).total_seconds() / 3600

        if time_diff_hours <= 0:
            return 0.0

        # Calculate energy difference in kWh
        energy_diff = current["total_reading"] - previous["total_reading"]

        # Calculate power in kW
        power_kw = energy_diff / time_diff_hours

        return power_kw

    def estimate_monthly_cost(self, rate_per_kwh: float = 0.12) -> float:
        """
        Estimate monthly electricity cost based on current usage

        Args:
            rate_per_kwh: Cost per kWh (default: $0.12)

        Returns:
            Estimated monthly cost in dollars
        """
        stats = self.calculate_statistics()

        if stats is None:
            return 0.0

        # Calculate average daily usage
        daily_usage = (stats["average_rate"] * 24)  # kWh per day

        # Estimate monthly usage (30 days)
        monthly_usage = daily_usage * 30

        # Calculate cost
        monthly_cost = monthly_usage * rate_per_kwh

        return monthly_cost

    def check_high_usage(self, threshold_kw: float = 5.0) -> bool:
        """
        Check if current power consumption is unusually high

        Args:
            threshold_kw: Power threshold in kW to consider as high usage

        Returns:
            True if high usage detected, False otherwise
        """
        power = self.calculate_power_consumption()
        return power > threshold_kw

    def get_usage_summary(self) -> Dict[str, Any]:
        """
        Get electricity usage summary

        Returns:
            Dictionary with usage statistics in electric-specific units
        """
        stats = self.calculate_statistics()

        if stats is None:
            return {
                "error": "Insufficient data for usage summary"
            }

        # Calculate power and costs
        current_power = self.calculate_power_consumption()
        estimated_cost = self.estimate_monthly_cost()

        return {
            "meter_type": "electric",
            "num_readings": stats["num_readings"],
            "duration_hours": stats["duration_hours"],
            "total_usage_kwh": stats["total_usage"],
            "average_rate_kwh_per_hour": stats["average_rate"],
            "average_rate_kwh_per_day": stats["average_rate"] * 24,
            "current_power_kw": current_power,
            "current_power_watts": current_power * 1000,
            "estimated_monthly_cost": estimated_cost,
            "start_reading": stats["start_reading"],
            "end_reading": stats["end_reading"],
            "start_time": stats["start_time"],
            "end_time": stats["end_time"],
            "high_usage_alert": self.check_high_usage()
        }

    def __str__(self) -> str:
        """String representation"""
        return f"Electric Meter @ {self.camera_ip} (Unit: {self.unit})"
