import time
import random
import requests

def make_session(user_agent: str) -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": user_agent})
    return s

def get_with_retries(session: requests.Session, url: str, timeout: int = 30, retries: int = 5, backoff: float = 1.5):
    last_err = None
    for i in range(retries):
        try:
            r = session.get(url, timeout=timeout)
            r.raise_for_status()
            return r
        except Exception as e:
            last_err = e
            sleep_s = (backoff ** i) + random.random() * 0.25
            time.sleep(sleep_s)
    raise last_err

def rate_limit(seconds: float):
    if seconds > 0:
        time.sleep(seconds)
