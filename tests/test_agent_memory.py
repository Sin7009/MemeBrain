import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from src.services.agent_memory import AgentMemory


class TestAgentMemory(unittest.TestCase):
    """Тесты для агентской памяти (markdown storage)"""
    
    def setUp(self):
        """Создаем временную директорию для тестов"""
        self.temp_dir = tempfile.mkdtemp()
        self.agent_memory = AgentMemory(memory_dir=self.temp_dir)
    
    def tearDown(self):
        """Удаляем временную директорию после тестов"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_save_message(self):
        """Тест сохранения сообщения"""
        chat_id = 12345
        message_id = 1
        user_id = 67890
        text = "Привет, мир!"
        
        self.agent_memory.save_message(chat_id, message_id, user_id, text)
        
        # Проверяем, что файл создан
        file_path = self.agent_memory._get_chat_file_path(chat_id)
        self.assertTrue(file_path.exists())
        
        # Проверяем содержимое
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn(f"# История чата {chat_id}", content)
            self.assertIn(f"### Сообщение #{message_id}", content)
            self.assertIn(f"User {user_id}", content)
            self.assertIn(text, content)
    
    def test_save_multiple_messages(self):
        """Тест сохранения нескольких сообщений"""
        chat_id = 12345
        messages = [
            (1, 111, "Первое сообщение"),
            (2, 222, "Второе сообщение"),
            (3, 111, "Третье сообщение"),
        ]
        
        for msg_id, user_id, text in messages:
            self.agent_memory.save_message(chat_id, msg_id, user_id, text)
        
        # Загружаем и проверяем
        loaded = self.agent_memory.load_chat_history(chat_id)
        self.assertEqual(len(loaded), 3)
        
        # Проверяем порядок и содержимое
        for i, (msg_id, user_id, text) in enumerate(messages):
            self.assertEqual(loaded[i][0], msg_id)
            self.assertEqual(loaded[i][1], user_id)
            self.assertEqual(loaded[i][2], text)
    
    def test_load_chat_history(self):
        """Тест загрузки истории чата"""
        chat_id = 12345
        
        # Сохраняем сообщения
        self.agent_memory.save_message(chat_id, 1, 111, "Сообщение 1")
        self.agent_memory.save_message(chat_id, 2, 222, "Сообщение 2")
        self.agent_memory.save_message(chat_id, 3, 333, "Сообщение 3")
        
        # Загружаем все
        history = self.agent_memory.load_chat_history(chat_id)
        self.assertEqual(len(history), 3)
        
        # Загружаем с лимитом
        history_limited = self.agent_memory.load_chat_history(chat_id, limit=2)
        self.assertEqual(len(history_limited), 2)
        # Должны быть последние 2 сообщения
        self.assertEqual(history_limited[0][0], 2)
        self.assertEqual(history_limited[1][0], 3)
    
    def test_load_nonexistent_chat(self):
        """Тест загрузки несуществующего чата"""
        history = self.agent_memory.load_chat_history(99999)
        self.assertEqual(len(history), 0)
    
    def test_metadata(self):
        """Тест работы с метаданными"""
        chat_id = 12345
        
        # Сохраняем сообщения
        self.agent_memory.save_message(chat_id, 1, 111, "Первое")
        self.agent_memory.save_message(chat_id, 2, 222, "Второе")
        
        # Получаем метаданные
        metadata = self.agent_memory.get_metadata(chat_id)
        
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata['chat_id'], chat_id)
        self.assertEqual(metadata['message_count'], 2)
        self.assertEqual(metadata['last_message_id'], 2)
        self.assertIn('created_at', metadata)
        self.assertIn('last_update', metadata)
    
    def test_list_chats(self):
        """Тест получения списка чатов"""
        # Создаем несколько чатов
        chat_ids = [111, 222, 333]
        
        for chat_id in chat_ids:
            self.agent_memory.save_message(chat_id, 1, 999, "Тестовое сообщение")
        
        # Получаем список
        listed_chats = self.agent_memory.list_chats()
        
        self.assertEqual(len(listed_chats), 3)
        self.assertEqual(sorted(listed_chats), sorted(chat_ids))
    
    def test_clear_chat(self):
        """Тест очистки истории чата"""
        chat_id = 12345
        
        # Сохраняем сообщения
        self.agent_memory.save_message(chat_id, 1, 111, "Сообщение")
        
        # Проверяем, что файлы существуют
        file_path = self.agent_memory._get_chat_file_path(chat_id)
        meta_path = self.agent_memory._get_metadata_file_path(chat_id)
        self.assertTrue(file_path.exists())
        self.assertTrue(meta_path.exists())
        
        # Очищаем
        self.agent_memory.clear_chat(chat_id)
        
        # Проверяем, что файлы удалены
        self.assertFalse(file_path.exists())
        self.assertFalse(meta_path.exists())
    
    def test_statistics(self):
        """Тест получения статистики"""
        # Создаем несколько чатов с разным количеством сообщений
        self.agent_memory.save_message(111, 1, 999, "Сообщение 1")
        self.agent_memory.save_message(111, 2, 999, "Сообщение 2")
        self.agent_memory.save_message(222, 1, 999, "Сообщение 1")
        self.agent_memory.save_message(333, 1, 999, "Сообщение 1")
        self.agent_memory.save_message(333, 2, 999, "Сообщение 2")
        self.agent_memory.save_message(333, 3, 999, "Сообщение 3")
        
        # Получаем статистику
        stats = self.agent_memory.get_statistics()
        
        self.assertEqual(stats['total_chats'], 3)
        self.assertEqual(stats['total_messages'], 6)  # 2 + 1 + 3
        self.assertEqual(len(stats['chat_ids']), 3)
    
    def test_special_characters(self):
        """Тест работы со специальными символами"""
        chat_id = 12345
        special_text = "Текст с `обратными кавычками` и **жирным**"
        
        self.agent_memory.save_message(chat_id, 1, 111, special_text)
        
        # Загружаем и проверяем
        history = self.agent_memory.load_chat_history(chat_id)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0][2], special_text)
    
    def test_multiline_text(self):
        """Тест работы с многострочным текстом"""
        chat_id = 12345
        multiline_text = """Первая строка
Вторая строка
Третья строка"""
        
        self.agent_memory.save_message(chat_id, 1, 111, multiline_text)
        
        # Загружаем и проверяем
        history = self.agent_memory.load_chat_history(chat_id)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0][2], multiline_text)
    
    def test_empty_text(self):
        """Тест работы с пустым текстом"""
        chat_id = 12345
        
        self.agent_memory.save_message(chat_id, 1, 111, "")
        
        # Загружаем и проверяем
        history = self.agent_memory.load_chat_history(chat_id)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0][2], "")
    
    def test_long_text(self):
        """Тест работы с длинным текстом"""
        chat_id = 12345
        long_text = "А" * 10000  # 10000 символов
        
        self.agent_memory.save_message(chat_id, 1, 111, long_text)
        
        # Загружаем и проверяем
        history = self.agent_memory.load_chat_history(chat_id)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0][2], long_text)
    
    def test_timestamp_preservation(self):
        """Тест сохранения временных меток"""
        chat_id = 12345
        timestamp = datetime(2026, 1, 9, 15, 30, 0)
        
        self.agent_memory.save_message(chat_id, 1, 111, "Тест", timestamp)
        
        # Проверяем, что временная метка записана в файл
        file_path = self.agent_memory._get_chat_file_path(chat_id)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("2026-01-09 15:30:00", content)


if __name__ == '__main__':
    unittest.main()
