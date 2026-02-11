import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from src.bot.handlers import command_start_handler, reaction_handler
from aiogram.types import Message, Chat, User, MessageReactionUpdated

# Helper to create mock messages
def create_message(text="Hello", chat_id=123, user_id=456):
    msg = AsyncMock(spec=Message)
    msg.text = text
    msg.chat = AsyncMock(spec=Chat)
    msg.chat.id = chat_id
    msg.from_user = AsyncMock(spec=User)
    msg.from_user.id = user_id
    msg.from_user.first_name = "User"
    msg.message_id = 1
    msg.answer = AsyncMock()
    msg.reply_photo = AsyncMock()
    return msg

@pytest.mark.asyncio
async def test_cmd_start():
    msg = create_message(text="/start")
    await command_start_handler(msg)
    msg.answer.assert_called_once()
    assert "Привет!" in msg.answer.call_args[0][0]

@pytest.mark.asyncio
async def test_reaction_handler_meme_action():
    # Mock reaction update
    reaction = AsyncMock()
    reaction.chat.id = 123
    reaction.message_id = 100
    reaction.new_reaction = [AsyncMock(emoji="🔥")]
    reaction.bot.send_chat_action = AsyncMock()
    reaction.bot.send_photo = AsyncMock()
    reaction.bot.send_message = AsyncMock()

    # Mock dependencies
    with patch('src.bot.handlers.history_manager') as mock_hist, \
         patch('src.bot.handlers.meme_brain') as mock_brain, \
         patch('src.bot.handlers.content_searcher') as mock_search, \
         patch('src.bot.handlers.meme_generator') as mock_gen, \
         patch('src.bot.handlers.FSInputFile') as mock_fs:

        # Setup successful chain
        mock_hist.get_context.return_value = ["User: Context"]
        mock_hist.get_message_text.return_value = "Trigger Message"

        # Mock LLM decision
        mock_brain.decide_content.return_value = {
            "action": "generate_meme",
            "search_query": "funny cat",
            "top_text": "TOP",
            "bottom_text": "BOTTOM"
        }

        mock_search.search_image.return_value = "http://img.jpg"
        mock_gen.create_meme.return_value = "out.jpg"

        await reaction_handler(reaction)

        # Verify meme generation flow
        mock_brain.decide_content.assert_called_once()
        mock_search.search_image.assert_called_with("funny cat meme template")
        mock_gen.create_meme.assert_called_once()
        reaction.bot.send_photo.assert_called_once()

@pytest.mark.asyncio
async def test_reaction_handler_gif_action():
    reaction = AsyncMock()
    reaction.chat.id = 123
    reaction.message_id = 100
    reaction.new_reaction = [AsyncMock(emoji="👍")]
    reaction.bot.send_animation = AsyncMock()

    with patch('src.bot.handlers.history_manager') as mock_hist, \
         patch('src.bot.handlers.meme_brain') as mock_brain, \
         patch('src.bot.handlers.content_searcher') as mock_search:

        mock_hist.get_context.return_value = ["User: Context"]
        mock_hist.get_message_text.return_value = "Trigger Message"

        mock_brain.decide_content.return_value = {
            "action": "search_gif",
            "search_query": "thumbs up"
        }

        mock_search.search_gif.return_value = "http://giphy.gif"

        await reaction_handler(reaction)

        mock_search.search_gif.assert_called_with("thumbs up")
        reaction.bot.send_animation.assert_called_once()

@pytest.mark.asyncio
async def test_reaction_handler_video_action():
    reaction = AsyncMock()
    reaction.chat.id = 123
    reaction.message_id = 100
    reaction.new_reaction = [AsyncMock(emoji="🤡")]
    reaction.bot.send_message = AsyncMock()

    with patch('src.bot.handlers.history_manager') as mock_hist, \
         patch('src.bot.handlers.meme_brain') as mock_brain, \
         patch('src.bot.handlers.content_searcher') as mock_search:

        mock_hist.get_context.return_value = ["User: Context"]
        mock_hist.get_message_text.return_value = "Trigger Message"

        mock_brain.decide_content.return_value = {
            "action": "search_video",
            "search_query": "clown meme"
        }

        mock_search.search_video.return_value = "https://youtube.com/..."

        await reaction_handler(reaction)

        mock_search.search_video.assert_called_with("clown meme")
        reaction.bot.send_message.assert_called()
        # send_message(chat_id, text, ...) -> call_args[0][1] is text
        assert "https://youtube.com/..." in reaction.bot.send_message.call_args[0][1]

@pytest.mark.asyncio
async def test_reaction_handler_no_history():
    reaction = AsyncMock()
    reaction.chat.id = 123
    reaction.message_id = 100
    reaction.new_reaction = [AsyncMock(emoji="🔥")]

    with patch('src.bot.handlers.history_manager') as mock_hist:
        mock_hist.get_context.return_value = [] # Empty context

        await reaction_handler(reaction)

        reaction.bot.send_message.assert_not_called()
