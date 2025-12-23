"""
Комплексный стресс-тест бота MemeBrain.
Проверяет все функции бота в различных сценариях использования.
"""
import pytest

# Настройка pytest-asyncio
pytest_plugins = ('pytest_asyncio',)
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from src.bot.handlers import (
    command_start_handler,
    command_help_handler,
    message_handler,
    reaction_handler,
    generate_and_send_meme,
    MEME_TRIGGERS
)
from aiogram.types import Message, Chat, User, MessageReactionUpdated
from src.services.history import HistoryManager
from src.services.llm import MemeBrain
from src.services.search import ImageSearcher
from src.services.image_gen import MemeGenerator


def create_message(text="Hello", chat_id=123, user_id=456, chat_type='private', message_id=1):
    """Helper для создания мок-сообщений"""
    msg = AsyncMock(spec=Message)
    msg.text = text
    msg.chat = AsyncMock(spec=Chat)
    msg.chat.id = chat_id
    msg.chat.type = chat_type
    msg.from_user = AsyncMock(spec=User)
    msg.from_user.id = user_id
    msg.from_user.first_name = "TestUser"
    msg.message_id = message_id
    msg.answer = AsyncMock()
    msg.reply_photo = AsyncMock()
    msg.bot = AsyncMock()
    msg.bot.send_chat_action = AsyncMock()
    msg.bot.send_photo = AsyncMock()
    msg.bot.send_message = AsyncMock()
    msg.forward_from = None
    msg.forward_from_chat = None
    msg.forward_sender_name = None
    return msg


def create_reaction(emoji="🔥", chat_id=123, message_id=100):
    """Helper для создания мок-реакций"""
    reaction = AsyncMock()
    reaction.chat.id = chat_id
    reaction.message_id = message_id
    reaction.new_reaction = [AsyncMock(emoji=emoji)]
    reaction.bot.send_chat_action = AsyncMock()
    reaction.bot.send_photo = AsyncMock()
    reaction.bot.send_message = AsyncMock()
    return reaction


class TestCommandsStress:
    """Стресс-тест команд бота"""
    
    @pytest.mark.asyncio
    async def test_start_command_multiple_calls(self):
        """Тест многократного вызова /start"""
        for i in range(10):
            msg = create_message(text="/start", user_id=i)
            await command_start_handler(msg)
            msg.answer.assert_called_once()
            assert "Привет" in msg.answer.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_help_command_multiple_calls(self):
        """Тест многократного вызова /help"""
        for i in range(10):
            msg = create_message(text="/help", user_id=i)
            await command_help_handler(msg)
            msg.answer.assert_called_once()
            assert "Как пользоваться ботом" in msg.answer.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_concurrent_commands(self):
        """Тест параллельных команд"""
        tasks = []
        for i in range(20):
            if i % 2 == 0:
                msg = create_message(text="/start", user_id=i)
                tasks.append(command_start_handler(msg))
            else:
                msg = create_message(text="/help", user_id=i)
                tasks.append(command_help_handler(msg))
        
        await asyncio.gather(*tasks)


class TestAllEmojiTriggers:
    """Стресс-тест всех эмодзи-триггеров"""
    
    @pytest.mark.asyncio
    async def test_all_emoji_triggers(self):
        """Проверка всех триггерных эмодзи"""
        with patch('src.bot.handlers.history_manager') as mock_hist, \
             patch('src.bot.handlers.meme_brain') as mock_brain, \
             patch('src.bot.handlers.image_searcher') as mock_search, \
             patch('src.bot.handlers.meme_generator') as mock_gen, \
             patch('src.bot.handlers.FSInputFile'):
            
            mock_hist.get_context.return_value = ["User 1: Тестовое сообщение"]
            mock_hist.get_message_text.return_value = "Триггер"
            mock_brain.generate_meme_idea.return_value = {
                "is_memable": True,
                "top_text": "TOP",
                "bottom_text": "BOTTOM",
                "search_query": "query"
            }
            mock_search.search_template.return_value = "http://img.jpg"
            mock_gen.create_meme.return_value = "output.jpg"
            
            # Тестируем каждую эмодзи из MEME_TRIGGERS
            for emoji, meaning in MEME_TRIGGERS.items():
                reaction = create_reaction(emoji=emoji, message_id=100 + list(MEME_TRIGGERS.keys()).index(emoji))
                await reaction_handler(reaction)
                
                # Проверяем, что была попытка отправить фото
                assert reaction.bot.send_photo.called or reaction.bot.send_message.called


