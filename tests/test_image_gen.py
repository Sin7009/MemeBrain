import pytest
from unittest.mock import patch, MagicMock
from src.services.image_gen import MemeGenerator
from PIL import Image
import io

@pytest.fixture
def generator():
    # We pass a non-existent font to force fallback to load_default if we were running real code,
    # but in tests we might want to mock things.
    return MemeGenerator(font_path="invalid_path_to_force_default.ttf")

def test_download_image_bytes_success(generator):
    # Mock requests.get to return a context manager
    fake_image_data = b"fakeimage"

    mock_response = MagicMock()
    mock_response.headers = {'Content-Length': '9'}
    mock_response.iter_content.return_value = [fake_image_data]
    mock_response.status_code = 200
    mock_response.ok = True

    # IMPORTANT: requests.get returns a context manager
    mock_get = MagicMock()
    mock_get.__enter__.return_value = mock_response
    mock_get.__exit__.return_value = None

    with patch('requests.get', return_value=mock_get):
        # Clear cache
        generator._download_image_bytes.cache_clear()

        data = generator._download_image_bytes("http://example.com/img.jpg")
        assert data == fake_image_data

def test_download_image_too_large(generator):
    # Mock large content
    mock_response = MagicMock()
    mock_response.headers = {'Content-Length': str(11 * 1024 * 1024)} # 11MB
    mock_response.status_code = 200
    mock_response.ok = True

    mock_get = MagicMock()
    mock_get.__enter__.return_value = mock_response
    mock_get.__exit__.return_value = None

    with patch('requests.get', return_value=mock_get):
        generator._download_image_bytes.cache_clear()
        data = generator._download_image_bytes("http://example.com/big.jpg")
        assert data is None

def test_create_meme_logic(generator):
    # Logic test without network
    img = Image.new('RGB', (100, 100), color='red')

    # Mock _draw_text_with_shadow so we don't hit PIL drawing issues with mock/bitmap fonts
    with patch.object(generator, '_download_image', return_value=img), \
         patch.object(generator, '_draw_text_with_shadow') as mock_draw:

        output_path = "test_output.jpg"
        result_path = generator.create_meme(
            image_url="http://mock",
            top_text="Test",
            bottom_text="Meme",
            output_path=output_path
        )

        assert result_path == output_path

        # Check that we tried to draw text
        assert mock_draw.called

        # Verify file exists
        import os
        assert os.path.exists(output_path)
        os.remove(output_path)

def test_create_meme_fail_download(generator):
    with patch.object(generator, '_download_image', return_value=None):
        result = generator.create_meme(
            image_url="http://fail",
            top_text="T",
            bottom_text="B",
            output_path="out.jpg"
        )
        assert result is None
