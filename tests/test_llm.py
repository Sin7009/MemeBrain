import pytest
from unittest.mock import patch, MagicMock
from src.services.llm import MemeBrain
from src.services.config import config

@pytest.fixture
def brain():
    # Patch the config directly where it is used or instantiated
    # Since MemeBrain uses `config.LLM_MOCK_ENABLED` in __init__, we need to patch it before init
    # OR since we already have an instance, we can modify the instance attribute `mock_enabled`
    with patch.object(config, 'LLM_MOCK_ENABLED', False):
        brain_instance = MemeBrain()
        # Force instance mock_enabled to False just in case
        brain_instance.mock_enabled = False
        yield brain_instance

def test_generate_meme_idea_success(brain):
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content='```json\n{"is_memable": true, "top_text": "TOP", "bottom_text": "BOTTOM", "search_query": "QUERY"}\n```'))
    ]

    # Patch the OpenAI client create method
    brain.client = MagicMock()
    brain.client.chat.completions.create.return_value = mock_response

    context = ["User: Hi"]
    trigger = "Hi"
    result = brain.generate_meme_idea(context, trigger)

    assert result is not None
    assert result['top_text'] == "TOP"
    assert result['bottom_text'] == "BOTTOM"

def test_generate_meme_idea_api_error(brain):
    brain.client = MagicMock()
    brain.client.chat.completions.create.side_effect = Exception("API Fail")

    result = brain.generate_meme_idea(["Hi"], "Hi")
    assert result is None

def test_generate_meme_idea_bad_json(brain):
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content='Not JSON'))
    ]
    brain.client = MagicMock()
    brain.client.chat.completions.create.return_value = mock_response

    result = brain.generate_meme_idea(["Hi"], "Hi")
    assert result is None
