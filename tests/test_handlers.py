import pytest
from unittest.mock import patch, AsyncMock
from src.bot.handlers import command_start_handler, reaction_handler, command_joke_handler, joke_feedback_handler
from aiogram.types import Message, Chat, User

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
async def test_reaction_handler_success():
    # Mock reaction update
    reaction = AsyncMock() # Removed spec to avoid attribute errors
    reaction.chat.id = 123
    reaction.message_id = 100
    reaction.new_reaction = [AsyncMock(emoji="🔥")]
    reaction.bot.send_chat_action = AsyncMock()
    reaction.bot.send_photo = AsyncMock()
    reaction.bot.send_message = AsyncMock()

    # Mock dependencies
    with patch('src.bot.handlers.history_manager') as mock_hist, \
         patch('src.bot.handlers.meme_brain') as mock_brain, \
         patch('src.bot.handlers.image_searcher') as mock_search, \
         patch('src.bot.handlers.meme_generator') as mock_gen, \
         patch('src.bot.handlers.FSInputFile'):

        # Setup successful chain
        mock_hist.get_context.return_value = ["User: Context"]
        mock_hist.get_message_text.return_value = "Trigger Message"
        mock_brain.generate_meme_idea.return_value = {
            "top_text": "T", "bottom_text": "B", "search_query": "Q", "is_memable": True
        }
        mock_search.search_template.return_value = "http://img.jpg"
        mock_gen.create_meme.return_value = "out.jpg"

        await reaction_handler(reaction)

        reaction.bot.send_photo.assert_called_once()

@pytest.mark.asyncio
async def test_reaction_handler_no_history():
    reaction = AsyncMock()
    reaction.chat.id = 123
    reaction.message_id = 100
    reaction.new_reaction = [AsyncMock(emoji="🔥")]

    with patch('src.bot.handlers.history_manager') as mock_hist:
        mock_hist.get_context.return_value = [] # Empty context

        await reaction_handler(reaction)

        # Should just return without sending anything
        reaction.bot.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_command_joke_success_with_feedback_buttons():
    msg = create_message(text="/joke")
    sent = AsyncMock()
    sent.message_id = 777
    msg.answer = AsyncMock(return_value=sent)

    with patch('src.bot.handlers.joke_service') as mock_joke_service:
        from src.services.jokes import JokeItem
        mock_joke_service.get_joke.return_value = JokeItem(title="Анекдот", text="Текст")

        await command_joke_handler(msg)

        msg.answer.assert_called_once()
        kwargs = msg.answer.call_args.kwargs
        assert kwargs.get('reply_markup') is not None
        mock_joke_service.bind_sent_message.assert_called_once_with(777, mock_joke_service.get_joke.return_value)


@pytest.mark.asyncio
async def test_joke_feedback_downvote_updates_model():
    callback = AsyncMock()
    callback.data = "joke_feedback:down"
    callback.message = AsyncMock()
    callback.message.message_id = 1234
    callback.answer = AsyncMock()

    with patch('src.bot.handlers.joke_service') as mock_joke_service:
        mock_joke_service.vote.return_value = True

        await joke_feedback_handler(callback)

        mock_joke_service.vote.assert_called_once_with(1234, False)
        callback.answer.assert_called_once()
