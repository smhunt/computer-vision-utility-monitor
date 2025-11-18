#!/usr/bin/env python3
"""
Image Preprocessing Module

Handles image rotation, orientation correction, and preprocessing
for meter reading analysis.
"""

import io
from pathlib import Path
from typing import Union, Tuple, Optional
from PIL import Image, ImageOps, ExifTags


def rotate_image(image: Union[str, Path, bytes, Image.Image], degrees: int) -> Image.Image:
    """
    Rotate an image by the specified degrees.

    Args:
        image: Image file path, bytes, or PIL Image object
        degrees: Rotation angle (0, 90, 180, 270)

    Returns:
        Rotated PIL Image object
    """
    # Load image if needed
    if isinstance(image, (str, Path)):
        img = Image.open(image)
    elif isinstance(image, bytes):
        img = Image.open(io.BytesIO(image))
    elif isinstance(image, Image.Image):
        img = image
    else:
        raise ValueError(f"Unsupported image type: {type(image)}")

    # Normalize degrees to 0-360
    degrees = degrees % 360

    # Rotate (counter-clockwise in PIL)
    # For clockwise rotation, use negative degrees
    if degrees == 90:
        return img.transpose(Image.Transpose.ROTATE_270)  # Clockwise 90
    elif degrees == 180:
        return img.transpose(Image.Transpose.ROTATE_180)
    elif degrees == 270:
        return img.transpose(Image.Transpose.ROTATE_90)   # Clockwise 270
    else:
        return img


def flip_image(image: Union[str, Path, bytes, Image.Image],
               horizontal: bool = False,
               vertical: bool = False) -> Image.Image:
    """
    Flip an image horizontally or vertically.

    Args:
        image: Image file path, bytes, or PIL Image object
        horizontal: Flip left-right
        vertical: Flip top-bottom

    Returns:
        Flipped PIL Image object
    """
    # Load image if needed
    if isinstance(image, (str, Path)):
        img = Image.open(image)
    elif isinstance(image, bytes):
        img = Image.open(io.BytesIO(image))
    elif isinstance(image, Image.Image):
        img = image
    else:
        raise ValueError(f"Unsupported image type: {type(image)}")

    if horizontal:
        img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    if vertical:
        img = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)

    return img


def auto_orient_image(image: Union[str, Path, bytes, Image.Image]) -> Image.Image:
    """
    Automatically orient image based on EXIF data.

    Many cameras embed orientation data in EXIF tags. This function
    reads that data and rotates the image to the correct orientation.

    Args:
        image: Image file path, bytes, or PIL Image object

    Returns:
        Correctly oriented PIL Image object
    """
    # Load image if needed
    if isinstance(image, (str, Path)):
        img = Image.open(image)
    elif isinstance(image, bytes):
        img = Image.open(io.BytesIO(image))
    elif isinstance(image, Image.Image):
        img = image
    else:
        raise ValueError(f"Unsupported image type: {type(image)}")

    # Use Pillow's built-in EXIF orientation correction
    return ImageOps.exif_transpose(img) or img


def save_rotated_image(image: Image.Image,
                       output_path: Union[str, Path],
                       quality: int = 95) -> Path:
    """
    Save a PIL Image to disk.

    Args:
        image: PIL Image object
        output_path: Where to save the image
        quality: JPEG quality (1-100)

    Returns:
        Path to saved image
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save with high quality
    image.save(output_path, quality=quality, optimize=True)

    return output_path


def image_to_bytes(image: Image.Image, format: str = 'JPEG', quality: int = 95) -> bytes:
    """
    Convert PIL Image to bytes.

    Args:
        image: PIL Image object
        format: Output format (JPEG, PNG, etc.)
        quality: Image quality for JPEG (1-100)

    Returns:
        Image as bytes
    """
    buffer = io.BytesIO()
    image.save(buffer, format=format, quality=quality, optimize=True)
    return buffer.getvalue()


def preprocess_meter_image(image_path: Union[str, Path],
                          rotation: Optional[int] = None,
                          auto_orient: bool = True) -> Tuple[Image.Image, dict]:
    """
    Preprocess meter image for analysis.

    This is the main entry point for image preprocessing before sending
    to the Claude Vision API.

    Args:
        image_path: Path to meter image
        rotation: Manual rotation angle (0, 90, 180, 270) or None
        auto_orient: Automatically correct orientation from EXIF

    Returns:
        Tuple of (processed_image, metadata)
    """
    metadata = {
        'original_path': str(image_path),
        'auto_oriented': False,
        'manual_rotation': 0,
        'flipped': False
    }

    # Load image
    img = Image.open(image_path)
    original_size = img.size
    metadata['original_size'] = original_size

    # Auto-orient from EXIF if requested
    if auto_orient:
        oriented_img = auto_orient_image(img)
        if oriented_img.size != img.size or oriented_img.tobytes() != img.tobytes():
            metadata['auto_oriented'] = True
            img = oriented_img

    # Apply manual rotation if specified
    if rotation and rotation != 0:
        img = rotate_image(img, rotation)
        metadata['manual_rotation'] = rotation

    metadata['final_size'] = img.size

    return img, metadata


def main():
    """CLI interface for testing image rotation."""
    import sys
    import argparse

    parser = argparse.ArgumentParser(description='Rotate and process meter images')
    parser.add_argument('image', help='Path to input image')
    parser.add_argument('--rotate', type=int, choices=[0, 90, 180, 270], default=0,
                       help='Rotation angle in degrees')
    parser.add_argument('--output', help='Output path (default: rotated_<input>)')
    parser.add_argument('--auto-orient', action='store_true',
                       help='Auto-orient based on EXIF data')

    args = parser.parse_args()

    # Process image
    img, metadata = preprocess_meter_image(
        args.image,
        rotation=args.rotate,
        auto_orient=args.auto_orient
    )

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        input_path = Path(args.image)
        output_path = input_path.parent / f"rotated_{input_path.name}"

    # Save
    save_rotated_image(img, output_path)

    print(f"✅ Image processed and saved to: {output_path}")
    print(f"📊 Metadata: {metadata}")


if __name__ == "__main__":
    main()
