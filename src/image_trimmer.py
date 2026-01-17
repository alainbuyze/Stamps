"""Image trimming utilities for removing whitespace and adding borders."""

import logging
from pathlib import Path

from PIL import Image, ImageChops, ImageOps

logger = logging.getLogger(__name__)


def trim_image(
    input_path: Path,
    output_path: Path | None = None,
    border_width: int = 0,
    border_color: str = "black",
) -> Path:
    """Trim whitespace from an image and optionally add a border.

    Args:
        input_path: Path to input image.
        output_path: Path to save trimmed image. If None, overwrites input.
        border_width: Width of border to add in pixels (default: 0 for no border).
        border_color: Color of the border (default: "black").

    Returns:
        Path to the output image.

    Raises:
        FileNotFoundError: If input image doesn't exist.
        ValueError: If border_width is negative.
        IOError: If image cannot be opened or saved.

    Example:
        >>> # Trim whitespace only
        >>> trim_image(Path("input.png"), Path("output.png"))

        >>> # Trim and add 2px black border
        >>> trim_image(Path("input.png"), Path("output.png"), border_width=2)

        >>> # Trim in-place
        >>> trim_image(Path("input.png"))
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input image not found: {input_path}")

    if border_width < 0:
        raise ValueError(f"border_width must be non-negative, got {border_width}")

    # Default to overwriting input if no output specified
    if output_path is None:
        output_path = input_path

    logger.debug(f"Trimming image: {input_path}")

    try:
        # Open image
        with Image.open(input_path) as img:
            # Convert to RGB if necessary (handles RGBA, grayscale, etc.)
            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGB")

            # Trim whitespace
            trimmed = _trim_whitespace(img)

            # Add border if requested
            if border_width > 0:
                trimmed = ImageOps.expand(trimmed, border=border_width, fill=border_color)

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Save trimmed image
            trimmed.save(output_path)

        logger.debug(f"Saved trimmed image to: {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Failed to trim image {input_path}: {e}")
        raise


def _trim_whitespace(img: Image.Image) -> Image.Image:
    """Trim whitespace from an image.

    Uses PIL's ImageChops to detect non-white pixels and crop to content.

    Args:
        img: PIL Image to trim.

    Returns:
        Trimmed PIL Image.
    """
    # Convert to RGB to ensure consistent comparison
    if img.mode == "RGBA":
        # Create a white background
        background = Image.new("RGB", img.size, (255, 255, 255))
        # Paste the image with alpha as mask
        background.paste(img, mask=img.split()[3])  # 3 is the alpha channel
        img = background
    elif img.mode != "RGB":
        img = img.convert("RGB")

    # Create a white background image
    bg = Image.new(img.mode, img.size, (255, 255, 255))

    # Calculate difference between image and white background
    diff = ImageChops.difference(img, bg)

    # Convert to grayscale for easier bbox detection
    diff = diff.convert("L")

    # Get bounding box of non-white pixels
    bbox = diff.getbbox()

    if bbox:
        # Crop to bounding box
        return img.crop(bbox)
    else:
        # Image is entirely white, return as-is
        logger.debug("Image is entirely white, no trimming needed")
        return img


def trim_images_batch(
    input_paths: list[Path],
    output_dir: Path,
    border_width: int = 0,
    border_color: str = "black",
    overwrite: bool = False,
) -> list[Path]:
    """Trim multiple images in batch.

    Args:
        input_paths: List of input image paths.
        output_dir: Directory to save trimmed images.
        border_width: Width of border to add in pixels (default: 0).
        border_color: Color of the border (default: "black").
        overwrite: If True, skip images that already exist in output_dir.

    Returns:
        List of paths to successfully trimmed images.

    Example:
        >>> images = [Path("img1.png"), Path("img2.png")]
        >>> trim_images_batch(images, Path("output"), border_width=2)
    """
    logger.debug(f"Trimming {len(input_paths)} images to {output_dir}")

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    trimmed_paths = []
    success_count = 0
    skip_count = 0
    error_count = 0

    for input_path in input_paths:
        # Generate output path
        output_path = output_dir / input_path.name

        # Check if already exists
        if not overwrite and output_path.exists():
            logger.debug(f"Skipping existing file: {output_path}")
            trimmed_paths.append(output_path)
            skip_count += 1
            continue

        try:
            result_path = trim_image(
                input_path,
                output_path,
                border_width=border_width,
                border_color=border_color,
            )
            trimmed_paths.append(result_path)
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to trim {input_path}: {e}")
            error_count += 1

    logger.debug(
        f"Batch complete: {success_count} trimmed, {skip_count} skipped, {error_count} errors"
    )

    return trimmed_paths


if __name__ == "__main__":
    """Test the image trimmer with a single file."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Trim whitespace from images")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", help="Output image path (optional)")
    parser.add_argument("-b", "--border", type=int, default=0, help="Border width in pixels")
    parser.add_argument(
        "-c", "--color", default="black", help="Border color (default: black)"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    # Set up logging
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
    else:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # Validate input file
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)

    # Trim the image
    output_path = Path(args.output) if args.output else None
    print(f"Trimming {input_path}...")

    try:
        result = trim_image(
            input_path, output_path, border_width=args.border, border_color=args.color
        )
        print(f"✓ Trimming successful: {result}")
        print(f"  File size: {result.stat().st_size} bytes")
    except Exception as e:
        print(f"✗ Trimming failed: {e}")
        sys.exit(1)
