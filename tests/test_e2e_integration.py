"""
End-to-End интеграционный тест для MemeBrain.
Симулирует реальный сценарий работы бота от начала до конца.
"""
import pytest

# Настройка pytest-asyncio
pytest_plugins = ('pytest_asyncio',)
import asyncio
import os
from unittest.mock import patch, AsyncMock, MagicMock
from src.bot.handlers import (
    command_start_handler,
    command_help_handler,
    message_handler,
    reaction_handler,
    MEME_TRIGGERS
)
from aiogram.types import Message, Chat, User
from src.services.history import HistoryManager


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


class TestE2EUserJourney:
    """End-to-End тест полного пути пользователя"""
    
    @pytest.mark.asyncio
    async def test_complete_user_journey_private_chat(self):
        """
        Симуляция полного пути пользователя в личном чате:
        1. Пользователь отправляет /start
        2. Пользователь отправляет /help
        3. Пользователь отправляет несколько сообщений
        4. Бот генерирует мемы на каждое сообщение
        """
        user_id = 12345
        chat_id = 12345  # В личном чате chat_id = user_id
        
        # Шаг 1: /start
        start_msg = create_message(text="/start", chat_id=chat_id, user_id=user_id)
        await command_start_handler(start_msg)
        start_msg.answer.assert_called_once()
        assert "Привет" in start_msg.answer.call_args[0][0]
        
        # Шаг 2: /help
        help_msg = create_message(text="/help", chat_id=chat_id, user_id=user_id)
        await command_help_handler(help_msg)
        help_msg.answer.assert_called_once()
        assert "Как пользоваться ботом" in help_msg.answer.call_args[0][0]
        
        # Шаг 3-4: Отправка сообщений и генерация мемов
        with patch('src.bot.handlers.history_manager') as mock_hist, \
             patch('src.bot.handlers.meme_brain') as mock_brain, \
             patch('src.bot.handlers.image_searcher') as mock_search, \
             patch('src.bot.handlers.meme_generator') as mock_gen, \
             patch('src.bot.handlers.FSInputFile'):
            
            # Настройка моков
            mock_hist.get_context.return_value = ["User: Привет, как дела?"]
            mock_brain.generate_meme_idea.return_value = {
                "is_memable": True,
                "top_text": "КОГДА НАПИСАЛ В ЧАТ",
                "bottom_text": "И БОТ СДЕЛАЛ МЕМ",
                "search_query": "surprised pikachu"
            }
            mock_search.search_template.return_value = "http://example.com/img.jpg"
            mock_gen.create_meme.return_value = "output.jpg"
            
            # Отправляем несколько сообщений
            messages = [
                "Привет, как дела?",
                "Расскажи мне анекдот",
                "Сегодня отличная погода"
            ]
            
            for i, text in enumerate(messages):
                msg = create_message(
                    text=text,
                    chat_id=chat_id,
                    user_id=user_id,
                    message_id=i + 10
                )
                await message_handler(msg)
                
                # Проверяем, что бот ответил
                msg.bot.send_photo.assert_called()
    
    @pytest.mark.asyncio
    async def test_complete_user_journey_group_chat(self):
        """
        Симуляция полного пути в групповом чате:
        1. Несколько пользователей отправляют сообщения
        2. История накапливается
        3. Один пользователь ставит реакцию
        4. Бот генерирует мем на основе контекста
        """
        chat_id = 99999
        
        with patch('src.bot.handlers.history_manager') as mock_hist, \
             patch('src.bot.handlers.meme_brain') as mock_brain, \
             patch('src.bot.handlers.image_searcher') as mock_search, \
             patch('src.bot.handlers.meme_generator') as mock_gen, \
             patch('src.bot.handlers.FSInputFile'):
            
            # Шаг 1: Несколько пользователей отправляют сообщения
            conversation = [
                (1, "Привет всем!"),
                (2, "Как дела?"),
                (1, "Отлично, спасибо!"),
                (3, "Кто-то знает погоду на завтра?"),
                (2, "Говорят будет дождь"),
                (1, "Опять дождь... надоело")
            ]
            
            for user_id, text in conversation:
                msg = create_message(
                    text=text,
                    chat_id=chat_id,
                    user_id=user_id,
                    chat_type='group',
                    message_id=len(mock_hist.add_message.call_args_list) if mock_hist.add_message.called else 0
                )
                await message_handler(msg)
                # В группе мемы не генерируются автоматически
                mock_hist.add_message.assert_called()
            
            # Шаг 2: Реакция на последнее сообщение
            mock_hist.get_context.return_value = [
                f"User {uid}: {txt}" for uid, txt in conversation
            ]
            mock_hist.get_message_text.return_value = conversation[-1][1]
            mock_brain.generate_meme_idea.return_value = {
                "is_memable": True,
                "top_text": "ОПЯТЬ ДОЖДЬ",
                "bottom_text": "КЛАССИКА",
                "search_query": "sad rain"
            }
            mock_search.search_template.return_value = "http://example.com/rain.jpg"
            mock_gen.create_meme.return_value = "rain_meme.jpg"
            
            reaction = create_reaction(emoji="😢", chat_id=chat_id, message_id=5)
            await reaction_handler(reaction)
            
            # Проверяем, что мем был сгенерирован с учетом контекста
            mock_brain.generate_meme_idea.assert_called_once()
            reaction.bot.send_photo.assert_called_once()


