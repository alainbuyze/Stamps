"""Tests for image trimming functionality."""

import tempfile
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from src.image_trimmer import trim_image, trim_images_batch


class TestTrimImage:
    """Test suite for trim_image function."""

    @staticmethod
    def create_test_image_with_whitespace(
        size: tuple[int, int] = (200, 200),
        content_size: tuple[int, int] = (100, 100),
        content_color: str = "blue",
    ) -> Image.Image:
        """Create a test image with white border around content.

        Args:
            size: Total image size (width, height).
            content_size: Size of content area (width, height).
            content_color: Color of content rectangle.

        Returns:
            PIL Image with white borders.
        """
        # Create white image
        img = Image.new("RGB", size, "white")
        draw = ImageDraw.Draw(img)

        # Calculate content position (centered)
        x_offset = (size[0] - content_size[0]) // 2
        y_offset = (size[1] - content_size[1]) // 2

        # Draw content rectangle
        draw.rectangle(
            [x_offset, y_offset, x_offset + content_size[0], y_offset + content_size[1]],
            fill=content_color,
        )

        return img

    def test_trim_basic(self):
        """Test basic whitespace trimming."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test image with whitespace
            img = self.create_test_image_with_whitespace(
                size=(200, 200), content_size=(100, 100)
            )
            input_path = Path(tmpdir) / "input.png"
            output_path = Path(tmpdir) / "output.png"
            img.save(input_path)

            # Trim image
            result = trim_image(input_path, output_path)

            assert result == output_path
            assert output_path.exists()

            # Check that output is smaller than input
            with Image.open(output_path) as trimmed:
                assert trimmed.size[0] <= 100
                assert trimmed.size[1] <= 100
                assert trimmed.size[0] < 200  # Should be trimmed
                assert trimmed.size[1] < 200  # Should be trimmed

    def test_trim_with_border(self):
        """Test trimming with border addition."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test image
            img = self.create_test_image_with_whitespace(
                size=(200, 200), content_size=(100, 100)
            )
            input_path = Path(tmpdir) / "input.png"
            output_path = Path(tmpdir) / "output.png"
            img.save(input_path)

            # Trim with 5px border
            border_width = 5
            result = trim_image(input_path, output_path, border_width=border_width)

            assert result.exists()

            # Check that border was added
            with Image.open(output_path) as trimmed:
                # Size should be content + 2*border (border on each side)
                expected_min_size = 100 + (2 * border_width)
                assert trimmed.size[0] >= expected_min_size - 2  # Allow small variance
                assert trimmed.size[1] >= expected_min_size - 2

                # Check corner pixel is black (border color)
                corner_pixel = trimmed.getpixel((0, 0))
                assert corner_pixel == (0, 0, 0)  # Black

    def test_trim_inplace(self):
        """Test trimming in-place (no output path specified)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test image
            img = self.create_test_image_with_whitespace(
                size=(200, 200), content_size=(100, 100)
            )
            input_path = Path(tmpdir) / "input.png"
            img.save(input_path)

            original_size = img.size

            # Trim in-place
            result = trim_image(input_path)

            assert result == input_path
            assert input_path.exists()

            # Check that file was modified
            with Image.open(input_path) as trimmed:
                assert trimmed.size[0] < original_size[0]
                assert trimmed.size[1] < original_size[1]

    def test_trim_no_whitespace(self):
        """Test trimming image with no whitespace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create image with no whitespace (entirely blue)
            img = Image.new("RGB", (100, 100), "blue")
            input_path = Path(tmpdir) / "input.png"
            output_path = Path(tmpdir) / "output.png"
            img.save(input_path)

            # Trim image
            result = trim_image(input_path, output_path)

            assert result.exists()

            # Size should be unchanged
            with Image.open(output_path) as trimmed:
                assert trimmed.size == (100, 100)

    def test_trim_entirely_white(self):
        """Test trimming entirely white image."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create entirely white image
            img = Image.new("RGB", (100, 100), "white")
            input_path = Path(tmpdir) / "input.png"
            output_path = Path(tmpdir) / "output.png"
            img.save(input_path)

            # Trim image
            result = trim_image(input_path, output_path)

            assert result.exists()

            # Size should be unchanged (nothing to trim)
            with Image.open(output_path) as trimmed:
                assert trimmed.size == (100, 100)

    def test_trim_rgba_image(self):
        """Test trimming RGBA image with transparency."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create RGBA image with transparency
            img = Image.new("RGBA", (200, 200), (255, 255, 255, 0))  # Transparent white
            draw = ImageDraw.Draw(img)
            # Draw opaque blue rectangle
            draw.rectangle([50, 50, 150, 150], fill=(0, 0, 255, 255))

            input_path = Path(tmpdir) / "input.png"
            output_path = Path(tmpdir) / "output.png"
            img.save(input_path)

            # Trim image
            result = trim_image(input_path, output_path)

            assert result.exists()

            # Check that output is smaller
            with Image.open(output_path) as trimmed:
                assert trimmed.size[0] <= 100
                assert trimmed.size[1] <= 100

    def test_trim_custom_border_color(self):
        """Test trimming with custom border color."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test image
            img = self.create_test_image_with_whitespace(
                size=(200, 200), content_size=(100, 100)
            )
            input_path = Path(tmpdir) / "input.png"
            output_path = Path(tmpdir) / "output.png"
            img.save(input_path)

            # Trim with red border
            result = trim_image(input_path, output_path, border_width=3, border_color="red")

            assert result.exists()

            # Check corner pixel is red
            with Image.open(output_path) as trimmed:
                corner_pixel = trimmed.getpixel((0, 0))
                assert corner_pixel == (255, 0, 0)  # Red

    def test_trim_nonexistent_file(self):
        """Test trimming non-existent file raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "nonexistent.png"
            output_path = Path(tmpdir) / "output.png"

            with pytest.raises(FileNotFoundError):
                trim_image(input_path, output_path)

    def test_trim_negative_border(self):
        """Test that negative border width raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            img = Image.new("RGB", (100, 100), "blue")
            input_path = Path(tmpdir) / "input.png"
            output_path = Path(tmpdir) / "output.png"
            img.save(input_path)

            with pytest.raises(ValueError, match="border_width must be non-negative"):
                trim_image(input_path, output_path, border_width=-5)

    def test_trim_creates_output_directory(self):
        """Test that trim creates output directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            img = Image.new("RGB", (100, 100), "blue")
            input_path = Path(tmpdir) / "input.png"
            output_path = Path(tmpdir) / "subdir" / "output.png"
            img.save(input_path)

            # Output directory doesn't exist
            assert not output_path.parent.exists()

            # Trim should create it
            result = trim_image(input_path, output_path)

            assert output_path.parent.exists()
            assert result.exists()

    def test_trim_asymmetric_whitespace(self):
        """Test trimming image with asymmetric whitespace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create image with different whitespace on each side
            img = Image.new("RGB", (300, 250), "white")
            draw = ImageDraw.Draw(img)
            # Draw blue rectangle offset to top-left
            draw.rectangle([10, 10, 110, 110], fill="blue")

            input_path = Path(tmpdir) / "input.png"
            output_path = Path(tmpdir) / "output.png"
            img.save(input_path)

            # Trim image
            result = trim_image(input_path, output_path)

            assert result.exists()

            # Should be trimmed to approximately 100x100
            with Image.open(output_path) as trimmed:
                assert trimmed.size[0] <= 110
                assert trimmed.size[1] <= 110
                assert trimmed.size[0] >= 100
                assert trimmed.size[1] >= 100


class TestTrimImagesBatch:
    """Test suite for trim_images_batch function."""

    @staticmethod
    def create_test_images(tmpdir: str, count: int = 3) -> list[Path]:
        """Create multiple test images with whitespace.

        Args:
            tmpdir: Temporary directory path.
            count: Number of images to create.

        Returns:
            List of created image paths.
        """
        paths = []
        for i in range(count):
            img = Image.new("RGB", (200, 200), "white")
            draw = ImageDraw.Draw(img)
            draw.rectangle([50, 50, 150, 150], fill="blue")

            path = Path(tmpdir) / f"image_{i}.png"
            img.save(path)
            paths.append(path)

        return paths

    def test_batch_trim_basic(self):
        """Test batch trimming of multiple images."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test images
            input_paths = self.create_test_images(tmpdir, count=3)
            output_dir = Path(tmpdir) / "output"

            # Trim batch
            results = trim_images_batch(input_paths, output_dir)

            assert len(results) == 3
            assert output_dir.exists()

            # Check all output files exist and are trimmed
            for result_path in results:
                assert result_path.exists()
                with Image.open(result_path) as img:
                    assert img.size[0] <= 100
                    assert img.size[1] <= 100

    def test_batch_trim_with_border(self):
        """Test batch trimming with border."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_paths = self.create_test_images(tmpdir, count=2)
            output_dir = Path(tmpdir) / "output"

            # Trim with border
            results = trim_images_batch(input_paths, output_dir, border_width=5)

            assert len(results) == 2

            # Check border was added to all images
            for result_path in results:
                with Image.open(result_path) as img:
                    # Should have border
                    corner_pixel = img.getpixel((0, 0))
                    assert corner_pixel == (0, 0, 0)  # Black border

    def test_batch_trim_skip_existing(self):
        """Test batch trimming skips existing files when overwrite=False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_paths = self.create_test_images(tmpdir, count=3)
            output_dir = Path(tmpdir) / "output"
            output_dir.mkdir(parents=True)

            # Create one existing file
            existing_file = output_dir / "image_0.png"
            Image.new("RGB", (50, 50), "red").save(existing_file)
            original_size = existing_file.stat().st_size

            # Trim batch without overwrite
            results = trim_images_batch(input_paths, output_dir, overwrite=False)

            assert len(results) == 3

            # Check that existing file was NOT overwritten
            assert existing_file.stat().st_size == original_size

    def test_batch_trim_overwrite_existing(self):
        """Test batch trimming overwrites existing files when overwrite=True."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_paths = self.create_test_images(tmpdir, count=2)
            output_dir = Path(tmpdir) / "output"
            output_dir.mkdir(parents=True)

            # Create existing file
            existing_file = output_dir / "image_0.png"
            Image.new("RGB", (50, 50), "red").save(existing_file)
            original_size = existing_file.stat().st_size

            # Trim batch with overwrite
            results = trim_images_batch(input_paths, output_dir, overwrite=True)

            assert len(results) == 2

            # Check that existing file WAS overwritten
            assert existing_file.stat().st_size != original_size

    def test_batch_trim_empty_list(self):
        """Test batch trimming with empty input list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"

            results = trim_images_batch([], output_dir)

            assert len(results) == 0
            assert output_dir.exists()  # Directory should still be created

    def test_batch_trim_handles_errors(self):
        """Test batch trimming continues after individual errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mix of valid images and non-existent paths
            valid_paths = self.create_test_images(tmpdir, count=2)
            invalid_path = Path(tmpdir) / "nonexistent.png"
            mixed_paths = [valid_paths[0], invalid_path, valid_paths[1]]

            output_dir = Path(tmpdir) / "output"

            # Should not raise, but should process valid images
            results = trim_images_batch(mixed_paths, output_dir)

            # Should have processed only the valid images
            assert len(results) == 2
            assert all(p.exists() for p in results)

    def test_batch_trim_creates_output_directory(self):
        """Test that batch trim creates output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_paths = self.create_test_images(tmpdir, count=1)
            output_dir = Path(tmpdir) / "nested" / "output"

            assert not output_dir.exists()

            results = trim_images_batch(input_paths, output_dir)

            assert output_dir.exists()
            assert len(results) == 1
