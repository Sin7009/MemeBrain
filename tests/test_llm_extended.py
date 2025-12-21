import pytest
from unittest.mock import patch, MagicMock
from src.services.llm import MemeBrain
from src.services.config import config


class TestMemeBrainExtended:
    """Extended tests for MemeBrain edge cases"""
    
    @pytest.fixture
    def brain(self):
        """Create brain instance with mocking disabled"""
        with patch.object(config, 'LLM_MOCK_ENABLED', False):
            brain_instance = MemeBrain()
            brain_instance.mock_enabled = False
            yield brain_instance
    
    def test_mock_mode_enabled(self):
        """Test that mock mode returns predefined response"""
        with patch.object(config, 'LLM_MOCK_ENABLED', True):
            brain = MemeBrain()
            brain.mock_enabled = True
            
            result = brain.generate_meme_idea(
                context_messages=["User: Test"],
                triggered_text="Test",
                reaction_context="Смех"
            )
            
            assert result is not None
            assert result['is_memable'] is True
            assert 'top_text' in result
            assert 'bottom_text' in result
            assert 'search_query' in result
    
    def test_generate_meme_idea_with_reaction_context(self, brain):
        """Test meme generation with reaction context"""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(
                content='{"is_memable": true, "top_text": "ANGRY", "bottom_text": "TEXT", "search_query": "angry cat"}'
            ))
        ]
        
        brain.client = MagicMock()
        brain.client.chat.completions.create.return_value = mock_response
        
        result = brain.generate_meme_idea(
            context_messages=["User: This is bad"],
            triggered_text="This is bad",
            reaction_context="Злость, ярость"
        )
        
        assert result is not None
        assert result['is_memable'] is True
        
        # Check that reaction context was included in prompt
        call_args = brain.client.chat.completions.create.call_args
        prompt = call_args[1]['messages'][1]['content']
        assert "Злость, ярость" in prompt
    
    def test_generate_meme_idea_empty_context(self, brain):
        """Test meme generation with empty context"""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(
                content='{"is_memable": true, "top_text": "T", "bottom_text": "B", "search_query": "q"}'
            ))
        ]
        
        brain.client = MagicMock()
        brain.client.chat.completions.create.return_value = mock_response
        
        result = brain.generate_meme_idea(
            context_messages=[],
            triggered_text="Test",
            reaction_context=None
        )
        
        # Should still work with empty context
        assert result is not None
    
    def test_generate_meme_idea_is_memable_false(self, brain):
        """Test when LLM returns is_memable: false"""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(
                content='{"is_memable": false, "top_text": "", "bottom_text": "", "search_query": ""}'
            ))
        ]
        
        brain.client = MagicMock()
        brain.client.chat.completions.create.return_value = mock_response
        
        result = brain.generate_meme_idea(
            context_messages=["User: boring"],
            triggered_text="boring"
        )
        
        # Should return None when not memable
        assert result is None
    
    def test_generate_meme_idea_malformed_json(self, brain):
        """Test handling of malformed JSON response"""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(
                content='{"is_memable": true, "top_text": "TEXT" // missing fields'
            ))
        ]
        
        brain.client = MagicMock()
        brain.client.chat.completions.create.return_value = mock_response
        
        result = brain.generate_meme_idea(
            context_messages=["User: test"],
            triggered_text="test"
        )
        
        assert result is None
    
    def test_generate_meme_idea_network_timeout(self, brain):
        """Test handling of network timeout"""
        brain.client = MagicMock()
        brain.client.chat.completions.create.side_effect = TimeoutError("Request timeout")
        
        result = brain.generate_meme_idea(
            context_messages=["User: test"],
            triggered_text="test"
        )
        
        assert result is None
    
    def test_generate_meme_idea_empty_response(self, brain):
        """Test handling of empty response from API"""
        mock_response = MagicMock()
        mock_response.choices = []
        
        brain.client = MagicMock()
        brain.client.chat.completions.create.return_value = mock_response
        
        result = brain.generate_meme_idea(
            context_messages=["User: test"],
            triggered_text="test"
        )
        
        # Should handle gracefully
        assert result is None
    
    def test_generate_meme_idea_missing_required_fields(self, brain):
        """Test handling of response missing required fields"""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(
                content='{"is_memable": true, "top_text": "TEXT"}'  # missing bottom_text and search_query
            ))
        ]
        
        brain.client = MagicMock()
        brain.client.chat.completions.create.return_value = mock_response
        
        result = brain.generate_meme_idea(
            context_messages=["User: test"],
            triggered_text="test"
        )
        
        # Should return None if required fields missing
        assert result is None
    
    def test_generate_meme_idea_special_characters(self, brain):
        """Test with special characters in text"""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(
                content='{"is_memable": true, "top_text": "TOP", "bottom_text": "BOTTOM", "search_query": "query"}'
            ))
        ]
        
        brain.client = MagicMock()
        brain.client.chat.completions.create.return_value = mock_response
        
        result = brain.generate_meme_idea(
            context_messages=["User: Test <html> & \"quotes\""],
            triggered_text="Test <html> & \"quotes\""
        )
        
        assert result is not None
        assert result['is_memable'] is True