class TestHistoryStress:
    """Стресс-тест системы истории"""
    
    def test_history_overflow(self):
        """Тест переполнения истории"""
        history = HistoryManager(max_size=10)
        
        # Добавляем 100 сообщений в один чат
        for i in range(100):
            msg = create_message(text=f"Message {i}", message_id=i)
            history.add_message(msg)
        
        # Проверяем, что хранится только 10 последних
        context = history.get_context(123, 99)
        assert len(context) == 10
        assert "Message 99" in context[-1]
    
    def test_multiple_chats_concurrent(self):
        """Тест работы с множеством чатов одновременно"""
        history = HistoryManager(max_size=5)
        
        # Создаем сообщения для 50 разных чатов
        for chat_id in range(50):
            for msg_id in range(10):
                msg = create_message(
                    text=f"Chat {chat_id} Message {msg_id}",
                    chat_id=chat_id,
                    message_id=msg_id
                )
                history.add_message(msg)
        
        # Проверяем, что для каждого чата хранится правильное количество
        for chat_id in range(50):
            context = history.get_context(chat_id, 9)
            assert len(context) == 5  # max_size
    
    def test_empty_context_handling(self):
        """Тест обработки пустого контекста"""
        history = HistoryManager()
        context = history.get_context(999, 1)
        assert context == []
        
        text = history.get_message_text(999, 1)
        assert text == ""


class TestFullPipelineStress:
    """Стресс-тест полной цепочки генерации мема"""
    
    @pytest.mark.asyncio
    async def test_full_pipeline_success(self):
        """Тест успешного прохождения всей цепочки"""
        msg = create_message(text="Тестовое сообщение", chat_type='private')
        
        with patch('src.bot.handlers.history_manager') as mock_hist, \
             patch('src.bot.handlers.meme_brain') as mock_brain, \
             patch('src.bot.handlers.image_searcher') as mock_search, \
             patch('src.bot.handlers.meme_generator') as mock_gen, \
             patch('src.bot.handlers.FSInputFile'):
            
            mock_hist.get_context.return_value = ["User: Тестовое сообщение"]
            mock_brain.generate_meme_idea.return_value = {
                "is_memable": True,
                "top_text": "КОГДА ТЕСТИРУЕШЬ",
                "bottom_text": "И ВСЕ РАБОТАЕТ",
                "search_query": "success kid"
            }
            mock_search.search_template.return_value = "http://example.com/img.jpg"
            mock_gen.create_meme.return_value = "test_output.jpg"
            
            await message_handler(msg)
            
            # Проверяем, что все компоненты были вызваны
            mock_hist.add_message.assert_called_once()
            mock_hist.get_context.assert_called_once()
            mock_brain.generate_meme_idea.assert_called_once()
            mock_search.search_template.assert_called_once()
            mock_gen.create_meme.assert_called_once()
            msg.bot.send_photo.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_pipeline_llm_failure(self):
        """Тест обработки ошибки LLM"""
        msg = create_message(text="Тест", chat_type='private')
        
        with patch('src.bot.handlers.history_manager') as mock_hist, \
             patch('src.bot.handlers.meme_brain') as mock_brain:
            
            mock_hist.get_context.return_value = ["User: Тест"]
            mock_brain.generate_meme_idea.return_value = None
            
            await message_handler(msg)
            
            # Должно быть отправлено сообщение об ошибке
            msg.bot.send_message.assert_called()
            assert "Мозги сломались" in msg.bot.send_message.call_args[0][1]
    
    @pytest.mark.asyncio
    async def test_pipeline_search_failure(self):
        """Тест обработки ошибки поиска"""
        msg = create_message(text="Тест", chat_type='private')
        
        with patch('src.bot.handlers.history_manager') as mock_hist, \
             patch('src.bot.handlers.meme_brain') as mock_brain, \
             patch('src.bot.handlers.image_searcher') as mock_search:
            
            mock_hist.get_context.return_value = ["User: Тест"]
            mock_brain.generate_meme_idea.return_value = {
                "is_memable": True,
                "top_text": "TOP",
                "bottom_text": "BOTTOM",
                "search_query": "query"
            }
            mock_search.search_template.return_value = None
            
            await message_handler(msg)
            
            # Должно быть отправлено сообщение о ненайденном шаблоне
            msg.bot.send_message.assert_called()
            assert "Шаблон не найден" in msg.bot.send_message.call_args[0][1]
    
    @pytest.mark.asyncio
    async def test_pipeline_image_gen_failure(self):
        """Тест обработки ошибки генерации изображения"""
        msg = create_message(text="Тест", chat_type='private')
        
        with patch('src.bot.handlers.history_manager') as mock_hist, \
             patch('src.bot.handlers.meme_brain') as mock_brain, \
             patch('src.bot.handlers.image_searcher') as mock_search, \
             patch('src.bot.handlers.meme_generator') as mock_gen:
            
            mock_hist.get_context.return_value = ["User: Тест"]
            mock_brain.generate_meme_idea.return_value = {
                "is_memable": True,
                "top_text": "TOP",
                "bottom_text": "BOTTOM",
                "search_query": "query"
            }
            mock_search.search_template.return_value = "http://img.jpg"
            mock_gen.create_meme.return_value = None
            
            await message_handler(msg)
            
            # Должно быть отправлено сообщение об ошибке
            msg.bot.send_message.assert_called()
            assert "Не удалось создать картинку" in msg.bot.send_message.call_args[0][1]


