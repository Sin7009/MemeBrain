"""
Модуль для экспорта метрик в Prometheus.
Собирает статистику по работе бота и генерации мемов.
"""

from prometheus_client import Counter, Histogram, Gauge, start_http_server
import logging
from .config import config
import time

# Определяем метрики
try:
    from prometheus_client import REGISTRY
    
    # Счетчики
    meme_generations_total = Counter(
        'meme_generations_total',
        'Total number of meme generation attempts',
        ['status', 'trigger_emoji']  # status: success, failed, skipped
    )
    
    messages_processed_total = Counter(
        'messages_processed_total',
        'Total number of messages processed',
        ['chat_type']  # chat_type: private, group, supergroup
    )
    
    reactions_received_total = Counter(
        'reactions_received_total',
        'Total number of reactions received',
        ['emoji']
    )
    
    api_calls_total = Counter(
        'api_calls_total',
        'Total number of API calls',
        ['service', 'status']  # service: llm, search, telegram; status: success, failed
    )
    
    # Гистограммы для времени выполнения
    meme_generation_duration = Histogram(
        'meme_generation_duration_seconds',
        'Time taken to generate a meme',
        ['stage']  # stage: llm, search, image_gen, total
    )
    
    # Gauges для текущего состояния
    active_chats = Gauge(
        'active_chats',
        'Number of active chats'
    )
    
    cache_size = Gauge(
        'cache_size_entries',
        'Number of entries in template cache'
    )
    
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    logging.warning("prometheus_client not available. Metrics disabled.")

class MetricsService:
    """
    Сервис для сбора и экспорта метрик.
    """
    
    def __init__(self):
        self.enabled = config.METRICS_ENABLED and METRICS_AVAILABLE
        self.server_started = False
        
        if config.METRICS_ENABLED and not METRICS_AVAILABLE:
            logging.error("Metrics enabled in config but prometheus_client not installed")
            logging.error("Install: pip install prometheus-client")
        elif self.enabled:
            logging.info(f"Metrics service enabled on port {config.METRICS_PORT}")
        else:
            logging.info("Metrics service disabled")
    
    def start_server(self):
        """Запуск HTTP-сервера для экспорта метрик."""
        if not self.enabled or self.server_started:
            return
            
        try:
            start_http_server(config.METRICS_PORT)
            self.server_started = True
            logging.info(f"Metrics server started on port {config.METRICS_PORT}")
            logging.info(f"Access metrics at http://localhost:{config.METRICS_PORT}/metrics")
        except Exception as e:
            logging.error(f"Failed to start metrics server: {e}")
            self.enabled = False
    
    # Методы для записи метрик
    
    def record_meme_generation(self, status: str, trigger_emoji: str = "unknown"):
        """Запись попытки генерации мема."""
        if not self.enabled:
            return
        try:
            meme_generations_total.labels(status=status, trigger_emoji=trigger_emoji).inc()
        except Exception as e:
            logging.error(f"Failed to record meme generation metric: {e}")
    
    def record_message_processed(self, chat_type: str):
        """Запись обработанного сообщения."""
        if not self.enabled:
            return
        try:
            messages_processed_total.labels(chat_type=chat_type).inc()
        except Exception as e:
            logging.error(f"Failed to record message metric: {e}")
    
    def record_reaction(self, emoji: str):
        """Запись полученной реакции."""
        if not self.enabled:
            return
        try:
            reactions_received_total.labels(emoji=emoji).inc()
        except Exception as e:
            logging.error(f"Failed to record reaction metric: {e}")
    
    def record_api_call(self, service: str, status: str):
        """Запись API-вызова."""
        if not self.enabled:
            return
        try:
            api_calls_total.labels(service=service, status=status).inc()
        except Exception as e:
            logging.error(f"Failed to record API call metric: {e}")
    
    def record_generation_duration(self, stage: str, duration: float):
        """Запись времени выполнения этапа генерации."""
        if not self.enabled:
            return
        try:
            meme_generation_duration.labels(stage=stage).observe(duration)
        except Exception as e:
            logging.error(f"Failed to record duration metric: {e}")
    
    def set_active_chats(self, count: int):
        """Установка количества активных чатов."""
        if not self.enabled:
            return
        try:
            active_chats.set(count)
        except Exception as e:
            logging.error(f"Failed to set active chats metric: {e}")
    
    def set_cache_size(self, size: int):
        """Установка размера кэша."""
        if not self.enabled:
            return
        try:
            cache_size.set(size)
        except Exception as e:
            logging.error(f"Failed to set cache size metric: {e}")
    
    def time_stage(self, stage: str):
        """
        Контекстный менеджер для измерения времени выполнения этапа.
        
        Использование:
            with metrics.time_stage('llm'):
                # выполнение кода
        """
        return _TimerContext(self, stage)

class _TimerContext:
    """Вспомогательный класс для измерения времени."""
    
    def __init__(self, metrics_service, stage: str):
        self.metrics_service = metrics_service
        self.stage = stage
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.metrics_service.record_generation_duration(self.stage, duration)
        return False

# Глобальный экземпляр сервиса
metrics_service = MetricsService()