class TestE2EConversationFlow:
    """E2E тест естественного потока разговора"""
    
    @pytest.mark.asyncio
    async def test_natural_conversation_with_context(self):
        """
        Симуляция естественного разговора с накоплением контекста
        """
        chat_id = 77777
        history = HistoryManager(max_size=10)
        
        # Создаем естественный разговор
        conversation_script = [
            (1, "Ребят, кто видел новую серию Рика и Морти?"),
            (2, "Я смотрел, она просто бомба!"),
            (3, "Серьезно? Что там произошло?"),
            (1, "Не буду спойлерить, но концовка просто взорвала мне мозг"),
            (2, "Да, моменты с порталом были гениальны"),
            (3, "Теперь хочу посмотреть"),
            (1, "Обязательно посмотри, не пожалеешь!"),
        ]
        
        # Добавляем сообщения в историю
        for user_id, text in conversation_script:
            msg = create_message(
                text=text,
                chat_id=chat_id,
                user_id=user_id,
                message_id=len(conversation_script) - conversation_script.index((user_id, text))
            )
            history.add_message(msg)
        
        # Проверяем, что контекст сохранился
        context = history.get_context(chat_id, 1)
        assert len(context) > 0
        assert any("Рика и Морти" in msg for msg in context)
        
        # Теперь симулируем реакцию и генерацию мема
        with patch('src.bot.handlers.history_manager', history), \
             patch('src.bot.handlers.meme_brain') as mock_brain, \
             patch('src.bot.handlers.image_searcher') as mock_search, \
             patch('src.bot.handlers.meme_generator') as mock_gen, \
             patch('src.bot.handlers.FSInputFile'):
            
            mock_brain.generate_meme_idea.return_value = {
                "is_memable": True,
                "top_text": "КОГДА УВИДЕЛ НОВУЮ СЕРИЮ",
                "bottom_text": "И МОЗГ ВЗОРВАЛСЯ",
                "search_query": "mind blown"
            }
            mock_search.search_template.return_value = "http://example.com/mindblown.jpg"
            mock_gen.create_meme.return_value = "mindblown.jpg"
            
            reaction = create_reaction(emoji="🤯", chat_id=chat_id, message_id=4)
            await reaction_handler(reaction)
            
            # Проверяем, что LLM получил весь контекст
            call_args = mock_brain.generate_meme_idea.call_args
            context_passed = call_args[0][0]
            assert len(context_passed) > 0


