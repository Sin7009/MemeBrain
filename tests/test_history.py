import unittest
import os
from unittest.mock import patch, MagicMock
# Set env vars before importing
os.environ["TELEGRAM_BOT_TOKEN"] = "dummy_token"
os.environ["TAVILY_API_KEY"] = "dummy_key"
os.environ["OPENROUTER_API_KEY"] = "dummy_openrouter"
os.environ["MEMORY_ENABLED"] = "False"  # Disable memory for these tests

from src.services.history import HistoryManager
from aiogram.types import Message, Chat, User
from datetime import datetime

class TestHistoryManager(unittest.TestCase):
    def setUp(self):
        self.manager = HistoryManager(max_size=5)
        self.chat_id = 12345
        self.user_id = 111

    def create_mock_message(self, message_id, text, is_forwarded=False):
        message_data = {
            "message_id": message_id,
            "date": datetime.now(),
            "chat": Chat(id=self.chat_id, type="private"),
            "from_user": User(id=self.user_id, is_bot=False, first_name="Test"),
            "text": text
        }
        if is_forwarded:
            message_data['forward_from'] = User(id=999, is_bot=False, first_name="ForwardedUser")
        return Message(**message_data)

    def test_add_and_retrieve_message(self):
        msg = self.create_mock_message(101, "Hello World")
        self.manager.add_message(msg)
        text = self.manager.get_message_text(self.chat_id, 101)
        self.assertEqual(text, "Hello World")

    def test_get_context(self):
        msg = self.create_mock_message(101, "Hello World")
        self.manager.add_message(msg)
        context = self.manager.get_context(self.chat_id, 101)
        self.assertEqual(len(context), 1)
        self.assertIn("User 111: Hello World", context[0])

    def test_ignore_forwarded_messages(self):
        reg_msg = self.create_mock_message(201, "Regular message")
        self.manager.add_message(reg_msg)
        fwd_msg = self.create_mock_message(202, "Forwarded", is_forwarded=True)
        self.manager.add_message(fwd_msg)
        self.assertEqual(len(self.manager.history.get(self.chat_id, [])), 1)

    def test_history_limit(self):
        for i in range(1, 7):
            msg = self.create_mock_message(100 + i, f"Msg {i}")
            self.manager.add_message(msg)
        self.assertEqual(len(self.manager.history[self.chat_id]), 5)
        self.assertEqual(self.manager.get_message_text(self.chat_id, 101), "")
        self.assertEqual(self.manager.get_message_text(self.chat_id, 106), "Msg 6")
