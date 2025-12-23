import requests
from typing import Optional
from .config import config
import hashlib
import os
import time
import logging
from pathlib import Path

class ImageSearcher:
    """
    Сервис поиска картинок через Tavily API с поддержкой кэширования.
    """
    API_URL = "https://api.tavily.com/search"

    def __init__(self):
        self.api_key = config.TAVILY_API_KEY
        self.mock_enabled = config.SEARCH_MOCK_ENABLED
        self.cache_enabled = config.CACHE_ENABLED
        self.cache_dir = config.CACHE_DIR
        self.cache_ttl = config.CACHE_TTL
        
        # Создаем директорию для кэша, если включено кэширование
        if self.cache_enabled:
            os.makedirs(self.cache_dir, exist_ok=True)
            logging.info(f"Template cache enabled at {self.cache_dir}")

    def _get_cache_key(self, query: str) -> str:
        """Генерирует ключ кэша на основе поискового запроса."""
        return hashlib.md5(query.encode()).hexdigest()

    def _get_cached_url(self, cache_key: str) -> Optional[str]:
        """Проверяет наличие URL в кэше и его актуальность."""
        if not self.cache_enabled:
            return None
            
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.txt")
        
        if not os.path.exists(cache_file):
            return None
        
        # Проверяем TTL
        file_age = time.time() - os.path.getmtime(cache_file)
        if file_age > self.cache_ttl:
            logging.info(f"Cache expired for {cache_key}")
            try:
                os.remove(cache_file)
            except Exception as e:
                logging.error(f"Failed to remove expired cache file: {e}")
            return None
        
        # Читаем URL из кэша
        try:
            with open(cache_file, 'r') as f:
                url = f.read().strip()
                logging.info(f"Cache hit for query (key: {cache_key})")
                return url
        except Exception as e:
            logging.error(f"Failed to read cache file: {e}")
            return None

    def _save_to_cache(self, cache_key: str, url: str):
        """Сохраняет URL в кэш."""
        if not self.cache_enabled:
            return
            
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.txt")
        
        try:
            with open(cache_file, 'w') as f:
                f.write(url)
            logging.info(f"Saved to cache: {cache_key}")
        except Exception as e:
            logging.error(f"Failed to save to cache: {e}")

    def search_template(self, query: str) -> Optional[str]:
        """
        Ищет подходящий шаблон мема и возвращает URL первого результата.
        Использует кэш для повторных запросов.
        """
        if self.mock_enabled:
            logging.info(f"Search: Используется мок-режим для запроса '{query}'.")
            # Ссылка на простой шаблон для тестирования
            return "https://placehold.co/600x400.png" 

        # Проверяем кэш
        cache_key = self._get_cache_key(query)
        cached_url = self._get_cached_url(cache_key)
        if cached_url:
            return cached_url

        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "basic",
            "include_images": True,
            "include_answer": False,
            "include_raw_content": False,
            "max_results": 1
        }

        try:
            response = requests.post(self.API_URL, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Tavily returns a list of image URLs in the 'images' field
            if 'images' in data and data['images']:
                # Возвращаем прямую ссылку на изображение
                # data['images'] is a list of strings (URLs)
                url = data['images'][0]
                
                # Сохраняем в кэш
                self._save_to_cache(cache_key, url)
                
                return url
            
            logging.info(f"Search: Результаты для '{query}' не найдены.")
            return None

        except requests.exceptions.RequestException as e:
            # 🛡️ Sentinel: Sanitize error logs to prevent API key leakage
            status_code = getattr(e.response, 'status_code', 'N/A')
            error_type = type(e).__name__
            # Tavily keys are in the body, but good to be safe about URL params anyway
            logging.error(f"Search: Ошибка при запросе к Tavily API ({error_type}, Status: {status_code})")
            return None
