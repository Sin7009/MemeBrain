import pytest
from unittest.mock import AsyncMock, patch

from src.bot.handlers import command_clear_memory_handler


@pytest.mark.asyncio
async def test_clear_memory_handler_import_and_clear_flow():
    msg = AsyncMock()
    msg.chat.id = 123
    msg.answer = AsyncMock()

    with patch("src.bot.handlers.history_manager") as mock_hist, \
         patch("src.services.agent_memory.agent_memory") as mock_agent_memory:
        mock_hist.history = {123: [(1, 1, "hello"), (2, 2, "world")]}
        mock_hist.memory_enabled = True

        await command_clear_memory_handler(msg)

        # In-memory history очищена
        assert mock_hist.history[123] == []
        # Проверяем, что дошли до импорта/вызова agent_memory.clear_chat
        mock_agent_memory.clear_chat.assert_called_once_with(123)
        msg.answer.assert_called_once()


@pytest.mark.asyncio
async def test_clear_memory_handler_when_chat_empty():
    msg = AsyncMock()
    msg.chat.id = 999
    msg.answer = AsyncMock()

    with patch("src.bot.handlers.history_manager") as mock_hist:
        mock_hist.history = {}

        await command_clear_memory_handler(msg)

        msg.answer.assert_called_once()
        text = msg.answer.call_args[0][0]
        assert "История пуста" in text
