import pytest
from unittest.mock import patch, MagicMock
from PIL import Image, UnidentifiedImageError
from src.services.image_gen import MemeGenerator

class TestDestructiveMemeGenerator:
    """
    Test suite for destructive testing of MemeGenerator.
    Focus: Data Structures and Mathematical Boundaries.
    """

    def test_create_meme_crash_on_tiny_image(self):
        """
        Logic Prone to Failure: Division by zero / Invalid Argument.

        Why this breaks:
        The `_wrap_text` method calculates `max_chars_per_line` based on the image width.
        If the image is extremely small (e.g., 1x1 pixel), the calculated `font_size` is clamped to 20.
        However, the `avg_char_width` for font size 20 is significantly larger than the image width (1px).

        This results in `max_chars_per_line` being 0.
        Subsequently, `textwrap.wrap` is called with `width=0`, which raises a `ValueError`.

        This test case simulates downloading a tiny image and asserts that the current logic
        fails with a ValueError.
        """
        generator = MemeGenerator()

        # Create a 1x1 pixel image
        tiny_image = Image.new('RGB', (1, 1), color='white')

        # Mock _download_image to return the tiny image
        with patch.object(generator, '_download_image', return_value=tiny_image):
            # Assert that ValueError is raised due to invalid width in textwrap
            with pytest.raises(ValueError, match="invalid width 0"):
                generator.create_meme(
                    image_url="http://example.com/tiny.jpg",
                    top_text="CRASH",
                    bottom_text="BOOM",
                    output_path="destructive_output.jpg"
                )

    def test_create_meme_crash_on_non_image_content(self):
        """
        Logic Prone to Failure: Data Structures / Malformed Data.

        Why this breaks:
        The `_download_image` method in `MemeGenerator` downloads bytes and immediately passes them
        to `Image.open(io.BytesIO(image_bytes))`.

        If the URL returns a 200 OK status but the content is NOT an image (e.g., HTML, plain text, JSON),
        `Image.open` raises an `UnidentifiedImageError`.

        The current implementation catches `requests.exceptions.RequestException` during download,
        but does NOT catch exceptions during `Image.open`.

        This unhandled exception will propagate up and crash the calling service or bot handler.

        This test simulates a successful download of a text file (acting as a corrupted or wrong image)
        and asserts that the generator raises `UnidentifiedImageError`.
        """
        generator = MemeGenerator()

        # Mock content that is definitely not an image
        fake_content = b"<html><body>This is not an image</body></html>"

        # We mock _download_image_bytes to return this content
        with patch.object(generator, '_download_image_bytes', return_value=fake_content):
            # We expect the code to CRASH with UnidentifiedImageError.
            with pytest.raises(UnidentifiedImageError):
                generator.create_meme(
                    image_url="http://example.com/not_an_image.html",
                    top_text="TEXT",
                    bottom_text="FILE",
                    output_path="should_fail.jpg"
                )
