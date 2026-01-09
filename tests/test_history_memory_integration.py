import unittest
import tempfile
import shutil
import os
from unittest.mock import Mock
from datetime import datetime

# Set dummy env vars before importing src modules
os.environ["TELEGRAM_BOT_TOKEN"] = "dummy_token"
os.environ["TAVILY_API_KEY"] = "dummy_key"
os.environ["OPENROUTER_API_KEY"] = "dummy_openrouter"

# Set temp directory for tests BEFORE importing
test_memory_dir = tempfile.mkdtemp(prefix="test_memory_")
os.environ["MEMORY_DIR"] = test_memory_dir
os.environ["MEMORY_ENABLED"] = "True"

from src.services.agent_memory import AgentMemory
from src.services.history import HistoryManager
from aiogram.types import Message, User, Chat


class TestHistoryWithMemory(unittest.TestCase):
    """Тесты интеграции HistoryManager с AgentMemory"""
    
    @classmethod
    def setUpClass(cls):
        """Один раз создаем менеджеры для всех тестов"""
        # Recreate agent_memory with test directory
        cls.agent_memory = AgentMemory(memory_dir=test_memory_dir)
        cls.history_manager = HistoryManager()
        cls.history_manager.memory_enabled = True
    
    def setUp(self):
        """Очищаем историю перед каждым тестом"""
        self.history_manager.history.clear()
    
    @classmethod
    def tearDownClass(cls):
        """Удаляем тестовую директорию"""
        if os.path.exists(test_memory_dir):
            shutil.rmtree(test_memory_dir, ignore_errors=True)
    
    def _create_mock_message(self, chat_id: int, message_id: int, user_id: int, text: str) -> Message:
        """Создает mock объект Message для тестов"""
        message = Mock(spec=Message)
        message.chat = Mock(spec=Chat)
        message.chat.id = chat_id
        message.message_id = message_id
        message.from_user = Mock(spec=User)
        message.from_user.id = user_id
        message.text = text
        message.date = datetime.now()
        message.forward_from = None
        message.forward_from_chat = None
        message.forward_sender_name = None
        return message
    
    def test_add_message_in_memory_history(self):
        """Тест базового добавления сообщения"""
        chat_id = 99999  # Используем уникальный ID для этого теста
        message = self._create_mock_message(chat_id, 1, 111, "Тестовое сообщение")
        
        # Добавляем через history manager
        self.history_manager.add_message(message)
        
        # Проверяем, что сообщение в in-memory хранилище
        context = self.history_manager.get_context(chat_id, 1)
        self.assertEqual(len(context), 1)
        self.assertIn("User 111: Тестовое сообщение", context[0])
    
    def test_multiple_messages_order(self):
        """Тест порядка нескольких сообщений"""
        chat_id = 99998  # Уникальный ID
        
        messages = [
            self._create_mock_message(chat_id, 1, 111, "Первое"),
            self._create_mock_message(chat_id, 2, 222, "Второе"),
            self._create_mock_message(chat_id, 3, 333, "Третье"),
        ]
        
        for msg in messages:
            self.history_manager.add_message(msg)
        
        # Проверяем порядок в контексте
        context = self.history_manager.get_context(chat_id, 3)
        self.assertEqual(len(context), 3)
        self.assertIn("Первое", context[0])
        self.assertIn("Второе", context[1])
        self.assertIn("Третье", context[2])
    
    def test_memory_statistics(self):
        """Тест получения статистики памяти"""
        stats = self.history_manager.get_memory_statistics()
        
        self.assertTrue(stats['enabled'])
        self.assertIn('total_chats', stats)
        self.assertIn('total_messages', stats)
        self.assertGreaterEqual(stats['total_chats'], 0)
    
    def test_empty_text_ignored(self):
        """Тест игнорирования пустых сообщений"""
        chat_id = 99997
        message = self._create_mock_message(chat_id, 1, 111, "")
        
        # Пустое сообщение не должно сохраняться
        self.history_manager.add_message(message)
        
        context = self.history_manager.get_context(chat_id, 1)
        self.assertEqual(len(context), 0)


class TestHistoryWithMemoryDisabled(unittest.TestCase):
    """Тесты HistoryManager с отключенной памятью"""
    
    def setUp(self):
        """Создаем HistoryManager с отключенной памятью"""
        # Временно отключаем память для этих тестов
        os.environ["MEMORY_ENABLED"] = "False"
        
        # Создаем новый менеджер
        self.history_manager = HistoryManager()
        self.history_manager.memory_enabled = False
    
    def tearDown(self):
        """Восстанавливаем настройки"""
        os.environ["MEMORY_ENABLED"] = "True"
    
    def _create_mock_message(self, chat_id: int, message_id: int, user_id: int, text: str) -> Message:
        """Создает mock объект Message для тестов"""
        message = Mock(spec=Message)
        message.chat = Mock(spec=Chat)
        message.chat.id = chat_id
        message.message_id = message_id
        message.from_user = Mock(spec=User)
        message.from_user.id = user_id
        message.text = text
        message.date = datetime.now()
        message.forward_from = None
        message.forward_from_chat = None
        message.forward_sender_name = None
        return message
    
    def test_memory_disabled(self):
        """Тест работы без памяти"""
        chat_id = 88888
        message = self._create_mock_message(chat_id, 1, 111, "Тест")
        
        self.history_manager.add_message(message)
        
        # Проверяем, что сообщение в in-memory хранилище
        context = self.history_manager.get_context(chat_id, 1)
        self.assertEqual(len(context), 1)
        
        # Проверяем статистику
        stats = self.history_manager.get_memory_statistics()
        self.assertFalse(stats['enabled'])


if __name__ == '__main__':
    unittest.main()
