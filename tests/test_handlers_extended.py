import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from src.bot.handlers import (
    command_help_handler,
    message_handler,
    generate_and_send_meme
)
from aiogram.types import Message, Chat, User


def create_message(text="Hello", chat_id=123, user_id=456, chat_type='private'):
    """Helper to create mock messages"""
    msg = AsyncMock(spec=Message)
    msg.text = text
    msg.chat = AsyncMock(spec=Chat)
    msg.chat.id = chat_id
    msg.chat.type = chat_type
    msg.from_user = AsyncMock(spec=User)
    msg.from_user.id = user_id
    msg.from_user.first_name = "User"
    msg.from_user.username = "testuser"
    msg.message_id = 1
    msg.answer = AsyncMock()
    msg.reply_photo = AsyncMock()
    msg.bot = AsyncMock()
    msg.bot.send_chat_action = AsyncMock()
    msg.bot.send_photo = AsyncMock()
    msg.bot.send_message = AsyncMock()
    return msg


@pytest.mark.asyncio
async def test_command_help():
    """Test /help command handler"""
    msg = create_message(text="/help")
    await command_help_handler(msg)
    msg.answer.assert_called_once()
    call_args = msg.answer.call_args[0][0]
    assert "Как пользоваться ботом" in call_args
    assert "Реакция" in call_args


@pytest.mark.asyncio
async def test_message_handler_private_chat():
    """Test message handler in private chat triggers meme generation"""
    msg = create_message(text="Test message", chat_type='private')
    
    with patch('src.bot.handlers.history_manager') as mock_hist, \
         patch('src.bot.handlers.meme_brain') as mock_brain, \
         patch('src.bot.handlers.image_searcher') as mock_search, \
         patch('src.bot.handlers.meme_generator') as mock_gen, \
         patch('src.bot.handlers.FSInputFile'):
        
        mock_hist.get_context.return_value = ["User: Test message"]
        mock_brain.generate_meme_idea.return_value = {
            "is_memable": True,
            "top_text": "TOP",
            "bottom_text": "BOTTOM",
            "search_query": "query"
        }
        mock_search.search_template.return_value = "http://img.jpg"
        mock_gen.create_meme.return_value = "output.jpg"
        
        await message_handler(msg)
        
        # Should add to history
        mock_hist.add_message.assert_called_once_with(msg)
        # Should send photo in private chat
        msg.bot.send_photo.assert_called_once()


@pytest.mark.asyncio
async def test_message_handler_group_chat():
    """Test message handler in group chat only saves to history"""
    msg = create_message(text="Group message", chat_type='group')
    
    with patch('src.bot.handlers.history_manager') as mock_hist:
        await message_handler(msg)
        
        # Should add to history
        mock_hist.add_message.assert_called_once_with(msg)
        # Should NOT send photo in group chat
        msg.bot.send_photo.assert_not_called()


@pytest.mark.asyncio
async def test_message_handler_command_ignored():
    """Test that commands starting with / are ignored in private chat"""
    msg = create_message(text="/command", chat_type='private')
    
    with patch('src.bot.handlers.history_manager') as mock_hist:
        await message_handler(msg)
        
        # Should add to history
        mock_hist.add_message.assert_called_once()
        # Should NOT generate meme for commands
        msg.bot.send_photo.assert_not_called()


@pytest.mark.asyncio
async def test_generate_and_send_meme_llm_failure():
    """Test generate_and_send_meme when LLM returns None"""
    msg = create_message()
    
    with patch('src.bot.handlers.meme_brain') as mock_brain:
        mock_brain.generate_meme_idea.return_value = None
        
        await generate_and_send_meme(
            chat_id=123,
            triggered_text="Test",
            context_messages=["User: Test"],
            bot_instance=msg.bot,
            reply_to_message_id=1
        )
        
        # Should send error message
        msg.bot.send_message.assert_called_once()
        assert "Мозги сломались" in msg.bot.send_message.call_args[0][1]


@pytest.mark.asyncio
async def test_generate_and_send_meme_not_memable():
    """Test generate_and_send_meme when LLM says not memable"""
    msg = create_message()
    
    with patch('src.bot.handlers.meme_brain') as mock_brain:
        mock_brain.generate_meme_idea.return_value = {
            "is_memable": False,
            "top_text": "",
            "bottom_text": "",
            "search_query": ""
        }
        
        await generate_and_send_meme(
            chat_id=123,
            triggered_text="Test",
            context_messages=["User: Test"],
            bot_instance=msg.bot,
            reply_to_message_id=1
        )
        
        # Should not send anything
        msg.bot.send_message.assert_not_called()
        msg.bot.send_photo.assert_not_called()


@pytest.mark.asyncio
async def test_generate_and_send_meme_search_failure():
    """Test generate_and_send_meme when search returns no results"""
    msg = create_message()
    
    with patch('src.bot.handlers.meme_brain') as mock_brain, \
         patch('src.bot.handlers.image_searcher') as mock_search:
        
        mock_brain.generate_meme_idea.return_value = {
            "is_memable": True,
            "top_text": "TOP",
            "bottom_text": "BOTTOM",
            "search_query": "query"
        }
        mock_search.search_template.return_value = None
        
        await generate_and_send_meme(
            chat_id=123,
            triggered_text="Test",
            context_messages=["User: Test"],
            bot_instance=msg.bot,
            reply_to_message_id=1
        )
        
        # Should send error message about template not found
        msg.bot.send_message.assert_called_once()
        assert "Шаблон не найден" in msg.bot.send_message.call_args[0][1]


@pytest.mark.asyncio
async def test_generate_and_send_meme_image_gen_failure():
    """Test generate_and_send_meme when image generation fails"""
    msg = create_message()
    
    with patch('src.bot.handlers.meme_brain') as mock_brain, \
         patch('src.bot.handlers.image_searcher') as mock_search, \
         patch('src.bot.handlers.meme_generator') as mock_gen:
        
        mock_brain.generate_meme_idea.return_value = {
            "is_memable": True,
            "top_text": "TOP",
            "bottom_text": "BOTTOM",
            "search_query": "query"
        }
        mock_search.search_template.return_value = "http://img.jpg"
        mock_gen.create_meme.return_value = None
        
        await generate_and_send_meme(
            chat_id=123,
            triggered_text="Test",
            context_messages=["User: Test"],
            bot_instance=msg.bot,
            reply_to_message_id=1
        )
        
        # Should send error message
        msg.bot.send_message.assert_called_once()
        assert "Не удалось создать картинку" in msg.bot.send_message.call_args[0][1]
