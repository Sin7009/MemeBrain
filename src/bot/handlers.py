from aiogram import Router, F
from aiogram.types import Message, MessageReactionUpdated, FSInputFile
from aiogram.filters import Command
from aiogram import Bot
from ..services.history import history_manager
from ..services.llm import MemeBrain
from ..services.search import ImageSearcher
from ..services.image_gen import MemeGenerator
from ..services.face_swap import FaceSwapper
import os
import html
import asyncio
import logging
from typing import List, Optional

router = Router()

# Инициализация всех сервисов
meme_brain = MemeBrain()
image_searcher = ImageSearcher()
meme_generator = MemeGenerator()
face_swapper = FaceSwapper()

# Эмодзи, на которые реагируем, и их смысловое значение
MEME_TRIGGERS = {
    "👍": "Одобрение, класс, лайк",
    "👎": "Осуждение, дизлайк, плохо",
    "❤": "Любовь, очень нравится",
    "🔥": "Офигеть как круто, огонь, жара",
    "🥰": "Милота, обожание",
    "👏": "Аплодисменты, браво, поддержка",
    "😁": "Смешно, радость, ухмылка",
    "🤔": "Задумался, сомнение, подозрение",
    "🤯": "Взрыв мозга, шок, невероятно",
    "😱": "Испуг, шок, ужас",
    "🤬": "Злость, ярость, маты",
    "😢": "Грусть, печаль, слезы",
    "🎉": "Праздник, поздравление, радость",
    "🤩": "Восхищение, звезды в глазах",
    "🤮": "Тошнота, отвращение, гадость",
    "💩": "Дерьмо, очень плохо, ирония",
    "🤡": "Клоунада, глупость, ирония над автором"
}
TEMP_OUTPUT_FILE = "temp_meme.jpg"

async def generate_and_send_meme(
    chat_id: int,
    triggered_text: str,
    context_messages: List[str],
    reaction_context: Optional[str] = None,
    reply_to_message_id: Optional[int] = None,
    bot_instance: Optional[Bot] = None,
    trigger_emoji: Optional[str] = None
) -> None:
    """
    Общая логика генерации и отправки мема.
    """
    # Validate input
    if not bot_instance:
        logging.error("bot_instance is required for generate_and_send_meme")
        return
    
    if not triggered_text or not triggered_text.strip():
        logging.warning("Skipping meme generation: triggered_text is empty")
        return
    
    if not context_messages:
        logging.warning("Skipping meme generation: context_messages is empty")
        return
    
    # 1. Показываем активность "печатает"
    try:
        await bot_instance.send_chat_action(chat_id, 'typing')
    except Exception as e:
        logging.error(f"Не удалось отправить chat action: {e}")

    # 2. LLM: Генерация идеи мема
    meme_idea = meme_brain.generate_meme_idea(context_messages, triggered_text, reaction_context)

    if not meme_idea:
        logging.error("❌ ОШИБКА: LLM вернула пустоту. Скорее всего, сломался JSON из-за мата или фильтров OpenAI.")
        # Опционально: сказать юзеру, что бот сломался
        await bot_instance.send_message(chat_id, "Мозги сломались, слишком сложно!", reply_to_message_id=reply_to_message_id)
        return

    if not meme_idea.get('is_memable'):
        logging.warning("⚠️ ОТКАЗ: Нейросеть решила, что это не смешно (или сработал фильтр).")
        return

    logging.info(f"✅ Идея сгенерирована: {meme_idea.get('top_text')} / {meme_idea.get('bottom_text')}")

    query = meme_idea['search_query']

    # 3. Search: Поиск шаблона
    template_url = image_searcher.search_template(query + " meme template")

    if not template_url:
        await bot_instance.send_message(
            chat_id,
            f"🎨 <b>Шаблон не найден!</b>\n\n"
            f"Я не смог найти подходящую картинку по запросу: <i>{html.escape(query)}</i>.",
            parse_mode='HTML',
            reply_to_message_id=reply_to_message_id
        )
        return

    # 4. Image Generation: Создание мема
    # Используем уникальное имя файла для каждого запроса, чтобы избежать гонок (в простой реализации)
    # Но для сохранения логики с TEMP_OUTPUT_FILE будем пока использовать его, зная о рисках.
    # Лучше сделать уникальным.
    unique_output_file = f"temp_meme_{chat_id}_{reply_to_message_id}.jpg"
    
    final_image_path = meme_generator.create_meme(
        image_url=template_url,
        top_text=meme_idea['top_text'],
        bottom_text=meme_idea['bottom_text'],
        output_path=unique_output_file
    )

    if not final_image_path:
        await bot_instance.send_message(chat_id, "Не удалось создать картинку из шаблона.", reply_to_message_id=reply_to_message_id)
        return

    # 5. Отправка результата
    try:
        generator_tag = f"generated by {trigger_emoji}" if trigger_emoji else "generated by meme bot"
        caption_text = (
            f"🤡 <b>{html.escape(meme_idea['top_text'])}</b>\n"
            f"{html.escape(meme_idea['bottom_text'])}\n\n"
            f"<i>({generator_tag})</i>"
        )

        await bot_instance.send_photo(
            chat_id=chat_id,
            photo=FSInputFile(final_image_path),
            caption=caption_text,
            parse_mode='HTML',
            reply_to_message_id=reply_to_message_id
        )
    except Exception as e:
        logging.error(f"Ошибка при отправке фото: {e}")
        try:
            await bot_instance.send_message(chat_id, "Ошибка отправки мема.", reply_to_message_id=reply_to_message_id)
        except Exception as nested_e:
            logging.error(f"Не удалось отправить сообщение об ошибке: {nested_e}")
    finally:
        # Clean up temporary file
        if os.path.exists(final_image_path):
            try:
                os.remove(final_image_path)
            except Exception as e:
                logging.error(f"Не удалось удалить временный файл {final_image_path}: {e}")


