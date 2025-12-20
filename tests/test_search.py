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
    mock_response.json.return_value = {
        "items": [
            {"link": "http://example.com/meme.jpg"}
        ]
    }
    mock_response.raise_for_status.return_value = None

    with patch('requests.get', return_value=mock_response) as mock_get:
        url = searcher.search_template("funny cat")
        assert url == "http://example.com/meme.jpg"
        mock_get.assert_called_once()

def test_search_template_no_results(searcher):
    mock_response = MagicMock()
    mock_response.json.return_value = {}

    with patch('requests.get', return_value=mock_response):
        url = searcher.search_template("ghost")
        assert url is None

def test_search_template_error(searcher):
    # This simulates a request exception which is caught and logged
    with patch('requests.get', side_effect=requests.exceptions.RequestException("API Error")):
        url = searcher.search_template("crash")
        assert url is None
