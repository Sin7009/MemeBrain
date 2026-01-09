from collections import deque
from typing import Deque, List, Tuple
from aiogram.types import Message
from datetime import datetime
import logging

# Размер истории берем из конфига
from .config import config
from .agent_memory import agent_memory

class HistoryManager:
    """
    Хранит ограниченное количество последних сообщений для каждого чата.
    Ключ - ID чата (int), Значение - deque сообщений.
    """
    def __init__(self, max_size: int = config.HISTORY_SIZE):
        self.max_size = max_size
        # Словарь, где ключ - chat_id, значение - Deque[Tuple[message_id, user_id, text]]
        # Храним ID сообщения и пользователя
        self.history: dict[int, Deque[Tuple[int, int, str]]] = {}
        self.memory_enabled = config.MEMORY_ENABLED
        
        # Загружаем историю из markdown файлов если включена память
        if self.memory_enabled:
            self._load_from_memory()
            logging.info("HistoryManager: Загружена история из agent_memory")

    def add_message(self, message: Message):
        """Добавляет новое сообщение в историю чата."""
        chat_id = message.chat.id
        message_id = message.message_id
        user_id = message.from_user.id if message.from_user else 0
        text = message.text

        if not text:
            # Игнорируем сообщения без текста (фото, стикеры и т.д.)
            return

        # --- ДОПОЛНЕНИЕ: Игнорируем пересланные сообщения (репосты) ---
        # Если это репост или пересланное сообщение, мы его не сохраняем в историю.
        if message.forward_from or message.forward_from_chat or message.forward_sender_name:
            return
        # --------------------------------------------------------------------

        if chat_id not in self.history:
            self.history[chat_id] = deque(maxlen=self.max_size)

        # Добавляем кортеж (ID сообщения, ID пользователя, текст)
        self.history[chat_id].append((message_id, user_id, text))
        
        # Сохраняем в markdown если включена память
        if self.memory_enabled:
            timestamp = datetime.fromtimestamp(message.date.timestamp()) if message.date else datetime.now()
            agent_memory.save_message(chat_id, message_id, user_id, text, timestamp)

    def get_message_text(self, chat_id: int, message_id: int) -> str:
        """Возвращает текст конкретного сообщения по его ID."""
        if chat_id not in self.history:
            return ""
        
        for mid, uid, text in self.history[chat_id]:
            if mid == message_id:
                return text
        return ""

    def get_context(self, chat_id: int, message_id: int) -> List[str]:
        """
        Возвращает форматированный список строк для LLM.
        Строки: "User {id}: Текст сообщения"
        """
        if chat_id not in self.history:
            return []

        formatted_history = []
        
        # Получаем все сообщения из deque
        messages_tuple = list(self.history[chat_id])

        # Форматируем для LLM
        for mid, user_id, text in messages_tuple:
            # Упрощенная маскировка ID:
            user_display = f"User {user_id}"
            formatted_history.append(f"{user_display}: {text}")
            
        return formatted_history

    def _load_from_memory(self):
        """Загружает историю сообщений из markdown файлов при инициализации."""
        try:
            chat_ids = agent_memory.list_chats()
            
            for chat_id in chat_ids:
                # Загружаем последние max_size сообщений для каждого чата
                messages = agent_memory.load_chat_history(chat_id, limit=self.max_size)
                
                if messages:
                    # Создаем deque и заполняем его
                    self.history[chat_id] = deque(messages, maxlen=self.max_size)
                    logging.info(f"HistoryManager: Загружено {len(messages)} сообщений для чата {chat_id}")
        
        except Exception as e:
            logging.error(f"HistoryManager: Ошибка при загрузке истории из памяти: {e}")
    
    def get_memory_statistics(self):
        """Возвращает статистику агентской памяти."""
        if not self.memory_enabled:
            return {"enabled": False}
        
        stats = agent_memory.get_statistics()
        stats["enabled"] = True
        return stats

# Инициализируем синглтон-менеджер для всего приложения
history_manager = HistoryManager()
