import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_http_session() -> requests.Session:
    """
    Creates a shared requests.Session with retry logic and connection pooling.
    This session should be reused across the application to optimize performance.
    """
    session = requests.Session()

    # Configure retry strategy
    retry_strategy = Retry(
        total=3,  # Total number of retries
        backoff_factor=1,  # Wait 1s, 2s, 4s...
        status_forcelist=[429, 500, 502, 503, 504],  # Retry on these status codes
        allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"]
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)

    # Mount adapter for both http and https
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session

# Shared session instance
http_session = create_http_session()
