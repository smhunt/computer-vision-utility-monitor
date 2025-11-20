#!/usr/bin/env python3
"""
Generate synthetic water meter display images for testing
Creates images that look like the Badger Meter "Absolute Digital" display
"""

from PIL import Image, ImageDraw, ImageFont
import math
import sys


def create_synthetic_meter(digital_reading: int, dial_reading: float, output_path: str = "synthetic_meter.jpg"):
    """
    Create a synthetic water meter display image

    Args:
        digital_reading: Integer reading (e.g., 2271)
        dial_reading: Dial reading as decimal (e.g., 0.75 for 7.5 on dial)
        output_path: Where to save the image
    """
    # Image dimensions
    width = 800
    height = 600

    # Create image with grayish background
    img = Image.new('RGB', (width, height), color=(200, 200, 200))
    draw = ImageDraw.Draw(img)

    # Draw meter face circle (white background)
    center_x, center_y = width // 2, height // 2
    meter_radius = 250
    draw.ellipse(
        [center_x - meter_radius, center_y - meter_radius,
         center_x + meter_radius, center_y + meter_radius],
        fill='white',
        outline='black',
        width=3
    )

    # --- Digital Display (White Rollers) ---
    # Format as 5 digits with leading zeros
    digit_string = f"{digital_reading:05d}"

    # Digital display position (top of meter)
    digit_y = center_y - 120
    digit_box_width = 200
    digit_box_height = 50
    digit_x = center_x - digit_box_width // 2

    # Draw black background for digital display
    draw.rectangle(
        [digit_x, digit_y, digit_x + digit_box_width, digit_y + digit_box_height],
        fill='black',
        outline='gray',
        width=2
    )

    # Try to load a monospace font, fall back to default
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Courier.dfont", 36)
        small_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
        tiny_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 12)
    except:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()
        tiny_font = ImageFont.load_default()

    # Draw digits with spacing
    digit_spacing = 38
    start_x = digit_x + 10
    for i, digit in enumerate(digit_string):
        x_pos = start_x + (i * digit_spacing)
        draw.text((x_pos, digit_y + 8), digit, fill='white', font=font)

    # Draw "m³" label
    draw.text((center_x + 80, center_y - 180), "m³", fill='gray', font=small_font)

    # --- Red Sweep Hand Dial ---
    dial_center_y = center_y + 80
    dial_radius = 100

    # Draw dial circle
    draw.ellipse(
        [center_x - dial_radius, dial_center_y - dial_radius,
         center_x + dial_radius, dial_center_y + dial_radius],
        fill='white',
        outline='black',
        width=2
    )

    # Draw dial markings (0-10 in 0.5 increments)
    for i in range(21):  # 0 to 10 in 0.5 steps = 21 marks
        value = i * 0.5
        angle_deg = (value / 10.0) * 360 - 90  # Start at top (12 o'clock)
        angle_rad = math.radians(angle_deg)

        # Longer marks for whole numbers
        if i % 2 == 0:
            inner_r = dial_radius - 15
            outer_r = dial_radius - 5
            width = 2
        else:
            inner_r = dial_radius - 10
            outer_r = dial_radius - 5
            width = 1

        x1 = center_x + inner_r * math.cos(angle_rad)
        y1 = dial_center_y + inner_r * math.sin(angle_rad)
        x2 = center_x + outer_r * math.cos(angle_rad)
        y2 = dial_center_y + outer_r * math.sin(angle_rad)

        draw.line([x1, y1, x2, y2], fill='black', width=width)

        # Label major marks (0, 2.5, 5, 7.5, 10)
        if value in [0, 2.5, 5, 7.5]:
            label_r = dial_radius - 25
            label_x = center_x + label_r * math.cos(angle_rad)
            label_y = dial_center_y + label_r * math.sin(angle_rad)
            label = str(int(value)) if value % 1 == 0 else str(value)
            draw.text((label_x - 8, label_y - 8), label, fill='black', font=tiny_font)

    # Label "0" at top and "10" just before it
    draw.text((center_x - 5, dial_center_y - dial_radius + 28), "0", fill='black', font=tiny_font)

    # Draw red sweep hand
    # dial_reading is 0.0 to 1.0 (representing 0 to 10 on the dial)
    hand_angle_deg = (dial_reading * 360) - 90  # Start at top
    hand_angle_rad = math.radians(hand_angle_deg)
    hand_length = dial_radius - 20

    # Hand end point
    hand_end_x = center_x + hand_length * math.cos(hand_angle_rad)
    hand_end_y = dial_center_y + hand_length * math.sin(hand_angle_rad)

    # Draw hand as thick line
    draw.line([center_x, dial_center_y, hand_end_x, hand_end_y],
              fill='red', width=4)

    # Draw center hub
    hub_radius = 8
    draw.ellipse(
        [center_x - hub_radius, dial_center_y - hub_radius,
         center_x + hub_radius, dial_center_y + hub_radius],
        fill='darkred',
        outline='black',
        width=1
    )

    # --- Labels ---
    # Badger Meter label
    draw.text((center_x - 60, dial_center_y + dial_radius + 20),
              "Badger Meter", fill='blue', font=small_font)

    # Model label
    draw.text((center_x - 40, dial_center_y + dial_radius + 40),
              "Absolute Digital", fill='black', font=tiny_font)

    # Flow rate indicators (decorative)
    draw.text((center_x - dial_radius + 10, dial_center_y + 50),
              "0.03", fill='lightblue', font=tiny_font)
    draw.text((center_x - dial_radius + 10, dial_center_y + 65),
              "0.04", fill='lightblue', font=tiny_font)
    draw.text((center_x - dial_radius + 10, dial_center_y + 80),
              "0.05", fill='lightblue', font=tiny_font)

    # Save image
    img.save(output_path, quality=95)
    print(f"✓ Generated synthetic meter image: {output_path}")
    print(f"  Digital reading: {digital_reading} m³")
    print(f"  Dial reading: {dial_reading:.2f} (position: {dial_reading * 10:.1f} on dial)")
    print(f"  Total: {digital_reading + dial_reading:.2f} m³")

    return img


if __name__ == "__main__":
    # Parse command line arguments
    if len(sys.argv) < 2:
        print("Usage: python3 generate_synthetic_meter.py <digital_reading> [dial_reading] [output_file]")
        print()
        print("Examples:")
        print("  python3 generate_synthetic_meter.py 2271 0.75 meter_2271_75.jpg")
        print("  python3 generate_synthetic_meter.py 2271 0.2")
        print("  python3 generate_synthetic_meter.py 2271")
        print()
        sys.exit(1)

    digital = int(sys.argv[1])
    dial = float(sys.argv[2]) if len(sys.argv) > 2 else 0.75
    output = sys.argv[3] if len(sys.argv) > 3 else "synthetic_meter.jpg"

    # Validate dial reading
    if dial < 0 or dial >= 1.0:
        print(f"Error: dial_reading must be between 0.0 and 0.99 (you provided {dial})")
        sys.exit(1)

    create_synthetic_meter(digital, dial, output)
