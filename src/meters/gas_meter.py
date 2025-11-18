"""
Gas Meter Implementation

Implements gas meter specific logic for reading and validating
gas meter measurements in CCF (hundred cubic feet) or cubic meters.
"""

from typing import Dict, Any
from datetime import datetime
from .base_meter import BaseMeter


class GasMeter(BaseMeter):
    """Gas meter implementation for monitoring natural gas usage"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize gas meter

        Args:
            config: Configuration dictionary (see BaseMeter for required keys)
                Additional optional keys:
                    - use_cubic_meters: If True, use m³ instead of CCF (default: False)
        """
        # Ensure meter_type is set
        config["meter_type"] = "gas"
        super().__init__(config)

        # Gas-specific configuration
        self.use_cubic_meters = config.get("use_cubic_meters", False)
        self.unit = "m³" if self.use_cubic_meters else "CCF"
        self.max_change_per_reading = config.get("max_change_per_reading", 100.0)

    def get_claude_prompt(self) -> str:
        """
        Get Claude API prompt for gas meter reading

        Returns:
            Prompt string customized for gas meters
        """
        unit_text = "cubic meters (m³)" if self.use_cubic_meters else "CCF (hundred cubic feet)"

        return f"""You are analyzing a natural gas meter image. Please identify and read the meter display.

Gas meters typically have:
1. **Digital Display**: A digital LCD showing gas consumption in {unit_text}
2. **Mechanical Dial**: Multiple circular dials (usually 4-6 dials) showing gas consumption
3. **Test Dial**: A small red or silver dial used for testing (do NOT include this in the reading)

Instructions for reading:
- For digital displays: Read the complete number including any decimal places
- For dial meters: Read each dial from left to right, noting that adjacent dials turn in opposite directions
  - If the pointer is between numbers, use the lower number
  - The rightmost dial is typically the smallest unit
- Ignore the test dial (the small fast-spinning dial)
- Note the unit if visible (CCF, ft³, m³)

Please provide:
- The complete meter reading
- The digital display reading (if present)
- The dial reading (if present, sum of all dials)
- Total reading in {unit_text}
- Confidence level (high/medium/low)
- Unit of measurement if visible
- Any observations or concerns

Return your response in JSON format:
{{
    "digital_reading": <float or 0 if not applicable>,
    "dial_reading": <float or 0 if not applicable>,
    "total_reading": <float in {unit_text}>,
    "unit": "{self.unit}",
    "confidence": "high|medium|low",
    "notes": "any observations, meter type, or concerns"
}}

If you cannot read the meter clearly, explain why in the notes field and set confidence to "low".
"""

    def parse_reading(self, claude_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Claude API response for gas meter

        Args:
            claude_response: Raw response from Claude API

        Returns:
            Standardized reading dictionary
        """
        # Add meter type if not present
        if "meter_type" not in claude_response:
            claude_response["meter_type"] = "gas"

        # Ensure timestamp is present
        if "timestamp" not in claude_response:
            claude_response["timestamp"] = datetime.now().isoformat()

        # Handle unit conversion if needed
        reported_unit = claude_response.get("unit", self.unit)

        # Convert if needed (1 CCF = 100 ft³ = 2.83168 m³)
        if self.use_cubic_meters and reported_unit.upper() == "CCF":
            claude_response["total_reading"] = claude_response["total_reading"] * 2.83168
            claude_response["notes"] = claude_response.get("notes", "") + " (converted from CCF to m³)"
        elif not self.use_cubic_meters and reported_unit.lower() in ["m³", "m3", "cubic meters"]:
            claude_response["total_reading"] = claude_response["total_reading"] / 2.83168
            claude_response["notes"] = claude_response.get("notes", "") + " (converted from m³ to CCF)"

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
        Validate gas meter reading for plausibility

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

                # Gas meters should only increase (or stay same)
                if change < 0:
                    print(f"  ⚠️  Validation failed: Reading decreased ({change:.2f} {self.unit})")
                    return False

                # Check for unreasonable increase
                if change > self.max_change_per_reading:
                    print(f"  ⚠️  Validation failed: Excessive change ({change:.2f} {self.unit})")
                    return False

            # All validation checks passed
            return True

        except Exception as e:
            print(f"  ⚠️  Validation error: {e}")
            return False

    def calculate_flow_rate(self) -> float:
        """
        Calculate current gas flow rate

        Returns:
            Flow rate in CCF/hour or m³/hour depending on configuration
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

        # Calculate volume difference
        volume_diff = current["total_reading"] - previous["total_reading"]

        # Calculate flow rate
        flow_rate = volume_diff / time_diff_hours

        return flow_rate

    def estimate_monthly_cost(self, rate_per_unit: float = 1.00) -> float:
        """
        Estimate monthly gas cost based on current usage

        Args:
            rate_per_unit: Cost per CCF or m³ (default: $1.00)

        Returns:
            Estimated monthly cost in dollars
        """
        stats = self.calculate_statistics()

        if stats is None:
            return 0.0

        # Calculate average daily usage
        daily_usage = stats["average_rate"] * 24

        # Estimate monthly usage (30 days)
        monthly_usage = daily_usage * 30

        # Calculate cost
        monthly_cost = monthly_usage * rate_per_unit

        return monthly_cost

    def check_high_usage(self, threshold: float = 2.0) -> bool:
        """
        Check if current gas consumption is unusually high

        Args:
            threshold: Flow rate threshold to consider as high usage
                      (CCF/hour or m³/hour depending on configuration)

        Returns:
            True if high usage detected, False otherwise
        """
        flow_rate = self.calculate_flow_rate()
        return flow_rate > threshold

    def convert_to_therms(self, value: float = None) -> float:
        """
        Convert gas reading to therms (common for billing)

        Args:
            value: Value to convert (uses total usage if not provided)

        Returns:
            Value in therms
        """
        if value is None:
            stats = self.calculate_statistics()
            if stats is None:
                return 0.0
            value = stats["total_usage"]

        # Conversion factors:
        # 1 CCF ≈ 1.037 therms (varies by gas composition)
        # 1 m³ ≈ 0.366 therms
        if self.use_cubic_meters:
            return value * 0.366
        else:
            return value * 1.037

    def get_usage_summary(self) -> Dict[str, Any]:
        """
        Get gas usage summary

        Returns:
            Dictionary with usage statistics in gas-specific units
        """
        stats = self.calculate_statistics()

        if stats is None:
            return {
                "error": "Insufficient data for usage summary"
            }

        # Calculate flow rate and costs
        current_flow = self.calculate_flow_rate()
        estimated_cost = self.estimate_monthly_cost()
        therms = self.convert_to_therms()

        return {
            "meter_type": "gas",
            "unit": self.unit,
            "num_readings": stats["num_readings"],
            "duration_hours": stats["duration_hours"],
            f"total_usage_{self.unit.lower()}": stats["total_usage"],
            "total_usage_therms": therms,
            f"average_rate_{self.unit.lower()}_per_hour": stats["average_rate"],
            f"average_rate_{self.unit.lower()}_per_day": stats["average_rate"] * 24,
            f"current_flow_rate_{self.unit.lower()}_per_hour": current_flow,
            "estimated_monthly_cost": estimated_cost,
            "start_reading": stats["start_reading"],
            "end_reading": stats["end_reading"],
            "start_time": stats["start_time"],
            "end_time": stats["end_time"],
            "high_usage_alert": self.check_high_usage()
        }

    def __str__(self) -> str:
        """String representation"""
        return f"Gas Meter @ {self.camera_ip} (Unit: {self.unit})"
