import requests
from typing import Optional
from functools import lru_cache
from .config import config
import urllib.parse

class ContentSearcher:
    """
    Универсальный сервис поиска контента (Картинки, GIF, Видео).
    """
    TAVILY_API_URL = "https://api.tavily.com/search"
    GIPHY_API_URL = "https://api.giphy.com/v1/gifs/search"

    def __init__(self):
        self.tavily_api_key = config.TAVILY_API_KEY
        self.giphy_api_key = config.GIPHY_API_KEY
        self.mock_enabled = config.SEARCH_MOCK_ENABLED

    def search_image(self, query: str) -> Optional[str]:
        """
        Ищет картинку через Tavily API.
        """
        return self._search_image_cached(query, self.tavily_api_key, self.mock_enabled, self.TAVILY_API_URL)

    def search_gif(self, query: str) -> Optional[str]:
        """
        Ищет GIF через Giphy API.
        """
        if not self.giphy_api_key:
            print("Search: GIPHY_API_KEY не установлен.")
            return None

        return self._search_gif_cached(query, self.giphy_api_key, self.mock_enabled, self.GIPHY_API_URL)

    def search_video(self, query: str) -> str:
        """
        Генерирует ссылку на поиск YouTube.
        TODO: В будущем реализовать скачивание через yt-dlp.
        """
        encoded_query = urllib.parse.quote(query)
        return f"https://www.youtube.com/results?search_query={encoded_query}"

    @staticmethod
    @lru_cache(maxsize=128)
    def _search_image_cached(query: str, api_key: str, mock_enabled: bool, api_url: str) -> Optional[str]:
        """
        Кешированная реализация поиска картинок (Tavily).
        """
        if mock_enabled:
            print(f"Search (Image): Mock mode for '{query}'.")
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

            if 'images' in data and data['images']:
                return data['images'][0]
            
            print(f"Search (Image): Ничего не найдено по запросу '{query}'.")
            return None

        except requests.exceptions.RequestException as e:
            print(f"Search (Image): Ошибка API ({e})")
            return None

    @staticmethod
    @lru_cache(maxsize=128)
    def _search_gif_cached(query: str, api_key: str, mock_enabled: bool, api_url: str) -> Optional[str]:
        """
        Кешированная реализация поиска GIF (Giphy).
        """
        if mock_enabled:
            print(f"Search (GIF): Mock mode for '{query}'.")
            return "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExbXgxbWJ1ZWF1M3YxeHl5Z3lxYnZyeXJ6YnZyeXJ6YnZyeXJ6YnZyeXJ6JmN0PWc/3o7TKSjRrfIPjeiVyM/giphy.gif"

        params = {
            "api_key": api_key,
            "q": query,
            "limit": 1,
            "offset": 0,
            "rating": "pg-13",
            "lang": "en",
            "bundle": "messaging_non_clips"
        }

        try:
            response = requests.get(api_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get('data') and len(data['data']) > 0:
                # Берем оригинальный MP4 или GIF
                # Лучше использовать 'original' -> 'url'
                return data['data'][0]['images']['original']['url']

            print(f"Search (GIF): Ничего не найдено по запросу '{query}'.")
            return None

        except requests.exceptions.RequestException as e:
            print(f"Search (GIF): Ошибка API ({e})")
            return None
