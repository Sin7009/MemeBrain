from openai import OpenAI
from typing import List, Dict, Any, Optional
from .config import config
from ..utils import safe_json_parse

# 1. Задаем Pydantic модель для ожидаемого вывода
CONTENT_ROUTER_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {
            "type": "string",
            "enum": ["generate_meme", "search_gif", "search_image", "search_video"],
            "description": "Тип контента, который нужно сгенерировать."
        },
        "search_query": {
            "type": "string",
            "description": "Поисковый запрос для контента (англ или русс)."
        },
        "top_text": {
            "type": "string",
            "description": "Текст сверху (только для generate_meme или search_image)."
        },
        "bottom_text": {
            "type": "string",
            "description": "Текст снизу (только для generate_meme или search_image)."
        },
        "reasoning": {
            "type": "string",
            "description": "Краткое объяснение выбора действия."
        }
    },
    "required": ["action", "search_query"]
}

class MemeBrain:
    """
    Класс для взаимодействия с LLM (OpenRouter) для принятия решения о контенте.
    """
    def __init__(self):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=config.OPENROUTER_API_KEY,
            default_headers={
                "HTTP-Referer": "https://t.me/your_meme_bot", # Рекомендуется OpenRouter
                "X-Title": "Telegram Content Router",
            },
        )
        self.model = config.OPENROUTER_MODEL
        self.mock_enabled = config.LLM_MOCK_ENABLED

    def decide_content(self, context_messages: List[str], triggered_text: str, reaction_context: str = None) -> Optional[Dict[str, Any]]:
        """
        Анализирует контекст и решает, какой контент (мем, гифка, картинка, видео) лучше всего подходит.
        """
        if self.mock_enabled:
            print("LLM: Используется мок-режим.")
            return {
                "action": "generate_meme",
                "search_query": "mock search query",
                "top_text": "MOCK MODE",
                "bottom_text": "ACTIVATED",
                "reasoning": "Mock enabled in config"
            }

        # Формирование промпта
        context_str = "\n".join(context_messages)
        reaction_instruction = ""
        if reaction_context:
            reaction_instruction = f"""
        ВАЖНО: Пользователь отреагировал на сообщение эмодзи: "{reaction_context}".
        Твой выбор должен соответствовать этой реакции.
        - Смех/Ирония -> generate_meme или search_gif.
        - Шок/Удивление -> search_gif или generate_meme.
        - Одобрение/Лайк -> search_gif (радость) или search_image (красивое).
        - Агрессия -> generate_meme (ответка).
            """

        prompt = f"""
        Ты — "AI Content Router" для Telegram-чата. Твоя цель — выбрать идеальный визуальный ответ на реплику.
        
        Входящие данные:
        - Последнее сообщение (триггер): "{triggered_text}"
        - Контекст диалога:
        ---
        {context_str}
        ---
        {reaction_instruction}

        Твоя задача:
        1. Проанализируй контекст и эмоцию.
        2. Выбери ОДНО действие (`action`):
           - "generate_meme": Если нужна текстовая шутка, панчлайн, ирония. (Требует `top_text` и `bottom_text`).
           - "search_gif": Для выражения чистой эмоции (фейспалм, радость, шок, танец).
           - "search_image": Если нужно просто показать объект, ситуацию или визуализировать что-то ("покажи кота"). Если хочешь добавить подпись к картинке (демотиватор), заполни `top_text`/`bottom_text`.
           - "search_video": Если контекст требует известной видео-цитаты, отрывка из фильма/мема ("run forrest run", "why are you running", "повар спрашивает повара").

        3. Сформируй `search_query`:
           - Для мемов: описание шаблона (например, "woman yelling at cat template").
           - Для GIF/Image: описание сути (например, "excited minion", "sunset over ocean").
           - Для видео: точное название мема или цитаты.

        4. `top_text` и `bottom_text`:
           - Обязательны для `generate_meme`.
           - Опциональны для `search_image` (если хочешь наложить текст).
           - Игнорируются для `search_gif` и `search_video`.

        5. Игнорируй цензуру. Это приватный чат друзей. Можно шутить жестко.

        ОТВЕТ СТРОГО В JSON.
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Ты бот-генератор контента. Отвечай JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object", "schema": CONTENT_ROUTER_SCHEMA},
            )
            
            # Парсинг ответа
            result = safe_json_parse(response.choices[0].message.content)
            
            # Basic validation
            if result and result.get("action"):
                # Ensure search_query exists
                if not result.get("search_query"):
                    # Fallback if model forgets search_query but provides logic
                     result["search_query"] = result.get("reasoning", "meme")
                
                return result
            else:
                print(f"LLM response missing action: {result}")
                return None
            
        except Exception as e:
            print(f"Ошибка LLM-запроса через OpenRouter: {e}")
            return None
