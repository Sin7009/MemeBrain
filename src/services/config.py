from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Конфигурация проекта, загружаемая из .env файла.
    """
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    # Telegram
    TELEGRAM_BOT_TOKEN: str

    # OpenRouter/LLM
    OPENROUTER_API_KEY: str
    OPENROUTER_MODEL: str = "google/gemini-3-flash-preview"
    LLM_MOCK_ENABLED: bool = False
    
    # Tavily Search
    TAVILY_API_KEY: str
    TAVILY_API_URL: str = "https://api.tavily.com/search"
    SEARCH_MOCK_ENABLED: bool = False
    
    # Face Swap
    FACE_SWAP_ENABLED: bool = False
    
    # History
    HISTORY_SIZE: int = 10 # Сколько сообщений хранить

    # Concurrency
    MAX_CONCURRENT_GENERATIONS: int = 2  # Глобальный лимит параллельных генераций мемов

    # Auto-jokes in groups
    JOKE_AUTO_CHANCE: float = 0.03  # Вероятность авто-анекдота на входящее сообщение
    JOKE_AUTO_COOLDOWN_SECONDS: int = 3600  # Минимальная пауза между авто-анекдотами в чате

    # Agent Memory
    MEMORY_DIR: str = "memory"  # Директория для хранения markdown файлов с историей
    MEMORY_ENABLED: bool = True  # Включить сохранение истории в markdown

def get_settings() -> Settings:
    """Фабрика конфигурации для ленивой инициализации и удобного тестирования."""
    return Settings()  # pyright: ignore[reportCallIssue]


config = get_settings()
