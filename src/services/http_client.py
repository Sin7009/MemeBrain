import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def _create_session() -> requests.Session:
    """
    Создает и настраивает requests.Session с пулом соединений и повторными попытками.
    """
    session = requests.Session()

    # Стратегия повторных попыток
    retry_strategy = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
    )

    # Адаптер для пулинга соединений
    # pool_connections: количество хостов, для которых мы храним соединение
    # pool_maxsize: количество соединений к одному хосту
    adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=10)

    session.mount("https://", adapter)
    session.mount("http://", adapter)

    return session

# Глобальный синглтон сессии для использования во всем приложении
http_session = _create_session()
