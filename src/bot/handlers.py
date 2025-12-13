from aiogram import Router, F
from aiogram.types import Message, MessageReactionUpdated, FSInputFile
from aiogram.filters import Command
from ..services.history import history_manager
from ..services.llm import MemeBrain
from ..services.search import ImageSearcher
from ..services.image_gen import MemeGenerator
from ..services.face_swap import FaceSwapper
import os
import html

router = Router()

# Инициализация всех сервисов
meme_brain = MemeBrain()
image_searcher = ImageSearcher()
meme_generator = MemeGenerator()
face_swapper = FaceSwapper()

# Эмодзи, на которые реагируем
MEME_TRIGGERS = ["🤡", "🔥"]
TEMP_OUTPUT_FILE = "temp_meme.jpg"

# Хендлер для сохранения истории
@router.message(F.text)
async def message_handler(message: Message):
    """Слушает все текстовые сообщения и сохраняет их в историю чата."""
    if message.text:
        history_manager.add_message(message)

# Хендлер для реакции - основной триггер
@router.message_reaction(F.new_reaction.contains(lambda reaction: any(r.emoji in MEME_TRIGGERS for r in reaction)))
async def reaction_handler(reaction: MessageReactionUpdated):
    """
    Срабатывает при получении одной из триггерных реакций. 
    Запускает всю цепочку генерации мема.
    """
    chat_id = reaction.chat.id
    
    # Получаем исходное сообщение, на которое была реакция
    # !!! Важно: в Telegram API/aiogram, чтобы получить текст исходного сообщения 
    # из MessageReactionUpdated, нужно будет сделать дополнительный запрос к API 
    # через bot.get_message(chat_id, message_id). Но для MVP и истории 
    # мы используем HistoryManager, который хранит текст.
    
    # 1. Получаем контекст из HistoryManager
    context_messages = history_manager.get_context(chat_id, reaction.message_id)

    if not context_messages:
        # Если история пуста, мы не можем сгенерировать контекстный мем
        # (или сообщение было очень давно, или бот перезагрузился)
        return

    # 2. Получаем текст сообщения, на которое поставили реакцию
    triggered_text = history_manager.get_message_text(chat_id, reaction.message_id)
    
    if not triggered_text:
        # Если не нашли сообщение в истории (слишком старое),
        # то теоретически можно попробовать bot.get_message (если есть права),
        # но для MVP просто игнорируем или берем последнее из контекста как fallback (но это рискованно)
        # Лучше просто выйти, чтобы не делать мем не на то сообщение.
        print(f"Сообщение {reaction.message_id} не найдено в истории.")
        return

    # Показываем активность "печатает"
    try:
        await reaction.bot.send_chat_action(chat_id, 'typing')
    except Exception as e:
        print(f"Не удалось отправить chat action: {e}")
    
    # 3. LLM: Генерация идеи мема (top_text, bottom_text, search_query)
    meme_idea = meme_brain.generate_meme_idea(context_messages, triggered_text)

    if not meme_idea or not meme_idea.get('is_memable'):
        # LLM решила, что мем не получится
        return
        
    query = meme_idea['search_query']
    
    # 4. Search: Поиск шаблона
    template_url = image_searcher.search_template(query + " meme template")

    if not template_url:
        await reaction.bot.send_message(chat_id, f"Простите, не нашел подходящего шаблона по запросу: *{query}*", parse_mode='Markdown')
        return

    # 5. Face Swap (опционально)
    # На этом этапе нужно было бы скачать аватар пользователя и передать его.
    # Пока пропускаем и просто используем URL
    
    # 6. Image Generation: Создание мема
    # NOTE: В реальном проекте FaceSwapper должен был бы работать с локальным файлом,
    # который мы скачали по template_url. Для MVP мы просто передаем URL в MemeGenerator.
    
    final_image_path = meme_generator.create_meme(
        image_url=template_url,
        top_text=meme_idea['top_text'],
        bottom_text=meme_idea['bottom_text'],
        output_path=TEMP_OUTPUT_FILE
    )

    if not final_image_path:
        await reaction.bot.send_message(chat_id, "Не удалось создать картинку из шаблона.", reply_to_message_id=reaction.message_id)
        return

    # 7. Отправка результата
    try:
        # Make the caption accessible and fun
        caption_text = (
            f"🤡 <b>{html.escape(meme_idea['top_text'])}</b>\n"
            f"{html.escape(meme_idea['bottom_text'])}\n\n"
            f"<i>(generated by {reaction.new_reaction[0].emoji})</i>"
        )

        await reaction.bot.send_photo(
            chat_id=chat_id,
            photo=FSInputFile(final_image_path),
            caption=caption_text,
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Ошибка при отправке фото: {e}")
        await reaction.bot.send_message(chat_id, "Ошибка отправки мема. Возможно, файл слишком большой.", reply_to_message_id=reaction.message_id)
    finally:
        # Очистка временного файла
        if os.path.exists(final_image_path):
            os.remove(final_image_path)

# Дополнительный хендлер для /start
@router.message(Command("start"))
async def command_start_handler(message: Message):
    """Ответ на команду /start."""
    await message.answer(f"Привет! Я бот-мемогенератор. Добавь меня в чат и поставь реакцию 🤡 или 🔥 на любое сообщение, чтобы запустить процесс генерации мема.")
