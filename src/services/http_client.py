import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session() -> requests.Session:
    """
    Creates a requests Session with retry logic and connection pooling.
    """
    session = requests.Session()

    # Configure retry strategy
    # total=3: Total number of retries
    # backoff_factor=0.3: Sleep 0.3s, 0.6s, 1.2s between retries
    # status_forcelist: Retry on these status codes
    retry = Retry(
        total=3,
        read=3,
        connect=3,
        backoff_factor=0.3,
        status_forcelist=(500, 502, 503, 504)
    )

    adapter = HTTPAdapter(max_retries=retry)

    # Mount adapter for both http and https
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    return session

# Global session instance to be reused across the application
http_session = create_session()
