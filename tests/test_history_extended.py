import pytest
from unittest.mock import MagicMock
from src.services.history import HistoryManager
from aiogram.types import Message, Chat, User
from datetime import datetime


class TestHistoryManagerExtended:
    """Extended tests for HistoryManager edge cases"""
    
    def create_mock_message(self, chat_id, message_id, user_id, text, **kwargs):
        """Helper to create mock message with additional attributes"""
        message_data = {
            "message_id": message_id,
            "date": datetime.now(),
            "chat": Chat(id=chat_id, type="private"),
            "from_user": User(id=user_id, is_bot=False, first_name="Test"),
            "text": text,
            **kwargs
        }
        return Message(**message_data)
    
    def test_get_message_text_nonexistent_chat(self):
        """Test get_message_text for chat that doesn't exist"""
        manager = HistoryManager(max_size=5)
        text = manager.get_message_text(999, 123)
        assert text == ""
    
    def test_get_message_text_nonexistent_message(self):
        """Test get_message_text for message that doesn't exist"""
        manager = HistoryManager(max_size=5)
        msg = self.create_mock_message(123, 1, 456, "Test")
        manager.add_message(msg)
        
        text = manager.get_message_text(123, 999)
        assert text == ""
    
    def test_get_context_nonexistent_chat(self):
        """Test get_context for chat that doesn't exist"""
        manager = HistoryManager(max_size=5)
        context = manager.get_context(999, 123)
        assert context == []
    
    def test_add_message_without_text(self):
        """Test that messages without text are ignored"""
        manager = HistoryManager(max_size=5)
        msg = self.create_mock_message(123, 1, 456, None)
        manager.add_message(msg)
        
        # History should be empty
        assert 123 not in manager.history
    
    def test_add_message_with_forward_from(self):
        """Test that forwarded messages are ignored"""
        manager = HistoryManager(max_size=5)
        msg = self.create_mock_message(
            123, 1, 456, "Forwarded text",
            forward_from=User(id=999, is_bot=False, first_name="Original")
        )
        manager.add_message(msg)
        
        # Should not be added
        assert len(manager.history.get(123, [])) == 0
    
    def test_add_message_with_forward_from_chat(self):
        """Test that messages forwarded from chat are ignored"""
        manager = HistoryManager(max_size=5)
        msg = self.create_mock_message(
            123, 1, 456, "Forwarded from channel",
            forward_from_chat=Chat(id=888, type="channel")
        )
        manager.add_message(msg)
        
        # Should not be added
        assert len(manager.history.get(123, [])) == 0
    
    def test_add_message_with_forward_sender_name(self):
        """Test that messages with forward_sender_name are ignored"""
        manager = HistoryManager(max_size=5)
        msg = self.create_mock_message(
            123, 1, 456, "Forwarded anonymous",
            forward_sender_name="Anonymous"
        )
        manager.add_message(msg)
        
        # Should not be added
        assert len(manager.history.get(123, [])) == 0
    
    def test_multiple_chats_isolation(self):
        """Test that different chats maintain separate histories"""
        manager = HistoryManager(max_size=5)
        
        msg1 = self.create_mock_message(100, 1, 1, "Chat 100 msg")
        msg2 = self.create_mock_message(200, 1, 1, "Chat 200 msg")
        
        manager.add_message(msg1)
        manager.add_message(msg2)
        
        # Check isolation
        context_100 = manager.get_context(100, 1)
        context_200 = manager.get_context(200, 1)
        
        assert len(context_100) == 1
        assert len(context_200) == 1
        assert "Chat 100 msg" in context_100[0]
        assert "Chat 200 msg" in context_200[0]
    
    def test_history_order_preserved(self):
        """Test that messages are stored in order"""
        manager = HistoryManager(max_size=10)
        
        for i in range(5):
            msg = self.create_mock_message(123, i, 456, f"Message {i}")
            manager.add_message(msg)
        
        context = manager.get_context(123, 4)
        
        # Check order
        for i in range(5):
            assert f"Message {i}" in context[i]
    
    def test_context_formatting(self):
        """Test that context is properly formatted with User ID"""
        manager = HistoryManager(max_size=5)
        
        msg = self.create_mock_message(123, 1, 789, "Test message")
        manager.add_message(msg)
        
        context = manager.get_context(123, 1)
        
        assert len(context) == 1
        assert context[0] == "User 789: Test message"
    
    def test_different_users_in_same_chat(self):
        """Test multiple users in same chat are tracked correctly"""
        manager = HistoryManager(max_size=5)
        
        msg1 = self.create_mock_message(123, 1, 100, "User 100 says hi")
        msg2 = self.create_mock_message(123, 2, 200, "User 200 replies")
        msg3 = self.create_mock_message(123, 3, 100, "User 100 again")
        
        manager.add_message(msg1)
        manager.add_message(msg2)
        manager.add_message(msg3)
        
        context = manager.get_context(123, 3)
        
        assert len(context) == 3
        assert "User 100:" in context[0]
        assert "User 200:" in context[1]
        assert "User 100:" in context[2]
    
    def test_message_without_from_user(self):
        """Test handling of messages without from_user (e.g., system messages)"""
        manager = HistoryManager(max_size=5)
        
        # Create message without from_user
        msg_data = {
            "message_id": 1,
            "date": datetime.now(),
            "chat": Chat(id=123, type="private"),
            "text": "System message"
        }
        msg = Message(**msg_data)
        
        manager.add_message(msg)
        
        # Should be added with user_id 0
        context = manager.get_context(123, 1)
        assert len(context) == 1
        assert "User 0:" in context[0]
