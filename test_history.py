import unittest
from collections import deque
from src.services.history import HistoryManager, config
from aiogram.types import Message, Chat, User

class TestHistoryManager(unittest.TestCase):
    def setUp(self):
        self.manager = HistoryManager(max_size=5)
        self.chat_id = 12345
        self.user_id = 111

    def create_mock_message(self, message_id, text):
        from datetime import datetime
        return Message(
            message_id=message_id,
            date=datetime.now(), 
            chat=Chat(id=self.chat_id, type="private"),
            from_user=User(id=self.user_id, is_bot=False, first_name="Test"),
            text=text
        )

    def test_add_and_retrieve_message(self):
        msg = self.create_mock_message(101, "Hello World")
        self.manager.add_message(msg)
        
        # Check if text is retrieved correctly by ID
        text = self.manager.get_message_text(self.chat_id, 101)
        self.assertEqual(text, "Hello World")
        
        # Check if context is formatted correctly
        context = self.manager.get_context(self.chat_id, 101)
        self.assertEqual(len(context), 1)
        self.assertIn("User 111: Hello World", context[0])

    def test_message_not_found(self):
        msg = self.create_mock_message(101, "Hello")
        self.manager.add_message(msg)
        
        # Check non-existent ID
        text = self.manager.get_message_text(self.chat_id, 999)
        self.assertEqual(text, "")

    def test_history_limit(self):
        # Add 6 messages (limit is 5)
        for i in range(1, 7):
            msg = self.create_mock_message(100 + i, f"Msg {i}")
            self.manager.add_message(msg)
            
        # Check size
        self.assertEqual(len(self.manager.history[self.chat_id]), 5)
        
        # Check that the first message (101) is gone
        text_101 = self.manager.get_message_text(self.chat_id, 101)
        self.assertEqual(text_101, "")
        
        # Check that the last message (106) is present
        text_106 = self.manager.get_message_text(self.chat_id, 106)
        self.assertEqual(text_106, "Msg 6")

if __name__ == '__main__':
    unittest.main()
