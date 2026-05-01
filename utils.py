import requests
import time
import random

HEADERS = {"User-Agent": "Mozilla/5.0"}

def safe_get(url):
    for _ in range(3):
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code == 200:
                return r
        except:
            time.sleep(2)
    return None

def sleep_jitter(base=0.6):
    time.sleep(base + random.random())