# Хендлер для реакции - основной триггер
@router.message_reaction(F.new_reaction.contains(lambda reaction: any(r.emoji in MEME_TRIGGERS for r in reaction)))
async def reaction_handler(reaction: MessageReactionUpdated):
    """
    Срабатывает при получении одной из триггерных реакций.
    """
    chat_id = reaction.chat.id
    trigger_emoji = reaction.new_reaction[0].emoji
    reaction_meaning = MEME_TRIGGERS.get(trigger_emoji)
    
    if not reaction_meaning:
        logging.warning(f"Unknown trigger emoji: {trigger_emoji}")
        return

    # Получаем контекст из HistoryManager
    context_messages = history_manager.get_context(chat_id, reaction.message_id)
    if not context_messages:
        return

    # Получаем текст сообщения
    triggered_text = history_manager.get_message_text(chat_id, reaction.message_id)

    if not triggered_text:
        try:
            await reaction.bot.send_message(
                chat_id,
                "🧐 <b>Я не вижу это сообщение!</b>\n\n"
                "Я могу делать мемы только из сообщений, которые пришли, пока я был онлайн.",
                parse_mode='HTML'
            )
        except Exception as e:
            logging.error(f"Не удалось отправить сообщение об ошибке истории: {e}")
        return

    await generate_and_send_meme(
        chat_id=chat_id,
        triggered_text=triggered_text,
        context_messages=context_messages,
        reaction_context=reaction_meaning,
        reply_to_message_id=reaction.message_id, # Отвечаем на сообщение, на которое была реакция - хотя технически это может быть не всегда возможно, если сообщение старое. Но try/except в generate_and_send_meme обработает.
        bot_instance=reaction.bot,
        trigger_emoji=trigger_emoji
    )


# Хендлер для текстовых сообщений
@router.message(F.text)
async def message_handler(message: Message):
    """
    Слушает все текстовые сообщения.
    1. Сохраняет их в историю.
    2. В личных сообщениях (private) автоматически генерирует мем.
    """
    if message.text and message.text.strip():
        history_manager.add_message(message)
    else:
        # Skip empty messages
        return

    # Логика для Личных Сообщений (DM)
    if message.chat.type == 'private' and not message.text.startswith('/'):
        # Отбивка: временное сообщение
        status_msg = await message.answer("🎨 Придумываю мем...")

        # Получаем контекст (последние сообщения, включая текущее)
        context_messages = history_manager.get_context(message.chat.id, message.message_id)
        
        if not context_messages:
            try:
                await status_msg.delete()
            except Exception:
                pass
            return

        # Запускаем генерацию
        # В качестве reaction_context передаем нейтральный или специфичный для ЛС контекст
        dm_context = "Пользователь написал это сообщение в личном чате. Сделай мем, который иронично обыгрывает этот текст."

        await generate_and_send_meme(
            chat_id=message.chat.id,
            triggered_text=message.text,
            context_messages=context_messages,
            reaction_context=dm_context,
            reply_to_message_id=message.message_id,
            bot_instance=message.bot
        )

        # Удаляем отбивку
        try:
            await status_msg.delete()
        except Exception:
            pass

