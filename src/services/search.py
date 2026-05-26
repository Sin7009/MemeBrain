import requests
import logging
from typing import Optional
from functools import lru_cache
from .config import config

class ImageSearcher:
    """
    Сервис поиска картинок через Tavily API.
    """

    def __init__(self):
        self.api_key = config.TAVILY_API_KEY
        self.mock_enabled = config.SEARCH_MOCK_ENABLED

    def search_template(self, query: str) -> Optional[str]:
        """
        Ищет подходящий шаблон мема и возвращает URL первого результата.
        """
        return self._search_template_cached(query, self.api_key, self.mock_enabled, config.TAVILY_API_URL)

    @staticmethod
    @lru_cache(maxsize=128)
    def _search_template_cached(query: str, api_key: str, mock_enabled: bool, api_url: str) -> Optional[str]:
        """
        Кешированная реализация поиска.
        """
        if mock_enabled:
            logging.info("Search: Используется мок-режим для запроса '%s'.", query)
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

            # Tavily возвращает список URL картинок в поле 'images'
            if 'images' in data and data['images']:
                return data['images'][0]
            
            logging.warning("Search: Результаты для '%s' не найдены.", query)
            return None

        except requests.exceptions.RequestException as e:
            # 🛡️ Sentinel: Очистка логов ошибок для предотвращения утечки API ключей
            status_code = getattr(e.response, 'status_code', 'N/A')
            error_type = type(e).__name__
            logging.error("Search: Ошибка при запросе к Tavily API (%s, Status: %s)", error_type, status_code)
            return None
