"""Async image downloader for tutorial content."""

import asyncio
import inspect
import logging
import re
from pathlib import Path
from urllib.parse import urlparse

import httpx

from src.core.config import get_settings
from src.core.errors import DownloadError
from src.sources.base import ExtractedContent

settings = get_settings()
logger = logging.getLogger(__name__)


def slugify(text: str) -> str:
    """Convert text to a URL-friendly slug for filenames.

    Args:
        text: Text to convert.

    Returns:
        Lowercase slug with underscores.
    """
    # Convert to lowercase and replace spaces/hyphens with underscores
    slug = text.lower()
    slug = re.sub(r"[-\s]+", "_", slug)
    # Remove non-alphanumeric characters (except underscores)
    slug = re.sub(r"[^a-z0-9_]", "", slug)
    # Remove multiple consecutive underscores
    slug = re.sub(r"_+", "_", slug)
    # Remove leading/trailing underscores
    slug = slug.strip("_")
    return slug


def generate_filename(url: str, alt: str, index: int) -> str:
    """Generate a filename for an image.

    Uses slugified alt text if available, otherwise falls back to index-based naming.

    Args:
        url: Image URL (for extension).
        alt: Alt text for the image.
        index: Image index for fallback naming.

    Returns:
        Generated filename with extension.
    """
    # Get extension from URL
    parsed = urlparse(url)
    path = parsed.path
    ext = Path(path).suffix.lower() or ".png"

    # Try to use alt text
    if alt and len(alt) > 3:
        name = slugify(alt)[:50]  # Limit length
        if name:
            return f"{name}{ext}"

    # Fall back to index-based naming
    return f"image_{index:03d}{ext}"


async def download_image(url: str, output_path: Path, client: httpx.AsyncClient) -> bool:
    """Download a single image with retry logic.

    Args:
        url: Image URL to download.
        output_path: Path to save the image.
        client: Async HTTP client.

    Returns:
        True if download succeeded, False otherwise.
    """
    from urllib.parse import urlparse
    url_stem = urlparse(url).path.split('/')[-1].split('.')[0]
    logger.debug(f" * {inspect.currentframe().f_code.co_name} > Downloading: {url_stem}")

    max_retries = settings.IMAGE_DOWNLOAD_MAX_RETRIES
    retry_delay = settings.IMAGE_DOWNLOAD_RETRY_DELAY
    backoff = settings.IMAGE_DOWNLOAD_RETRY_BACKOFF

    last_error = None
    for attempt in range(max_retries + 1):
        try:
            async with client.stream("GET", url) as response:
                if response.status_code >= 400:
                    logger.warning(f"    -> Failed to download: HTTP {response.status_code}")
                    last_error = f"HTTP {response.status_code}"
                    if attempt < max_retries:
                        wait_time = retry_delay * (backoff ** attempt)
                        logger.debug(f"    -> Retrying in {wait_time:.1f}s (attempt {attempt + 1}/{max_retries})")
                        await asyncio.sleep(wait_time)
                        continue
                    return False

                # Ensure directory exists
                output_path.parent.mkdir(parents=True, exist_ok=True)

                # Stream to file
                with open(output_path, "wb") as f:
                    async for chunk in response.aiter_bytes():
                        f.write(chunk)

            return True

        except httpx.TimeoutException as e:
            last_error = f"Timeout: {e}"
            logger.warning(f"    -> Download timeout (attempt {attempt + 1}/{max_retries + 1})")
        except httpx.ConnectError as e:
            last_error = f"Connection error: {e}"
            logger.warning(f"    -> Connection error (attempt {attempt + 1}/{max_retries + 1})")
        except Exception as e:
            last_error = str(e)
            logger.warning(f"    -> Download error (attempt {attempt + 1}/{max_retries + 1}): {e}")

        # Retry with backoff
        if attempt < max_retries:
            wait_time = retry_delay * (backoff ** attempt)
            logger.debug(f"    -> Retrying in {wait_time:.1f}s")
            await asyncio.sleep(wait_time)

    logger.error(f"    -> Download failed after {max_retries + 1} attempts: {last_error}")
    return False


async def download_images(content: ExtractedContent, output_dir: Path) -> ExtractedContent:
    """Download all images from extracted content.

    Downloads images to output_dir/images/ and updates image dicts with local_path.

    Args:
        content: Extracted content with images to download.
        output_dir: Guide-specific output directory (e.g., output/guide-name).

    Returns:
        Updated ExtractedContent with local_path set for downloaded images.

    Raises:
        DownloadError: If critical download failure occurs.
    """
    logger.debug(
        f" * {inspect.currentframe().f_code.co_name} > Downloading {len(content.images)} images"
    )

    if not content.images:
        logger.debug("    -> No images to download")
        return content

    # Setup output directory
    images_dir = output_dir / settings.IMAGE_OUTPUT_DIR
    images_dir.mkdir(parents=True, exist_ok=True)

    # Configure client
    timeout = httpx.Timeout(settings.IMAGE_DOWNLOAD_TIMEOUT, connect=10.0)

    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            for idx, image in enumerate(content.images):
                # Skip images already replaced with Dutch MakeCode screenshots
                if image.get("replaced_with_dutch"):
                    logger.debug(f"    -> Skipping image {idx}: already replaced with Dutch MakeCode screenshot")
                    continue

                url = image.get("src", "")
                if not url:
                    continue

                # Generate filename
                alt = image.get("alt", "")
                filename = generate_filename(url, alt, idx)
                output_path = images_dir / filename

                # Download
                success = await download_image(url, output_path, client)

                if success:
                    # Store relative path for markdown (relative to root output directory)
                    guide_name = output_dir.name
                    image["local_path"] = str(Path(guide_name) / settings.IMAGE_OUTPUT_DIR / filename)
                else:
                    logger.warning(f"    -> Failed to download image {idx}: {url}")

                # Rate limiting between downloads
                if settings.RATE_LIMIT_SECONDS > 0:
                    await asyncio.sleep(settings.RATE_LIMIT_SECONDS / 2)

        downloaded = sum(1 for img in content.images if "local_path" in img)
        logger.debug(f"    -> Downloaded {downloaded}/{len(content.images)} images")

        return content

    except Exception as e:
        error_context = {
            "total_images": len(content.images),
            "output_dir": str(output_dir),
            "error_type": type(e).__name__,
        }
        logger.error(f"Download batch failed: {e} | Context: {error_context}")
        raise DownloadError(f"Failed to download images: {e}") from e
