import pytest
from unittest.mock import patch, AsyncMock
from src.bot.handlers import generate_and_send_meme
from aiogram.types import Message, Chat


@pytest.mark.asyncio
async def test_generate_and_send_meme_no_bot_instance():
    """Test that function returns early if bot_instance is None"""
    result = await generate_and_send_meme(
        chat_id=123,
        triggered_text="Test",
        context_messages=["User: Test"],
        bot_instance=None
    )
    
    # Should return early without errors
    assert result is None


@pytest.mark.asyncio
async def test_generate_and_send_meme_empty_triggered_text():
    """Test that function returns early if triggered_text is empty"""
    bot = AsyncMock()
    
    result = await generate_and_send_meme(
        chat_id=123,
        triggered_text="",
        context_messages=["User: Test"],
        bot_instance=bot
    )
    
    # Should return early without calling any bot methods
    bot.send_chat_action.assert_not_called()
    assert result is None


@pytest.mark.asyncio
async def test_generate_and_send_meme_whitespace_triggered_text():
    """Test that function returns early if triggered_text is only whitespace"""
    bot = AsyncMock()
    
    result = await generate_and_send_meme(
        chat_id=123,
        triggered_text="   \n\t  ",
        context_messages=["User: Test"],
        bot_instance=bot
    )
    
    # Should return early without calling any bot methods
    bot.send_chat_action.assert_not_called()
    assert result is None


@pytest.mark.asyncio
async def test_generate_and_send_meme_empty_context():
    """Test that function returns early if context_messages is empty"""
    bot = AsyncMock()
    bot.send_chat_action = AsyncMock()
    
    result = await generate_and_send_meme(
        chat_id=123,
        triggered_text="Test",
        context_messages=[],
        bot_instance=bot
    )
    
    # Should return early without generating meme
    bot.send_chat_action.assert_not_called()
    assert result is None


@pytest.mark.asyncio
async def test_generate_and_send_meme_send_photo_exception():
    """Test error handling when send_photo raises exception"""
    bot = AsyncMock()
    bot.send_chat_action = AsyncMock()
    bot.send_photo = AsyncMock(side_effect=Exception("Network error"))
    bot.send_message = AsyncMock()
    
    with patch('src.bot.handlers.meme_brain') as mock_brain, \
         patch('src.bot.handlers.image_searcher') as mock_search, \
         patch('src.bot.handlers.meme_generator') as mock_gen, \
         patch('src.bot.handlers.FSInputFile'), \
         patch('os.path.exists', return_value=True), \
         patch('os.remove') as mock_remove:
        
        mock_brain.generate_meme_idea.return_value = {
            "is_memable": True,
            "top_text": "TOP",
            "bottom_text": "BOTTOM",
            "search_query": "query"
        }
        mock_search.search_template.return_value = "http://img.jpg"
        mock_gen.create_meme.return_value = "output.jpg"
        
        await generate_and_send_meme(
            chat_id=123,
            triggered_text="Test",
            context_messages=["User: Test"],
            bot_instance=bot,
            reply_to_message_id=1
        )
        
        # Should handle error and send error message
        bot.send_message.assert_called_once()
        assert "Ошибка отправки мема" in bot.send_message.call_args[0][1]
        
        # Should still clean up file
        mock_remove.assert_called_once()


@pytest.mark.asyncio
async def test_generate_and_send_meme_cleanup_on_error():
    """Test that temporary file is cleaned up even when errors occur"""
    bot = AsyncMock()
    bot.send_chat_action = AsyncMock()
    bot.send_photo = AsyncMock(side_effect=Exception("Error"))
    bot.send_message = AsyncMock()
    
    with patch('src.bot.handlers.meme_brain') as mock_brain, \
         patch('src.bot.handlers.image_searcher') as mock_search, \
         patch('src.bot.handlers.meme_generator') as mock_gen, \
         patch('src.bot.handlers.FSInputFile'), \
         patch('os.path.exists', return_value=True), \
         patch('os.remove') as mock_remove:
        
        mock_brain.generate_meme_idea.return_value = {
            "is_memable": True,
            "top_text": "TOP",
            "bottom_text": "BOTTOM",
            "search_query": "query"
        }
        mock_search.search_template.return_value = "http://img.jpg"
        mock_gen.create_meme.return_value = "test_output.jpg"
        
        await generate_and_send_meme(
            chat_id=123,
            triggered_text="Test",
            context_messages=["User: Test"],
            bot_instance=bot
        )
        
        # Should clean up file even on error
        mock_remove.assert_called_once_with("test_output.jpg")


@pytest.mark.asyncio
async def test_generate_and_send_meme_cleanup_exception():
    """Test that cleanup exception is handled gracefully"""
    bot = AsyncMock()
    bot.send_chat_action = AsyncMock()
    bot.send_photo = AsyncMock()
    
    with patch('src.bot.handlers.meme_brain') as mock_brain, \
         patch('src.bot.handlers.image_searcher') as mock_search, \
         patch('src.bot.handlers.meme_generator') as mock_gen, \
         patch('src.bot.handlers.FSInputFile'), \
         patch('os.path.exists', return_value=True), \
         patch('os.remove', side_effect=OSError("Permission denied")):
        
        mock_brain.generate_meme_idea.return_value = {
            "is_memable": True,
            "top_text": "TOP",
            "bottom_text": "BOTTOM",
            "search_query": "query"
        }
        mock_search.search_template.return_value = "http://img.jpg"
        mock_gen.create_meme.return_value = "output.jpg"
        
        # Should not raise exception
        await generate_and_send_meme(
            chat_id=123,
            triggered_text="Test",
            context_messages=["User: Test"],
            bot_instance=bot
        )
        
        # Photo should still be sent
        bot.send_photo.assert_called_once()