# Дополнительный хендлер для /help
@router.message(Command("help"))
async def command_help_handler(message: Message):
    """Справка по использованию бота."""
    # Выводим первые 5 и последние для краткости или просто список
    triggers_list = list(MEME_TRIGGERS.keys())
    triggers_str = ", ".join(triggers_list[:10]) + "..."

    help_text = (
        "🎨 <b>Как пользоваться ботом</b>\n\n"
        "Я превращаю ваши сообщения в мемы! Вот как это работает:\n\n"
        f"1. <b>Реакция</b>: Поставьте реакцию ({triggers_str}) на любое сообщение.\n"
        "2. <b>Личка</b>: Просто напиши мне сообщение, и я сделаю из него мем.\n"
        "3. <b>Контекст</b>: Я читаю диалог, чтобы мем был в тему.\n\n"
        "<i>Совет: Добавьте меня в группу, там веселее!</i>"
    )
    await message.answer(help_text, parse_mode='HTML')


# Дополнительный хендлер для /start
@router.message(Command("start"))
async def command_start_handler(message: Message):
    """Ответ на команду /start."""
    welcome_text = (
        f"👋 <b>Привет! Я бот-мемогенератор.</b>\n\n"
        f"Добавь меня в чат и ставь реакции на сообщения.\n"
        "Или просто пиши мне сюда — я сделаю мем из твоего текста!\n\n"
        "Нажми /help для подробностей!"
    )
    await message.answer(welcome_text, parse_mode='HTML')


# Команда для просмотра статистики памяти
@router.message(Command("memory_stats"))
async def command_memory_stats_handler(message: Message):
    """Показывает статистику агентской памяти."""
    stats = history_manager.get_memory_statistics()
    
    if not stats.get('enabled'):
        await message.answer(
            "📝 <b>Агентская память отключена</b>\n\n"
            "Память не сохраняется между перезапусками.",
            parse_mode='HTML'
        )
        return
    
    stats_text = (
        f"📊 <b>Статистика агентской памяти</b>\n\n"
        f"💬 <b>Чатов в памяти:</b> {stats.get('total_chats', 0)}\n"
        f"📝 <b>Всего сообщений:</b> {stats.get('total_messages', 0)}\n"
        f"🗂 <b>ID чатов:</b> {', '.join(map(str, stats.get('chat_ids', [])[:5]))}"
    )
    
    if len(stats.get('chat_ids', [])) > 5:
        stats_text += f"... (+{len(stats['chat_ids']) - 5} еще)"
    
    await message.answer(stats_text, parse_mode='HTML')


# Команда для очистки истории текущего чата
@router.message(Command("clear_memory"))
async def command_clear_memory_handler(message: Message):
    """Очищает историю текущего чата из памяти."""
    chat_id = message.chat.id
    
    # Проверяем, есть ли что очищать
    if chat_id not in history_manager.history or len(history_manager.history[chat_id]) == 0:
        await message.answer(
            "🤷‍♂️ <b>История пуста</b>\n\n"
            "В этом чате нет сохраненных сообщений.",
            parse_mode='HTML'
        )
        return
    
    # Очищаем in-memory историю
    message_count = len(history_manager.history[chat_id])
    history_manager.history[chat_id].clear()
    
    # Очищаем markdown файлы если память включена
    if history_manager.memory_enabled:
        from .services.agent_memory import agent_memory
        agent_memory.clear_chat(chat_id)
    
    await message.answer(
        f"🗑 <b>История очищена!</b>\n\n"
        f"Удалено {message_count} сообщений из памяти этого чата.",
        parse_mode='HTML'
    )
