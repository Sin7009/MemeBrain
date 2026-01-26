import requests
from typing import Optional
from functools import lru_cache
from .config import config

class ImageSearcher:
    """
    Сервис поиска картинок через Tavily API.
    """
    API_URL = "https://api.tavily.com/search"

    def __init__(self):
        self.api_key = config.TAVILY_API_KEY
        self.mock_enabled = config.SEARCH_MOCK_ENABLED

    def search_template(self, query: str) -> Optional[str]:
        """
        Ищет подходящий шаблон мема и возвращает URL первого результата.
        """
        return self._search_template_cached(query, self.api_key, self.mock_enabled, self.API_URL)

    @staticmethod
    @lru_cache(maxsize=128)
    def _search_template_cached(query: str, api_key: str, mock_enabled: bool, api_url: str) -> Optional[str]:
        """
        Кешированная реализация поиска.
        """
        if mock_enabled:
            print(f"Search: Используется мок-режим для запроса '{query}'.")
            # Ссылка на простой шаблон для тестирования
            return "https://placehold.co/600x400.png" 

        payload = {
            "api_key": api_key,
            "query": query,
            "search_depth": "basic",
            "include_images": True,
            "include_answer": False,
            "include_raw_content": False,
            "max_results": 1
        }

        try:
            response = requests.post(api_url, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Tavily returns a list of image URLs in the 'images' field
            if 'images' in data and data['images']:
                # Возвращаем прямую ссылку на изображение
                # data['images'] is a list of strings (URLs)
                return data['images'][0]
            
            print(f"Search: Результаты для '{query}' не найдены.")
            return None

        except requests.exceptions.RequestException as e:
            # 🛡️ Sentinel: Sanitize error logs to prevent API key leakage
            status_code = getattr(e.response, 'status_code', 'N/A')
            error_type = type(e).__name__
            # Tavily keys are in the body, but good to be safe about URL params anyway
            print(f"Search: Ошибка при запросе к Tavily API ({error_type}, Status: {status_code})")
            return None
