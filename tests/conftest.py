import os
import pytest
from unittest.mock import patch, MagicMock
from PIL import Image

# Set dummy env vars for pydantic validation BEFORE importing src modules
os.environ["TELEGRAM_BOT_TOKEN"] = "dummy_token"
os.environ["TAVILY_API_KEY"] = "dummy_key"
os.environ["OPENROUTER_API_KEY"] = "dummy_openrouter"
# Clean up old vars if they interfere (though pydantic allows extra)
if "GOOGLE_SEARCH_API_KEY" in os.environ:
    del os.environ["GOOGLE_SEARCH_API_KEY"]
if "GOOGLE_SEARCH_CX_ID" in os.environ:
    del os.environ["GOOGLE_SEARCH_CX_ID"]

@pytest.fixture(autouse=True)
def mock_settings_env():
    """Ensure env vars are set for all tests."""
    os.environ["TELEGRAM_BOT_TOKEN"] = "dummy_token"
    os.environ["TAVILY_API_KEY"] = "dummy_key"
    os.environ["OPENROUTER_API_KEY"] = "dummy_openrouter"

@pytest.fixture
def mock_fonts():
    """
    Mock ImageFont.truetype.
    Not autouse anymore to allow specific tests to use real fonts or load_default.
    """
    with patch('src.services.image_gen.ImageFont.truetype') as mock_font:
        font_instance = MagicMock()
        font_instance.getbbox.return_value = (0, 0, 10, 10)
        font_instance.getlength.return_value = 10
        font_instance.getmask2.return_value = (MagicMock(), (0,0))

        mock_font.return_value = font_instance
        yield mock_font
