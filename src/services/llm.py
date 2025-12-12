from openai import OpenAI
from typing import List, Dict, Any, Optional
from .config import config
from ..utils import safe_json_parse

# 1. Задаем Pydantic модель для ожидаемого вывода
MEME_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "is_memable": {"type": "boolean", "description": "True, если сообщение заслуживает мема"},
        "top_text": {"type": "string", "description": "Текст для верхней части мема"},
        "bottom_text": {"type": "string", "description": "Текст для нижней части мема"},
        "search_query": {"type": "string", "description": "Короткое, буквальное описание изображения (шаблона) для поиска"}
    },
    "required": ["is_memable", "top_text", "bottom_text", "search_query"]
}

class MemeBrain:
    """
    Класс для взаимодействия с LLM (OpenRouter) для генерации идеи мема.
    """
    def __init__(self):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=config.OPENROUTER_API_KEY,
            default_headers={
                "HTTP-Referer": "https://t.me/your_meme_bot", # Рекомендуется OpenRouter
                "X-Title": "Telegram Meme Generator",
            },
        )
        self.model = config.OPENROUTER_MODEL
        self.mock_enabled = config.LLM_MOCK_ENABLED

    def generate_meme_idea(self, context_messages: List[str], triggered_text: str) -> Optional[Dict[str, Any]]:
        """Генерирует текст и запрос для поиска шаблона."""
        if self.mock_enabled:
            print("LLM: Используется мок-режим.")
            return {
                "is_memable": True,
                "top_text": "КОГДА ПОСТАВИЛ ОГОНЕК",
                "bottom_text": "И БОТ МГНОВЕННО ГЕНЕРИРУЕТ МЕМ",
                "search_query": "удивленная обезьяна мем шаблон"
            }

        # Формирование промпта
        context_str = "\n".join(context_messages)
        prompt = f"""
        Ты — нейросеть для генерации мемов в Телеграм-чатах. Тебе предоставлена история диалога.
        Последнее сообщение, на которое была поставлена реакция, это: "{triggered_text}".
        
        ИСТОРИЯ ДИАЛОГА (включая сообщение-триггер):
        ---
        {context_str}
        ---

        Твоя задача:
        1. Определи, можно ли на основе этого диалога создать смешной мем.
        2. Если да, придумай верхний и нижний текст.
        3. Придумай ОЧЕНЬ КОРОТКИЙ, буквальный запрос на русском языке для поиска подходящего шаблона (например, "грустный Киану Ривз", "два парня жмут руки").
        4. Ответ должен быть строго в формате JSON, соответствующем предоставленной схеме.

        ОТВЕТ:
        """

        try:
            # 
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Ты эксперт по мемам. Отвечай только в формате JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object", "schema": MEME_OUTPUT_SCHEMA},
            )
            
            # Парсинг ответа
            result = safe_json_parse(response.choices[0].message.content)
            
            if result and result.get("is_memable"):
                return result
            
        except Exception as e:
            print(f"Ошибка LLM-запроса через OpenRouter: {e}")
            return None
