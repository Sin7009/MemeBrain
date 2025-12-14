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

        Updated behavior: Should return None instead of raising ValueError.
        """
        generator = MemeGenerator()

        # Create a 1x1 pixel image
        tiny_image = Image.new('RGB', (1, 1), color='white')

        # Mock _download_image to return the tiny image
        with patch.object(generator, '_download_image', return_value=tiny_image):
            # Expect gracefully handling (return None)
            result = generator.create_meme(
                image_url="http://example.com/tiny.jpg",
                top_text="CRASH",
                bottom_text="BOOM",
                output_path="destructive_output.jpg"
            )
            assert result is None

    def test_create_meme_crash_on_non_image_content(self):
        """
        Logic Prone to Failure: Data Structures / Malformed Data.

        Updated behavior: Should return None (handled internally) instead of raising UnidentifiedImageError.
        """
        generator = MemeGenerator()

        # Mock content that is definitely not an image
        fake_content = b"<html><body>This is not an image</body></html>"

        # We mock _download_image_bytes to return this content
        # Note: We must NOT mock _download_image because we want to test its error handling logic
        with patch.object(generator, '_download_image_bytes', return_value=fake_content):
            result = generator.create_meme(
                image_url="http://example.com/not_an_image.html",
                top_text="TEXT",
                bottom_text="FILE",
                output_path="should_fail.jpg"
            )
            assert result is None

    def test_create_meme_file_too_large(self):
        """
        Security Test: Denial of Service via Large File.

        Ensures that files exceeding the size limit are rejected.
        """
        generator = MemeGenerator()

        # 6MB of dummy data (limit is 5MB)
        large_content = b"0" * (6 * 1024 * 1024)

        # We need to mock requests.get to return a response that behaves like a large file download
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.headers = {'Content-Length': str(len(large_content))}
            mock_response.iter_content.return_value = [large_content]
            mock_response.content = large_content
            mock_get.return_value.__enter__.return_value = mock_response

            # Since _download_image_bytes is cached, we need to ensure we're calling it with a fresh URL
            # or clear the cache if possible. For simplicity, use a unique URL.
            result = generator._download_image_bytes("http://example.com/large_file.jpg")

            assert result is None
