import pytest
from unittest.mock import patch, MagicMock
from src.services.search import ContentSearcher
from src.services.config import config
import requests

@pytest.fixture
def searcher():
    with patch.object(config, 'SEARCH_MOCK_ENABLED', False):
        searcher_instance = ContentSearcher()
        searcher_instance.mock_enabled = False
        yield searcher_instance

def test_search_image_success(searcher):
    mock_response = MagicMock()
    # Mock Tavily response structure
    mock_response.json.return_value = {
        "images": [
            "http://example.com/meme.jpg",
            "http://example.com/meme2.jpg"
        ],
        "results": []
    }
    mock_response.raise_for_status.return_value = None

    with patch('requests.post', return_value=mock_response) as mock_post:
        url = searcher.search_image("funny cat")
        assert url == "http://example.com/meme.jpg"
        mock_post.assert_called_once()
        # Verify call args
        args, kwargs = mock_post.call_args
        assert kwargs['json']['query'] == "funny cat"
        assert kwargs['json']['include_images'] is True

def test_search_gif_success(searcher):
    searcher.giphy_api_key = "test_key"
    mock_response = MagicMock()
    # Mock Giphy response structure
    mock_response.json.return_value = {
        "data": [
            {
                "images": {
                    "original": {
                        "url": "http://giphy.com/funny.gif"
                    }
                }
            }
        ]
    }
    mock_response.raise_for_status.return_value = None

    with patch('requests.get', return_value=mock_response) as mock_get:
        url = searcher.search_gif("dancing cat")
        assert url == "http://giphy.com/funny.gif"
        mock_get.assert_called_once()
        # Verify call args
        args, kwargs = mock_get.call_args
        assert kwargs['params']['q'] == "dancing cat"
        assert kwargs['params']['api_key'] == "test_key"

def test_search_video(searcher):
    # This is a simple string formatting test
    url = searcher.search_video("rick roll")
    assert "youtube.com" in url
    assert "rick%20roll" in url

def test_search_image_caching(searcher):
    # Clear cache before test to ensure isolation
    ContentSearcher._search_image_cached.cache_clear()

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "images": ["http://example.com/cached.jpg"],
        "results": []
    }
    mock_response.raise_for_status.return_value = None

    with patch('requests.post', return_value=mock_response) as mock_post:
        # First call
        url1 = searcher.search_image("repeat query")
        assert url1 == "http://example.com/cached.jpg"

        # Second call - should be cached
        url2 = searcher.search_image("repeat query")
        assert url2 == "http://example.com/cached.jpg"

        # Verify network request happened only once
        mock_post.assert_called_once()