class TestE2EErrorRecovery:
    """E2E тест восстановления после ошибок"""
    
    @pytest.mark.asyncio
    async def test_error_recovery_sequence(self):
        """
        Тест восстановления после различных ошибок в цепочке
        """
        chat_id = 55555
        user_id = 11111
        
        with patch('src.bot.handlers.history_manager') as mock_hist, \
             patch('src.bot.handlers.meme_brain') as mock_brain, \
             patch('src.bot.handlers.image_searcher') as mock_search, \
             patch('src.bot.handlers.meme_generator') as mock_gen, \
             patch('src.bot.handlers.FSInputFile'):
            
            mock_hist.get_context.return_value = ["User: Тестовое сообщение"]
            
            # Сценарий 1: LLM падает, потом восстанавливается
            mock_brain.generate_meme_idea.side_effect = [
                None,  # Первая попытка - ошибка
                {      # Вторая попытка - успех
                    "is_memable": True,
                    "top_text": "УСПЕХ",
                    "bottom_text": "ПОСЛЕ ОШИБКИ",
                    "search_query": "success"
                }
            ]
            mock_search.search_template.return_value = "http://img.jpg"
            mock_gen.create_meme.return_value = "output.jpg"
            
            # Первая попытка - ошибка
            msg1 = create_message(text="Тест 1", chat_id=chat_id, user_id=user_id, message_id=1)
            await message_handler(msg1)
            msg1.bot.send_message.assert_called()  # Ошибка была обработана
            
            # Вторая попытка - успех
            msg2 = create_message(text="Тест 2", chat_id=chat_id, user_id=user_id, message_id=2)
            await message_handler(msg2)
            msg2.bot.send_photo.assert_called()  # Успешная генерация


class TestE2EMultiUserScenarios:
    """E2E тест сценариев с множественными пользователями"""
    
    @pytest.mark.asyncio
    async def test_multiple_users_concurrent_requests(self):
        """
        Тест одновременных запросов от разных пользователей
        """
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
            
            # Создаем задачи для 20 пользователей
            tasks = []
            for user_id in range(1, 21):
                msg = create_message(
                    text=f"Сообщение от пользователя {user_id}",
                    chat_id=user_id,  # У каждого свой чат
                    user_id=user_id,
                    message_id=1
                )
                tasks.append(message_handler(msg))
            
            # Выполняем все параллельно
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Проверяем, что все обработались без исключений
            for result in results:
                assert not isinstance(result, Exception)
            
            # Проверяем, что было создано 20 мемов
            assert mock_gen.create_meme.call_count == 20
    
    @pytest.mark.asyncio
    async def test_multiple_chats_isolation(self):
        """
        Тест изоляции контекста между разными чатами
        """
        history = HistoryManager(max_size=5)
        
        # Создаем сообщения в разных чатах
        chat_messages = {
            1: ["Сообщение в чате 1", "Еще одно в чате 1"],
            2: ["Сообщение в чате 2", "Продолжение чата 2"],
            3: ["Третий чат начало", "Третий чат продолжение"]
        }
        
        for chat_id, messages in chat_messages.items():
            for i, text in enumerate(messages):
                msg = create_message(
                    text=text,
                    chat_id=chat_id,
                    user_id=1,
                    message_id=i
                )
                history.add_message(msg)
        
        # Проверяем изоляцию контекстов
        context_1 = history.get_context(1, 1)
        context_2 = history.get_context(2, 1)
        context_3 = history.get_context(3, 1)
        
        assert any("чате 1" in msg for msg in context_1)
        assert any("чате 2" in msg for msg in context_2)
        assert any("Третий чат" in msg for msg in context_3)
        
        # Контексты не должны пересекаться
        assert not any("чате 2" in msg for msg in context_1)
        assert not any("чате 1" in msg for msg in context_2)


class TestE2EAllEmojiWorkflow:
    """E2E тест работы всех эмодзи-триггеров"""
    
    @pytest.mark.asyncio
    async def test_all_emoji_generate_appropriate_memes(self):
        """
        Тест что каждая эмодзи генерирует соответствующий мем
        """
        chat_id = 88888
        
        with patch('src.bot.handlers.history_manager') as mock_hist, \
             patch('src.bot.handlers.meme_brain') as mock_brain, \
             patch('src.bot.handlers.image_searcher') as mock_search, \
             patch('src.bot.handlers.meme_generator') as mock_gen, \
             patch('src.bot.handlers.FSInputFile'):
            
            mock_hist.get_context.return_value = ["User: Контекст"]
            mock_hist.get_message_text.return_value = "Сообщение"
            mock_search.search_template.return_value = "http://img.jpg"
            mock_gen.create_meme.return_value = "output.jpg"
            
            # Тестируем каждую эмодзи
            for emoji, meaning in MEME_TRIGGERS.items():
                # Настраиваем мок для каждой эмодзи
                mock_brain.generate_meme_idea.return_value = {
                    "is_memable": True,
                    "top_text": f"ЭМОДЗИ {emoji}",
                    "bottom_text": meaning.upper(),
                    "search_query": "test"
                }
                
                reaction = create_reaction(
                    emoji=emoji,
                    chat_id=chat_id,
                    message_id=list(MEME_TRIGGERS.keys()).index(emoji)
                )
                
                await reaction_handler(reaction)
                
                # Проверяем, что LLM получил контекст реакции
                call_args = mock_brain.generate_meme_idea.call_args
                if call_args:
                    reaction_context = call_args[0][2] if len(call_args[0]) > 2 else None
                    # Контекст реакции должен содержать значение эмодзи
                    if reaction_context:
                        assert meaning in reaction_context


