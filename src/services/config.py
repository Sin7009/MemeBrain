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
    SEARCH_MOCK_ENABLED: bool = False
    
    # Cache Settings
    CACHE_ENABLED: bool = True
    CACHE_DIR: str = "./cache/templates"
    CACHE_TTL: int = 86400  # 24 часа в секундах
    
    # Face Swap
    FACE_SWAP_ENABLED: bool = False
    
    # History
    HISTORY_SIZE: int = 10 # Сколько сообщений хранить
    
    # Database Settings
    DATABASE_URL: str = ""  # Пустая строка = использовать in-memory
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    
    # Metrics Settings
    METRICS_ENABLED: bool = False
    METRICS_PORT: int = 9090

config = Settings()