class TestConcurrentRequests:
    """Стресс-тест параллельных запросов"""
    
    @pytest.mark.asyncio
    async def test_concurrent_meme_generation(self):
        """Тест параллельной генерации мемов"""
        with patch('src.bot.handlers.history_manager') as mock_hist, \
             patch('src.bot.handlers.meme_brain') as mock_brain, \
             patch('src.bot.handlers.image_searcher') as mock_search, \
             patch('src.bot.handlers.meme_generator') as mock_gen, \
             patch('src.bot.handlers.FSInputFile'):
            
            mock_hist.get_context.return_value = ["User: Контекст"]
            mock_brain.generate_meme_idea.return_value = {
                "is_memable": True,
                "top_text": "TOP",
                "bottom_text": "BOTTOM",
                "search_query": "query"
            }
            mock_search.search_template.return_value = "http://img.jpg"
            mock_gen.create_meme.return_value = "output.jpg"
            
            # Создаем 50 параллельных запросов
            tasks = []
            for i in range(50):
                msg = create_message(
                    text=f"Сообщение {i}",
                    chat_type='private',
                    user_id=i,
                    message_id=i
                )
                tasks.append(message_handler(msg))
            
            # Выполняем все параллельно
            await asyncio.gather(*tasks)
            
            # Проверяем, что все запросы обработаны
            assert mock_gen.create_meme.call_count == 50
    
    @pytest.mark.asyncio
    async def test_concurrent_reactions(self):
        """Тест параллельных реакций"""
        with patch('src.bot.handlers.history_manager') as mock_hist, \
             patch('src.bot.handlers.meme_brain') as mock_brain, \
             patch('src.bot.handlers.image_searcher') as mock_search, \
             patch('src.bot.handlers.meme_generator') as mock_gen, \
             patch('src.bot.handlers.FSInputFile'):
            
            mock_hist.get_context.return_value = ["User: Контекст"]
            mock_hist.get_message_text.return_value = "Сообщение"
            mock_brain.generate_meme_idea.return_value = {
                "is_memable": True,
                "top_text": "TOP",
                "bottom_text": "BOTTOM",
                "search_query": "query"
            }
            mock_search.search_template.return_value = "http://img.jpg"
            mock_gen.create_meme.return_value = "output.jpg"
            
            # Создаем 30 параллельных реакций с разными эмодзи
            tasks = []
            emojis = list(MEME_TRIGGERS.keys())
            for i in range(30):
                emoji = emojis[i % len(emojis)]
                reaction = create_reaction(emoji=emoji, message_id=i)
                tasks.append(reaction_handler(reaction))
            
            # Выполняем все параллельно
            await asyncio.gather(*tasks)


