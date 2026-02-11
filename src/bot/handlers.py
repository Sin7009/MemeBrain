from aiogram import Router, F
from aiogram.types import Message, MessageReactionUpdated, FSInputFile, URLInputFile
from aiogram.filters import Command
from aiogram import Bot
from ..services.history import history_manager
from ..services.llm import MemeBrain
from ..services.search import ContentSearcher
from ..services.image_gen import MemeGenerator
import os
import html
import asyncio
import logging
from typing import List, Optional

router = Router()

# Инициализация всех сервисов
meme_brain = MemeBrain()
content_searcher = ContentSearcher()
meme_generator = MemeGenerator()

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

async def handle_content_generation(
    chat_id: int,
    triggered_text: str,
    context_messages: List[str],
    reaction_context: Optional[str] = None,
    reply_to_message_id: Optional[int] = None,
    bot_instance: Optional[Bot] = None,
    trigger_emoji: Optional[str] = None
) -> None:
    """
    Основной диспетчер генерации контента.
    Решает, что отправить: Мем, Гифку, Картинку или Видео.
    """
    # Validate input
    if not bot_instance:
        logging.error("bot_instance is required for handle_content_generation")
        return
    
    if not triggered_text or not triggered_text.strip():
        return
    
    if not context_messages:
        return
    
    # 1. Показываем активность "печатает"
    try:
        await bot_instance.send_chat_action(chat_id, 'typing')
    except Exception as e:
        logging.error(f"Не удалось отправить chat action: {e}")

    # 2. LLM: Принятие решения
    decision = await asyncio.to_thread(meme_brain.decide_content, context_messages, triggered_text, reaction_context)

    if not decision:
        logging.error("❌ ОШИБКА: LLM не вернула решение.")
        # Fail silently or generic message
        return

    action = decision.get('action')
    query = decision.get('search_query')
    top_text = decision.get('top_text')
    bottom_text = decision.get('bottom_text')

    logging.info(f"🧠 Decision: {action} | Query: {query}")

    try:
        if action == "generate_meme":
            await _handle_meme_action(chat_id, query, top_text, bottom_text, reply_to_message_id, bot_instance, trigger_emoji)

        elif action == "search_gif":
            await _handle_gif_action(chat_id, query, reply_to_message_id, bot_instance)

        elif action == "search_image":
            await _handle_image_action(chat_id, query, top_text, bottom_text, reply_to_message_id, bot_instance, trigger_emoji)

        elif action == "search_video":
            await _handle_video_action(chat_id, query, reply_to_message_id, bot_instance)

        else:
            logging.warning(f"Unknown action: {action}")

    except Exception as e:
        logging.error(f"Ошибка при выполнении действия {action}: {e}")
        await bot_instance.send_message(chat_id, "Что-то пошло не так при генерации...", reply_to_message_id=reply_to_message_id)


async def _handle_meme_action(chat_id, query, top_text, bottom_text, reply_to_message_id, bot_instance, trigger_emoji):
    """Логика создания мема (Шаблон + Текст)."""
    template_url = await asyncio.to_thread(content_searcher.search_image, query + " meme template")

    if not template_url:
        await bot_instance.send_message(chat_id, f"🤷‍♂️ Не нашел шаблон: {html.escape(query)}", reply_to_message_id=reply_to_message_id)
        return

    unique_output_file = f"meme_{chat_id}_{reply_to_message_id}.jpg"
    
    final_image_path = await asyncio.to_thread(
        meme_generator.create_meme,
        image_url=template_url,
        top_text=top_text or "",
        bottom_text=bottom_text or "",
        output_path=unique_output_file
    )

    if final_image_path:
        await _send_photo_with_cleanup(chat_id, final_image_path, top_text, bottom_text, trigger_emoji, reply_to_message_id, bot_instance)
    else:
        await bot_instance.send_message(chat_id, "Ошибка генерации картинки.", reply_to_message_id=reply_to_message_id)


async def _handle_image_action(chat_id, query, top_text, bottom_text, reply_to_message_id, bot_instance, trigger_emoji):
    """Логика отправки картинки. Если есть текст - накладываем его."""
    image_url = await asyncio.to_thread(content_searcher.search_image, query)

    if not image_url:
        await bot_instance.send_message(chat_id, f"🤷‍♂️ Не нашел картинку: {html.escape(query)}", reply_to_message_id=reply_to_message_id)
        return

    # Если есть текст, превращаем в мем/демотиватор
    if top_text or bottom_text:
        unique_output_file = f"img_gen_{chat_id}_{reply_to_message_id}.jpg"
        final_image_path = await asyncio.to_thread(
            meme_generator.create_meme,
            image_url=image_url,
            top_text=top_text or "",
            bottom_text=bottom_text or "",
            output_path=unique_output_file
        )
        if final_image_path:
            await _send_photo_with_cleanup(chat_id, final_image_path, top_text, bottom_text, trigger_emoji, reply_to_message_id, bot_instance)
        else:
            # Fallback to sending raw image if generation fails
            await bot_instance.send_photo(chat_id, URLInputFile(image_url), caption=f"🔍 {html.escape(query)}", reply_to_message_id=reply_to_message_id)
    else:
        # Просто отправляем картинку
        await bot_instance.send_photo(chat_id, URLInputFile(image_url), caption=f"🔍 {html.escape(query)}", reply_to_message_id=reply_to_message_id)


