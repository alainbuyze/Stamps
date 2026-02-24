"""Groq vision API integration for generating stamp descriptions.

Uses Groq's vision models (e.g., llama-3.2-11b-vision-preview) to analyze
stamp images and generate detailed textual descriptions suitable for
embedding and semantic search.
"""

import asyncio
import base64
import logging
import time
from pathlib import Path
from typing import Callable, Optional

import httpx
from groq import Groq

from src.core.config import get_settings
from src.core.errors import DescriptionError, GroqAPIError

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter for API calls."""

    def __init__(self, requests_per_minute: int):
        """Initialize rate limiter.

        Args:
            requests_per_minute: Maximum requests allowed per minute
        """
        self.requests_per_minute = requests_per_minute
        self.interval = 60.0 / requests_per_minute
        self.last_request_time = 0.0

    async def acquire(self) -> None:
        """Wait until a request can be made within rate limits."""
        now = time.time()
        time_since_last = now - self.last_request_time

        if time_since_last < self.interval:
            wait_time = self.interval - time_since_last
            logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)

        self.last_request_time = time.time()


class StampDescriber:
    """Generates descriptions for stamp images via Groq vision API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        prompt_path: Optional[Path] = None,
    ):
        """Initialize the stamp describer.

        Args:
            api_key: Groq API key (defaults to settings)
            model: Groq vision model name (defaults to settings)
            prompt_path: Path to prompt template file (defaults to settings)
        """
        settings = get_settings()

        self.api_key = api_key or settings.GROQ_API_KEY
        if not self.api_key:
            raise GroqAPIError("GROQ_API_KEY not configured")

        self.model = model or settings.GROQ_MODEL
        self.client = Groq(api_key=self.api_key)
        self.rate_limiter = RateLimiter(settings.GROQ_RATE_LIMIT_PER_MINUTE)

        # Load prompt template
        prompt_file = prompt_path or Path(settings.VISION_PROMPT_FILE)
        if prompt_file.exists():
            self.prompt_template = prompt_file.read_text(encoding="utf-8").strip()
            logger.debug(f"Loaded prompt template from {prompt_file}")
        else:
            logger.warning(f"Prompt template not found at {prompt_file}, using default")
            self.prompt_template = self._default_prompt()

    def _default_prompt(self) -> str:
        """Return default prompt if template file not found."""
        return """Describe this postage stamp in detail for identification purposes.
Include: subject/theme, visual elements, colors, country (if visible),
denomination, year (if visible), and any distinctive features.
Format as a single flowing paragraph suitable for semantic search."""

    async def describe_from_url(self, image_url: str, fallback_to_download: bool = True) -> str:
        """Generate description for stamp image from URL.

        Args:
            image_url: URL of the stamp image
            fallback_to_download: If True, download image and retry on timeout errors

        Returns:
            Textual description of the stamp

        Raises:
            GroqAPIError: If API call fails
            DescriptionError: If description cannot be generated
        """
        logger.debug(f" * describe_from_url > Starting for {image_url}")

        await self.rate_limiter.acquire()

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": self.prompt_template,
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_url,
                                },
                            },
                        ],
                    }
                ],
                max_tokens=512,
                temperature=0.3,
            )

            description = response.choices[0].message.content.strip()
            logger.debug(f"    -> Generated description: {description[:100]}...")
            return description

        except Exception as e:
            error_str = str(e).lower()
            # Check if this is a timeout or URL fetch error - try downloading instead
            if fallback_to_download and ("timeout" in error_str or "fetching url" in error_str):
                logger.warning(f"Direct URL failed, downloading image: {image_url}")
                return await self._describe_via_download(image_url)

            error_msg = f"Groq API error for {image_url}: {e}"
            logger.error(error_msg)
            raise GroqAPIError(error_msg) from e

    async def _describe_via_download(self, image_url: str) -> str:
        """Download image and describe via base64.

        Args:
            image_url: URL to download image from

        Returns:
            Textual description of the stamp
        """
        # Browser-like headers to avoid being blocked
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://colnect.com/",
        }

        try:
            async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
                response = await client.get(image_url, follow_redirects=True)
                response.raise_for_status()

                content_type = response.headers.get("content-type", "image/jpeg")
                image_base64 = base64.b64encode(response.content).decode("utf-8")

                return await self.describe_from_base64(image_base64, content_type)
        except Exception as e:
            error_msg = f"Failed to download and describe {image_url}: {e}"
            logger.error(error_msg)
            raise GroqAPIError(error_msg) from e

    async def describe_from_base64(self, image_base64: str, media_type: str = "image/jpeg") -> str:
        """Generate description for stamp image from base64 data.

        Args:
            image_base64: Base64-encoded image data
            media_type: MIME type of image (default: image/jpeg)

        Returns:
            Textual description of the stamp

        Raises:
            GroqAPIError: If API call fails
            DescriptionError: If description cannot be generated
        """
        logger.debug(" * describe_from_base64 > Starting")

        await self.rate_limiter.acquire()

        try:
            data_url = f"data:{media_type};base64,{image_base64}"

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": self.prompt_template,
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": data_url,
                                },
                            },
                        ],
                    }
                ],
                max_tokens=512,
                temperature=0.3,
            )

            description = response.choices[0].message.content.strip()
            logger.debug(f"    -> Generated description: {description[:100]}...")
            return description

        except Exception as e:
            error_msg = f"Groq API error: {e}"
            logger.error(error_msg)
            raise GroqAPIError(error_msg) from e

    async def describe_from_file(self, image_path: Path) -> str:
        """Generate description for stamp image from local file.

        Args:
            image_path: Path to the stamp image file

        Returns:
            Textual description of the stamp

        Raises:
            DescriptionError: If file cannot be read or description fails
        """
        logger.debug(f" * describe_from_file > Starting for {image_path}")

        if not image_path.exists():
            raise DescriptionError(f"Image file not found: {image_path}")

        # Determine media type from extension
        extension = image_path.suffix.lower()
        media_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        media_type = media_types.get(extension, "image/jpeg")

        # Read and encode image
        try:
            image_data = image_path.read_bytes()
            image_base64 = base64.b64encode(image_data).decode("utf-8")
        except Exception as e:
            raise DescriptionError(f"Failed to read image {image_path}: {e}") from e

        return await self.describe_from_base64(image_base64, media_type)

    async def describe_batch(
        self,
        items: list[tuple[str, str]],
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> dict[str, str]:
        """Generate descriptions for multiple stamp images.

        Args:
            items: List of (id, image_url) tuples
            progress_callback: Optional callback(current, total, id) for progress updates

        Returns:
            Dict mapping id to description

        Note:
            Failed items are logged but not included in results.
            Rate limiting is automatically applied.
        """
        logger.info(f"Starting batch description of {len(items)} stamps")

        results: dict[str, str] = {}
        total = len(items)

        for idx, (item_id, image_url) in enumerate(items, 1):
            if progress_callback:
                progress_callback(idx, total, item_id)

            try:
                description = await self.describe_from_url(image_url)
                results[item_id] = description
            except Exception as e:
                logger.error(f"Failed to describe {item_id}: {e}")
                # Continue with next item

        logger.info(f"Batch description complete: {len(results)}/{total} successful")
        return results


async def download_and_describe(
    image_url: str,
    describer: Optional[StampDescriber] = None,
) -> str:
    """Download image and generate description.

    This is a convenience function that downloads an image from URL
    and passes it to the describer. Useful when direct URL access
    doesn't work with the vision API.

    Args:
        image_url: URL of the image to download
        describer: StampDescriber instance (creates new if not provided)

    Returns:
        Textual description of the stamp
    """
    if describer is None:
        describer = StampDescriber()

    # Try direct URL first
    try:
        return await describer.describe_from_url(image_url)
    except GroqAPIError:
        logger.debug("Direct URL failed, downloading image...")

    # Download and encode as base64
    async with httpx.AsyncClient() as client:
        response = await client.get(image_url, follow_redirects=True)
        response.raise_for_status()

        content_type = response.headers.get("content-type", "image/jpeg")
        image_base64 = base64.b64encode(response.content).decode("utf-8")

        return await describer.describe_from_base64(image_base64, content_type)
