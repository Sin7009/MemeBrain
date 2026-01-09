import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging

class AgentMemory:
    """
    Класс для хранения агентской памяти в markdown файлах.
    Сохраняет историю сообщений чатов в структурированном формате.
    """
    
    def __init__(self, memory_dir: str = "memory"):
        """
        Инициализирует систему агентской памяти.
        
        Args:
            memory_dir: Директория для хранения markdown файлов
        """
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(exist_ok=True)
        logging.info(f"AgentMemory: Инициализирована с директорией {self.memory_dir}")
    
    def _get_chat_file_path(self, chat_id: int) -> Path:
        """Возвращает путь к markdown файлу для конкретного чата."""
        return self.memory_dir / f"chat_{chat_id}.md"
    
    def _get_metadata_file_path(self, chat_id: int) -> Path:
        """Возвращает путь к JSON файлу с метаданными чата."""
        return self.memory_dir / f"chat_{chat_id}_meta.json"
    
    def save_message(self, chat_id: int, message_id: int, user_id: int, text: str, timestamp: Optional[datetime] = None):
        """
        Сохраняет сообщение в markdown файл чата.
        
        Args:
            chat_id: ID чата
            message_id: ID сообщения
            user_id: ID пользователя
            text: Текст сообщения
            timestamp: Временная метка (если None, используется текущее время)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        file_path = self._get_chat_file_path(chat_id)
        
        # Создаем файл если его нет
        if not file_path.exists():
            self._create_chat_file(chat_id)
        
        # Форматируем сообщение в markdown
        formatted_message = self._format_message(message_id, user_id, text, timestamp)
        
        # Добавляем сообщение в файл
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(formatted_message + "\n\n")
        
        # Обновляем метаданные
        self._update_metadata(chat_id, message_id, timestamp)
    
    def _create_chat_file(self, chat_id: int):
        """Создает новый markdown файл для чата с заголовком."""
        file_path = self._get_chat_file_path(chat_id)
        
        header = f"""# История чата {chat_id}

> Автоматически сгенерированная история сообщений
> Создано: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(header)
        
        logging.info(f"AgentMemory: Создан новый файл для чата {chat_id}")
    
    def _format_message(self, message_id: int, user_id: int, text: str, timestamp: datetime) -> str:
        """
        Форматирует сообщение в markdown.
        
        Returns:
            Строка в формате markdown с сообщением
        """
        time_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        # Экранируем специальные символы markdown
        text_escaped = text.replace('`', '\\`')
        
        formatted = f"""### Сообщение #{message_id}
**Пользователь:** User {user_id}  
**Время:** {time_str}

```
{text_escaped}
```"""
        
        return formatted
    
    def _update_metadata(self, chat_id: int, message_id: int, timestamp: datetime):
        """Обновляет метаданные чата."""
        meta_path = self._get_metadata_file_path(chat_id)
        
        # Загружаем существующие метаданные или создаем новые
        if meta_path.exists():
            with open(meta_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        else:
            metadata = {
                "chat_id": chat_id,
                "created_at": datetime.now().isoformat(),
                "message_count": 0,
                "last_message_id": 0,
                "last_update": None
            }
        
        # Обновляем метаданные
        metadata["message_count"] += 1
        metadata["last_message_id"] = message_id
        metadata["last_update"] = timestamp.isoformat()
        
        # Сохраняем метаданные
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    def load_chat_history(self, chat_id: int, limit: Optional[int] = None) -> List[Tuple[int, int, str]]:
        """
        Загружает историю сообщений из markdown файла.
        
        Args:
            chat_id: ID чата
            limit: Максимальное количество сообщений (последние N)
        
        Returns:
            Список кортежей (message_id, user_id, text)
        """
        file_path = self._get_chat_file_path(chat_id)
        
        if not file_path.exists():
            return []
        
        messages = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Парсим markdown файл
            # Разбиваем по заголовкам сообщений
            message_blocks = content.split('### Сообщение #')[1:]  # Пропускаем заголовок файла
            
            for block in message_blocks:
                try:
                    lines = block.strip().split('\n')
                    
                    # Извлекаем message_id из первой строки
                    message_id = int(lines[0].strip())
                    
                    # Извлекаем user_id
                    user_line = [l for l in lines if l.startswith('**Пользователь:**')][0]
                    user_id = int(user_line.split('User ')[1].strip())
                    
                    # Извлекаем текст сообщения (между тройными обратными кавычками)
                    text_start = None
                    text_end = None
                    
                    for i, line in enumerate(lines):
                        if line.strip() == '```' and text_start is None:
                            text_start = i + 1
                        elif line.strip() == '```' and text_start is not None:
                            text_end = i
                            break
                    
                    if text_start is not None and text_end is not None:
                        text = '\n'.join(lines[text_start:text_end])
                        # Убираем экранирование
                        text = text.replace('\\`', '`')
                        messages.append((message_id, user_id, text))
                
                except (IndexError, ValueError) as e:
                    logging.warning(f"AgentMemory: Не удалось распарсить блок сообщения: {e}")
                    continue
        
        except Exception as e:
            logging.error(f"AgentMemory: Ошибка при загрузке истории чата {chat_id}: {e}")
            return []
        
        # Применяем лимит если указан
        if limit and len(messages) > limit:
            messages = messages[-limit:]
        
        return messages
    
    def get_metadata(self, chat_id: int) -> Optional[Dict]:
        """Возвращает метаданные чата."""
        meta_path = self._get_metadata_file_path(chat_id)
        
        if not meta_path.exists():
            return None
        
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"AgentMemory: Ошибка при загрузке метаданных чата {chat_id}: {e}")
            return None
    
    def list_chats(self) -> List[int]:
        """Возвращает список ID всех чатов в памяти."""
        chat_ids = []
        
        for file_path in self.memory_dir.glob("chat_*_meta.json"):
            try:
                # Извлекаем chat_id из имени файла
                filename = file_path.stem  # chat_123_meta
                chat_id = int(filename.split('_')[1])
                chat_ids.append(chat_id)
            except (IndexError, ValueError):
                continue
        
        return sorted(chat_ids)
    
    def clear_chat(self, chat_id: int):
        """Очищает историю конкретного чата."""
        file_path = self._get_chat_file_path(chat_id)
        meta_path = self._get_metadata_file_path(chat_id)
        
        if file_path.exists():
            file_path.unlink()
            logging.info(f"AgentMemory: Удален файл истории чата {chat_id}")
        
        if meta_path.exists():
            meta_path.unlink()
            logging.info(f"AgentMemory: Удалены метаданные чата {chat_id}")
    
    def get_statistics(self) -> Dict:
        """Возвращает статистику по всей памяти."""
        chats = self.list_chats()
        total_messages = 0
        
        for chat_id in chats:
            metadata = self.get_metadata(chat_id)
            if metadata:
                total_messages += metadata.get('message_count', 0)
        
        return {
            "total_chats": len(chats),
            "total_messages": total_messages,
            "chat_ids": chats
        }


# Инициализируем синглтон для использования в приложении
agent_memory = AgentMemory()