async def _handle_gif_action(chat_id, query, reply_to_message_id, bot_instance):
    """Логика отправки GIF. Fallback на Image."""
    gif_url = await asyncio.to_thread(content_searcher.search_gif, query)

    if gif_url:
        await bot_instance.send_animation(chat_id, URLInputFile(gif_url), caption=f"🎞 {html.escape(query)}", reply_to_message_id=reply_to_message_id)
    else:
        # Fallback: Try image
        logging.info(f"GIF not found for '{query}', trying image...")
        await _handle_image_action(chat_id, query, None, None, reply_to_message_id, bot_instance, None)


async def _handle_video_action(chat_id, query, reply_to_message_id, bot_instance):
    """Логика отправки видео (ссылка)."""
    video_link = content_searcher.search_video(query) # Not async

    text = f"🎥 <b>Видео по теме:</b>\n{video_link}"
    await bot_instance.send_message(chat_id, text, parse_mode='HTML', reply_to_message_id=reply_to_message_id)


async def _send_photo_with_cleanup(chat_id, file_path, top, bottom, emoji, reply_id, bot):
    """Helper to send photo and cleanup file."""
    try:
        generator_tag = f"generated by {emoji}" if emoji else "AI Content Router"
        caption = f"{html.escape(top or '')} {html.escape(bottom or '')}".strip()
        if not caption:
             caption = "Generated Image"

        full_caption = f"{caption}\n\n<i>({generator_tag})</i>"[:1024]

        await bot.send_photo(
            chat_id=chat_id,
            photo=FSInputFile(file_path),
            caption=full_caption,
            parse_mode='HTML',
            reply_to_message_id=reply_id
        )
    finally:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                logging.error(f"Failed to remove temp file {file_path}: {e}")


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
        except Exception:
            pass
        return

    await handle_content_generation(
        chat_id=chat_id,
        triggered_text=triggered_text,
        context_messages=context_messages,
        reaction_context=reaction_meaning,
        reply_to_message_id=reaction.message_id,
        bot_instance=reaction.bot,
        trigger_emoji=trigger_emoji
    )


# Хендлер для текстовых сообщений
@router.message(F.text)
async def message_handler(message: Message):
    """
    Слушает все текстовые сообщения.
    """
    if message.text and message.text.strip():
        history_manager.add_message(message)
    else:
        return

    # Логика для Личных Сообщений (DM)
    if message.chat.type == 'private' and not message.text.startswith('/'):
        # Отбивка
        status_msg = await message.answer("🤖 Думаю над ответом...")

        context_messages = history_manager.get_context(message.chat.id, message.message_id)
        
        if not context_messages:
            try:
                await status_msg.delete()
            except Exception:
                pass
            return

        dm_context = "Личный чат. Будь остроумным и полезным собеседником."

        await handle_content_generation(
            chat_id=message.chat.id,
            triggered_text=message.text,
            context_messages=context_messages,
            reaction_context=dm_context,
            reply_to_message_id=message.message_id,
            bot_instance=message.bot
        )

        try:
            await status_msg.delete()
        except Exception:
            pass

# Дополнительный хендлер для /help
@router.message(Command("help"))
async def command_help_handler(message: Message):
    """Справка по использованию бота."""
    triggers_list = list(MEME_TRIGGERS.keys())
    triggers_str = ", ".join(triggers_list[:10]) + "..."

    help_text = (
        "🎨 <b>AI Content Router</b>\n\n"
        "Я теперь не просто мемодел, я агрегатор контента!\n"
        "Ставь реакции, и я решу, что отправить:\n"
        "- Мем (для шуток)\n"
        "- GIF (для эмоций)\n"
        "- Картинку (для визуализации)\n"
        "- Видео (для отсылок)\n\n"
        f"Реагируй: {triggers_str}"
    )
    await message.answer(help_text, parse_mode='HTML')


# Дополнительный хендлер для /start
@router.message(Command("start"))
async def command_start_handler(message: Message):
    """Ответ на команду /start."""
    welcome_text = (
        f"👋 <b>Привет! Я обновленный MemeBrain -> AI Content Router.</b>\n\n"
        f"Кидай мне текст или ставь реакции в группах.\n"
        "Я подберу идеальный мем, гифку или видео под контекст!"
    )
    await message.answer(welcome_text, parse_mode='HTML')


# Команда для просмотра статистики памяти
@router.message(Command("memory_stats"))
async def command_memory_stats_handler(message: Message):
    """Показывает статистику агентской памяти."""
    stats = history_manager.get_memory_statistics()
    
    if not stats.get('enabled'):
        await message.answer("Память отключена.", parse_mode='HTML')
        return
    
    stats_text = (
        f"📊 <b>Статистика</b>\n"
        f"Чатов: {stats.get('total_chats', 0)}\n"
        f"Сообщений: {stats.get('total_messages', 0)}"
    )
    await message.answer(stats_text, parse_mode='HTML')


# Команда для очистки истории текущего чата
@router.message(Command("clear_memory"))
async def command_clear_memory_handler(message: Message):
    """Очищает историю текущего чата."""
    chat_id = message.chat.id
    history_manager.history.get(chat_id, []).clear()
    
    if history_manager.memory_enabled:
        from .services.agent_memory import agent_memory
        agent_memory.clear_chat(chat_id)
    
    await message.answer("🗑 История очищена!", parse_mode='HTML')
