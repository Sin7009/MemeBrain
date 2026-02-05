import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session() -> requests.Session:
    """
    Creates a requests Session with retry logic and connection pooling.
    """
    session = requests.Session()

    # Define retry strategy
    retry_strategy = Retry(
        total=3,  # Total number of retries
        backoff_factor=0.5,  # Wait 0.5s, 1s, 2s...
        status_forcelist=[500, 502, 503, 504],  # Retry on these status codes
        allowed_methods=["HEAD", "GET", "OPTIONS", "POST"] # Retry on these methods
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)

    # Mount adapter for both http and https
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session

# Singleton session instance to be used throughout the application
http_session = create_session()