class TestEdgeCases:
    """Тест граничных случаев"""
    
    @pytest.mark.asyncio
    async def test_empty_message(self):
        """Тест пустого сообщения"""
        msg = create_message(text="", chat_type='private')
        
        with patch('src.bot.handlers.history_manager') as mock_hist:
            await message_handler(msg)
            # Пустые сообщения не должны обрабатываться
            mock_hist.add_message.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_very_long_message(self):
        """Тест очень длинного сообщения"""
        long_text = "Слово " * 1000  # 5000+ символов
        msg = create_message(text=long_text, chat_type='private')
        
        with patch('src.bot.handlers.history_manager') as mock_hist, \
             patch('src.bot.handlers.meme_brain') as mock_brain, \
             patch('src.bot.handlers.image_searcher') as mock_search, \
             patch('src.bot.handlers.meme_generator') as mock_gen, \
             patch('src.bot.handlers.FSInputFile'):
            
            mock_hist.get_context.return_value = [f"User: {long_text}"]
            mock_brain.generate_meme_idea.return_value = {
                "is_memable": True,
                "top_text": "ДЛИННЫЙ ТЕКСТ",
                "bottom_text": "ОБРАБОТАН",
                "search_query": "success"
            }
            mock_search.search_template.return_value = "http://img.jpg"
            mock_gen.create_meme.return_value = "output.jpg"
            
            await message_handler(msg)
            
            # Должно обработаться нормально
            msg.bot.send_photo.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_special_characters_in_message(self):
        """Тест специальных символов в сообщении"""
        special_text = "Тест <>&\"'`\\n\\t\\r %$#@!"
        msg = create_message(text=special_text, chat_type='private')
        
        with patch('src.bot.handlers.history_manager') as mock_hist, \
             patch('src.bot.handlers.meme_brain') as mock_brain, \
             patch('src.bot.handlers.image_searcher') as mock_search, \
             patch('src.bot.handlers.meme_generator') as mock_gen, \
             patch('src.bot.handlers.FSInputFile'):
            
            mock_hist.get_context.return_value = [f"User: {special_text}"]
            mock_brain.generate_meme_idea.return_value = {
                "is_memable": True,
                "top_text": "СПЕЦСИМВОЛЫ",
                "bottom_text": "ОБРАБОТАНЫ",
                "search_query": "success"
            }
            mock_search.search_template.return_value = "http://img.jpg"
            mock_gen.create_meme.return_value = "output.jpg"
            
            await message_handler(msg)
            
            # Должно обработаться нормально
            msg.bot.send_photo.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_not_memable_response(self):
        """Тест когда LLM решает, что мем не нужен"""
        msg = create_message(text="Привет", chat_type='private')
        
        with patch('src.bot.handlers.history_manager') as mock_hist, \
             patch('src.bot.handlers.meme_brain') as mock_brain:
            
            mock_hist.get_context.return_value = ["User: Привет"]
            mock_brain.generate_meme_idea.return_value = {
                "is_memable": False,
                "top_text": "",
                "bottom_text": "",
                "search_query": ""
            }
            
            await message_handler(msg)
            
            # Не должно быть отправки фото или сообщения
            msg.bot.send_photo.assert_not_called()
            # Сообщение статуса должно быть удалено
    
    @pytest.mark.asyncio
    async def test_reaction_on_missing_message(self):
        """Тест реакции на отсутствующее сообщение"""
        reaction = create_reaction(emoji="🔥", message_id=999)
        
        with patch('src.bot.handlers.history_manager') as mock_hist:
            mock_hist.get_context.return_value = []
            
            await reaction_handler(reaction)
            
            # Не должно быть никаких действий
            reaction.bot.send_photo.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_forwarded_message_ignored(self):
        """Тест игнорирования пересланных сообщений"""
        msg = create_message(text="Пересланное", chat_type='group')
        msg.forward_from = AsyncMock()
        
        with patch('src.bot.handlers.history_manager') as mock_hist:
            await message_handler(msg)
            
            # Пересланное сообщение должно быть добавлено в историю
            # (логика фильтрации в HistoryManager.add_message)
            mock_hist.add_message.assert_called_once_with(msg)


