import os
import asyncio
from src.services.llm import MemeBrain
from src.services.image_gen import MemeGenerator
from src.services.config import config
from dotenv import load_dotenv

# Загружаем переменные окружения, чтобы получить настройки моков
load_dotenv()

# Устанавливаем мок-режимы для тестирования
config.LLM_MOCK_ENABLED = True
config.SEARCH_MOCK_ENABLED = True

# Исходные данные для моков
MOCK_CONTEXT = [
    "User 123: Всем привет, как настроение?",
    "User 456: Скучно что-то, сижу код пишу.",
    "User 123: Зато я сегодня запустил юнит-тесты без ошибок с первого раза!", # <-- Триггерное сообщение
]
MOCK_TRIGGER_TEXT = "Зато я сегодня запустил юнит-тесты без ошибок с первого раза!"
TEST_OUTPUT_FILE = "test_meme_result.jpg"

import pytest

@pytest.mark.asyncio
async def test_full_pipeline_mock():
    print("--- 🧪 Запуск локального тестирования пайплайна (Mock Mode) ---")
    
    # 1. LLM Mock: Получение идеи
    meme_brain = MemeBrain()
    meme_idea = meme_brain.generate_meme_idea(MOCK_CONTEXT, MOCK_TRIGGER_TEXT)
    
    if not meme_idea:
        print("Тест LLM: Провал. Идея не сгенерирована.")
        return

    print(f"Тест LLM: Успех. Идея: {meme_idea['top_text']} / {meme_idea['bottom_text']}")
    
    # 2. Search Mock: Получение URL шаблона (используется mock URL)
    from src.services.search import ImageSearcher
    image_searcher = ImageSearcher()
    template_url = image_searcher.search_template(meme_idea['search_query'])
    
    if not template_url:
        print("Тест Search: Провал. URL не получен.")
        return
    
    print(f"Тест Search: Успех. URL: {template_url}")

    # 3. Image Generation: Создание файла
    meme_generator = MemeGenerator()
    final_path = meme_generator.create_meme(
        image_url=template_url,
        top_text=meme_idea['top_text'],
        bottom_text=meme_idea['bottom_text'],
        output_path=TEST_OUTPUT_FILE
    )
    
    if final_path and os.path.exists(final_path):
        print(f"--- ✅ Тест УСПЕШЕН. Мем сохранен локально: {final_path}")
        # 
    else:
        print("--- ❌ Тест ПРОВАЛЕН. Файл не был создан.")
        
    # Очистка
    if os.path.exists(TEST_OUTPUT_FILE):
        os.remove(TEST_OUTPUT_FILE)
        
if __name__ == "__main__":
    # Для корректного запуска асинхронного кода в скрипте
    asyncio.run(test_full_pipeline_mock())
