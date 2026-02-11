import pytest
from unittest.mock import patch, MagicMock
from src.services.llm import MemeBrain
from src.services.config import config

@pytest.fixture
def brain():
    with patch.object(config, 'LLM_MOCK_ENABLED', False):
        brain_instance = MemeBrain()
        brain_instance.mock_enabled = False
        yield brain_instance

def test_decide_content_meme(brain):
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content='```json\n{"action": "generate_meme", "search_query": "funny cat", "top_text": "TOP", "bottom_text": "BOTTOM"}\n```'))
    ]

    brain.client = MagicMock()
    brain.client.chat.completions.create.return_value = mock_response

    context = ["User: Hi"]
    trigger = "Hi"
    result = brain.decide_content(context, trigger)

    assert result is not None
    assert result['action'] == "generate_meme"
    assert result['top_text'] == "TOP"
    assert result['bottom_text'] == "BOTTOM"

def test_decide_content_gif(brain):
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content='{"action": "search_gif", "search_query": "facepalm"}'))
    ]

    brain.client = MagicMock()
    brain.client.chat.completions.create.return_value = mock_response

    result = brain.decide_content(["Hi"], "Hi")

    assert result is not None
    assert result['action'] == "search_gif"
    assert result['search_query'] == "facepalm"

def test_decide_content_api_error(brain):
    brain.client = MagicMock()
    brain.client.chat.completions.create.side_effect = Exception("API Fail")

    result = brain.decide_content(["Hi"], "Hi")
    assert result is None

def test_decide_content_bad_json(brain):
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content='Not JSON'))
    ]
    brain.client = MagicMock()
    brain.client.chat.completions.create.return_value = mock_response

    result = brain.decide_content(["Hi"], "Hi")
    assert result is None

def test_decide_content_missing_search_query_recovery(brain):
    """Test that missing search_query is recovered from reasoning"""
    mock_response = MagicMock()
    # OpenRouter forgot search_query but provided reasoning
    mock_response.choices = [
        MagicMock(message=MagicMock(content='{"action": "search_image", "reasoning": "cute puppy"}'))
    ]

    brain.client = MagicMock()
    brain.client.chat.completions.create.return_value = mock_response

    result = brain.decide_content(["User: Hi"], "Hi")

    assert result is not None
    assert result['action'] == "search_image"
    assert result['search_query'] == "cute puppy" # Recovered from reasoning
