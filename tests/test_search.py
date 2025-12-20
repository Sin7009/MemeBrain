import pytest
from unittest.mock import patch, MagicMock
from src.services.search import ImageSearcher
from src.services.config import config
import requests

@pytest.fixture
def searcher():
    with patch.object(config, 'SEARCH_MOCK_ENABLED', False):
        searcher_instance = ImageSearcher()
        searcher_instance.mock_enabled = False
        yield searcher_instance

def test_search_template_success(searcher):
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
        url = searcher.search_template("funny cat")
        assert url == "http://example.com/meme.jpg"
        mock_post.assert_called_once()
        # Verify call args
        args, kwargs = mock_post.call_args
        assert kwargs['json']['query'] == "funny cat"
        assert kwargs['json']['include_images'] is True

def test_search_template_no_results(searcher):
    mock_response = MagicMock()
    mock_response.json.return_value = {"images": []}

    with patch('requests.post', return_value=mock_response):
        url = searcher.search_template("ghost")
        assert url is None

def test_search_template_error(searcher):
    # This simulates a request exception which is caught and logged
    with patch('requests.post', side_effect=requests.exceptions.RequestException("API Error")):
        url = searcher.search_template("crash")
        assert url is None