class TestE2ERealWorldScenarios:
    """E2E тесты реальных сценариев использования"""
    
    @pytest.mark.asyncio
    async def test_meme_debate_scenario(self):
        """
        Сценарий: Дебаты в чате с множественными мемами
        """
        chat_id = 44444
        history = HistoryManager(max_size=15)
        
        # Симулируем дебаты
        debate = [
            (1, "Я считаю, что пицца с ананасами - это нормально"),
            (2, "Что?! Это преступление против человечества!"),
            (3, "Согласен со вторым, ананасы на пицце - зло"),
            (1, "Вы просто не пробовали правильную гавайскую пиццу"),
            (2, "Я пробовал, и это было ужасно"),
            (3, "Давайте не будем ссориться из-за еды"),
            (1, "Хорошо, согласен на мирное сосуществование")
        ]
        
        for user_id, text in debate:
            msg = create_message(
                text=text,
                chat_id=chat_id,
                user_id=user_id,
                chat_type='group',
                message_id=debate.index((user_id, text))
            )
            history.add_message(msg)
        
        # Проверяем, что весь спор сохранен в истории
        context = history.get_context(chat_id, 6)
        assert len(context) > 0
        
        # Генерируем мем на одно из сообщений спора
        with patch('src.bot.handlers.history_manager', history), \
             patch('src.bot.handlers.meme_brain') as mock_brain, \
             patch('src.bot.handlers.image_searcher') as mock_search, \
             patch('src.bot.handlers.meme_generator') as mock_gen, \
             patch('src.bot.handlers.FSInputFile'):
            
            mock_brain.generate_meme_idea.return_value = {
                "is_memable": True,
                "top_text": "КОГДА НАЧИНАЕТСЯ СПОР",
                "bottom_text": "О ПИЦЦЕ С АНАНАСАМИ",
                "search_query": "debate meme"
            }
            mock_search.search_template.return_value = "http://debate.jpg"
            mock_gen.create_meme.return_value = "debate.jpg"
            
            reaction = create_reaction(emoji="🤬", chat_id=chat_id, message_id=1)
            await reaction_handler(reaction)
            
            # Мем должен быть создан с учетом всего контекста спора
            reaction.bot.send_photo.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_celebration_scenario(self):
        """
        Сценарий: Празднование успеха в чате
        """
        chat_id = 33333
        
        celebration_messages = [
            (1, "Ребята, я сдал экзамен!"),
            (2, "Поздравляю! 🎉"),
            (3, "Молодец, всегда в тебя верил!"),
            (4, "Давай отметим!")
        ]
        
        with patch('src.bot.handlers.history_manager') as mock_hist, \
             patch('src.bot.handlers.meme_brain') as mock_brain, \
             patch('src.bot.handlers.image_searcher') as mock_search, \
             patch('src.bot.handlers.meme_generator') as mock_gen, \
             patch('src.bot.handlers.FSInputFile'):
            
            # Формируем контекст празднования
            context = [f"User {uid}: {txt}" for uid, txt in celebration_messages]
            mock_hist.get_context.return_value = context
            mock_hist.get_message_text.return_value = celebration_messages[0][1]
            
            mock_brain.generate_meme_idea.return_value = {
                "is_memable": True,
                "top_text": "КОГДА СДАЛ ЭКЗАМЕН",
                "bottom_text": "ВРЕМЯ ПРАЗДНОВАТЬ",
                "search_query": "celebration"
            }
            mock_search.search_template.return_value = "http://party.jpg"
            mock_gen.create_meme.return_value = "party.jpg"
            
            reaction = create_reaction(emoji="🎉", chat_id=chat_id, message_id=0)
            await reaction_handler(reaction)
            
            # Проверяем успешную генерацию праздничного мема
            reaction.bot.send_photo.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
