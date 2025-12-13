import requests
from typing import Optional
from .config import config

class ImageSearcher:
    """
    Сервис поиска картинок через Google Custom Search JSON API.
    """
    API_URL = "https://www.googleapis.com/customsearch/v1"

    def __init__(self):
        self.api_key = config.GOOGLE_SEARCH_API_KEY
        self.cx_id = config.GOOGLE_SEARCH_CX_ID
        self.mock_enabled = config.SEARCH_MOCK_ENABLED

    def search_template(self, query: str) -> Optional[str]:
        """
        Ищет подходящий шаблон мема и возвращает URL первого результата.
        """
        if self.mock_enabled:
            print(f"Search: Используется мок-режим для запроса '{query}'.")
            # Ссылка на простой шаблон для тестирования
            # Используем placeholder image service, который стабильнее imgur для тестов
            return "https://placehold.co/600x400.png" 

        params = {
            "key": self.api_key,
            "cx": self.cx_id,
            "q": query,
            "searchType": "image",  # Ищем только изображения
            "num": 1,               # Берем только один результат
            "fileType": "png|jpg|jpeg",
            "safe": "active",       # Умеренная фильтрация
        }

        try:
            response = requests.get(self.API_URL, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()

            # Проверяем наличие результатов
            if 'items' in data and data['items']:
                # Возвращаем прямую ссылку на изображение
                return data['items'][0].get('link')
            
            print(f"Search: Результаты для '{query}' не найдены.")
            return None

        except requests.exceptions.RequestException as e:
            # 🛡️ Sentinel: Sanitize error logs to prevent API key leakage
            # The exception message often contains the full URL with query parameters (including the API key).
            status_code = getattr(e.response, 'status_code', 'N/A')
            error_type = type(e).__name__
            print(f"Search: Ошибка при запросе к Google Search API ({error_type}, Status: {status_code})")
            return None
