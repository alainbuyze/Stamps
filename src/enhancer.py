"""Image enhancement using Upscayl CLI."""

import inspect
import logging
import shutil
import subprocess
from pathlib import Path

from src.core.config import get_settings
from src.sources.base import ExtractedContent

settings = get_settings()
logger = logging.getLogger(__name__)

# Minimum file size to enhance (skip tiny images)
MIN_FILE_SIZE_BYTES = 10 * 1024  # 10KB


def find_upscayl_binary() -> Path | None:
    """Find the Upscayl binary.

    Returns:
        Path to binary if found, None otherwise.
    """
    # Check configured path first
    configured_path = Path(settings.UPSCAYL_PATH)
    if configured_path.exists():
        return configured_path

    # Check common Windows locations
    common_paths = [
        Path("C:/Program Files/Upscayl/resources/bin/upscayl-bin.exe"),
        Path("C:/Program Files (x86)/Upscayl/resources/bin/upscayl-bin.exe"),
    ]

    for path in common_paths:
        if path.exists():
            return path

    # Check if in PATH
    which_result = shutil.which("upscayl-bin")
    if which_result:
        return Path(which_result)

    return None


def enhance_image(input_path: Path, output_path: Path) -> bool:
    """Enhance a single image using Upscayl.

    Args:
        input_path: Path to input image.
        output_path: Path to save enhanced image.

    Returns:
        True if enhancement succeeded, False otherwise.
    """
    logger.debug(f" * {inspect.currentframe().f_code.co_name} > Enhancing: {input_path}")

    # Check file size
    if input_path.stat().st_size < MIN_FILE_SIZE_BYTES:
        logger.debug(f"    -> Skipping (too small): {input_path.stat().st_size} bytes")
        return False

    # Find Upscayl binary
    upscayl_bin = find_upscayl_binary()
    if not upscayl_bin:
        logger.warning("    -> Upscayl binary not found, skipping enhancement")
        return False

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Build command
    cmd = [
        str(upscayl_bin),
        "-i",
        str(input_path),
        "-o",
        str(output_path),
        "-s",
        str(settings.UPSCAYL_SCALE),
        "-n",
        settings.UPSCAYL_MODEL,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,  # 2 minute timeout per image
        )

        if result.returncode != 0:
            logger.warning(f"    -> Enhancement failed: {result.stderr}")
            return False

        if output_path.exists():
            logger.debug(f"    -> Enhanced: {output_path}")
            return True
        else:
            logger.warning("    -> Output file not created")
            return False

    except subprocess.TimeoutExpired:
        logger.warning(f"    -> Enhancement timed out for: {input_path}")
        return False
    except Exception as e:
        logger.error(f"    -> Enhancement error: {e}")
        return False


def enhance_all_images(content: ExtractedContent, output_dir: Path) -> ExtractedContent:
    """Enhance all downloaded images in content.

    Processes images that have local_path set by the downloader.
    Enhanced images are saved with '_enhanced' suffix.

    Args:
        content: Extracted content with downloaded images.
        output_dir: Base output directory.

    Returns:
        Updated ExtractedContent with enhanced_path set for enhanced images.

    Raises:
        EnhancementError: If critical enhancement failure occurs.
    """
    logger.debug(f" * {inspect.currentframe().f_code.co_name} > Enhancing images in {output_dir}")

    # Check if enhancement is enabled
    if not settings.ENHANCE_IMAGES:
        logger.debug("    -> Enhancement disabled in settings")
        return content

    # Check for Upscayl
    upscayl_bin = find_upscayl_binary()
    if not upscayl_bin:
        logger.warning("    -> Upscayl not found, skipping all enhancements")
        return content

    # Find images with local paths
    images_to_enhance = [img for img in content.images if img.get("local_path")]

    if not images_to_enhance:
        logger.debug("    -> No local images to enhance")
        return content

    logger.debug(f"    -> Found {len(images_to_enhance)} images to enhance")

    enhanced_count = 0
    for image in images_to_enhance:
        local_path = image["local_path"]
        input_path = output_dir / local_path

        if not input_path.exists():
            logger.warning(f"    -> Local image not found: {input_path}")
            continue

        # Generate enhanced path (add _enhanced before extension)
        stem = input_path.stem
        suffix = input_path.suffix
        enhanced_filename = f"{stem}_enhanced{suffix}"
        enhanced_path = input_path.parent / enhanced_filename

        # Enhance
        success = enhance_image(input_path, enhanced_path)

        if success:
            # Store relative path for markdown
            relative_enhanced = Path(local_path).parent / enhanced_filename
            image["enhanced_path"] = str(relative_enhanced)
            enhanced_count += 1
        else:
            # Fall back to original - no enhanced_path set
            logger.debug(f"    -> Keeping original for: {local_path}")

    logger.debug(f"    -> Enhanced {enhanced_count}/{len(images_to_enhance)} images")
    return content