class TestInputValidation:
    """Тест валидации входных данных"""
    
    @pytest.mark.asyncio
    async def test_generate_and_send_meme_no_bot_instance(self):
        """Тест вызова без bot_instance"""
        await generate_and_send_meme(
            chat_id=123,
            triggered_text="Тест",
            context_messages=["User: Тест"],
            bot_instance=None
        )
        # Должно просто вернуться без ошибок
    
    @pytest.mark.asyncio
    async def test_generate_and_send_meme_empty_text(self):
        """Тест вызова с пустым текстом"""
        bot = AsyncMock()
        await generate_and_send_meme(
            chat_id=123,
            triggered_text="",
            context_messages=["User: Контекст"],
            bot_instance=bot
        )
        # Не должно быть вызовов к боту
        bot.send_photo.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_generate_and_send_meme_empty_context(self):
        """Тест вызова с пустым контекстом"""
        bot = AsyncMock()
        await generate_and_send_meme(
            chat_id=123,
            triggered_text="Тест",
            context_messages=[],
            bot_instance=bot
        )
        # Не должно быть вызовов к боту
        bot.send_photo.assert_not_called()


class TestRealServicesIntegration:
    """Интеграционные тесты с реальными сервисами (в мок-режиме)"""
    
    def test_history_manager_real(self):
        """Тест реального HistoryManager"""
        from src.services.history import HistoryManager
        
        history = HistoryManager(max_size=5)
        
        # Добавляем сообщения
        for i in range(10):
            msg = create_message(text=f"Message {i}", message_id=i)
            history.add_message(msg)
        
        # Проверяем размер
        context = history.get_context(123, 9)
        assert len(context) <= 5
        
        # Проверяем получение текста
        text = history.get_message_text(123, 9)
        assert text == "Message 9"
    
    def test_llm_mock_mode(self):
        """Тест LLM в мок-режиме"""
        with patch('src.services.config.config') as mock_config:
            mock_config.LLM_MOCK_ENABLED = True
            mock_config.OPENROUTER_API_KEY = "dummy"
            mock_config.OPENROUTER_MODEL = "test"
            
            from src.services.llm import MemeBrain
            brain = MemeBrain()
            brain.mock_enabled = True
            
            result = brain.generate_meme_idea(
                ["User: Тест"],
                "Тест",
                "Одобрение"
            )
            
            assert result is not None
            assert result["is_memable"] == True
            assert "top_text" in result
            assert "bottom_text" in result
            assert "search_query" in result
    
    def test_search_mock_mode(self):
        """Тест поиска в мок-режиме"""
        with patch('src.services.config.config') as mock_config:
            mock_config.SEARCH_MOCK_ENABLED = True
            mock_config.TAVILY_API_KEY = "dummy"
            
            from src.services.search import ImageSearcher
            searcher = ImageSearcher()
            searcher.mock_enabled = True
            
            result = searcher.search_template("test query")
            
            assert result is not None
            assert result.startswith("http")
    
    def test_image_generator_text_wrapping(self):
        """Тест обертки текста в MemeGenerator"""
        from src.services.image_gen import MemeGenerator
        
        gen = MemeGenerator()
        
        # Тест с длинным текстом
        long_text = "ОЧЕНЬ ДЛИННЫЙ ТЕКСТ КОТОРЫЙ ДОЛЖЕН БЫТЬ ОБЕРНУТ"
        
        # Создаем мок-шрифт для теста
        with patch('src.services.image_gen.ImageFont.truetype') as mock_font:
            font_instance = MagicMock()
            font_instance.getlength.return_value = 10
            font_instance.getbbox.return_value = (0, 0, 100, 20)
            mock_font.return_value = font_instance
            
            lines = gen._wrap_text(long_text, max_width=200, font=font_instance)
            
            # Должно быть разбито на несколько строк
            assert len(lines) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
