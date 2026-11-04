import os
import queue
import threading
from dataclasses import dataclass
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("ARENA_API_URL", "http://127.0.0.1:8000")
TIMEOUT = 5


@dataclass
class Result:
    ok: bool
    data: dict | None = None
    error: str = ""
    expired: bool = False


def is_safe_url(url):
    parts = urlparse(url)
    return parts.scheme == "https" or (parts.scheme == "http" and parts.hostname in ("127.0.0.1", "localhost"))


def call(method, path, token=None, body=None):
    if not is_safe_url(API_URL):
        return Result(False, error="The server address must use https")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        response = requests.request(
            method, API_URL + path, json=body, headers=headers, timeout=TIMEOUT, allow_redirects=False
        )
    except requests.RequestException:
        return Result(False, error="Cannot reach the server")
    try:
        data = response.json()
    except ValueError:
        data = None
    if response.ok and isinstance(data, dict):
        return Result(True, data)
    if response.status_code == 401 and token:
        return Result(False, error="Session expired, please log in again", expired=True)
    message = data.get("detail") if isinstance(data, dict) else None
    return Result(False, error=message if isinstance(message, str) else "Server error")


class Network:
    def __init__(self):
        self.results = queue.Queue()

    def start(self, callback, function, *args):
        def work():
            self.results.put((callback, function(*args)))

        threading.Thread(target=work, daemon=True).start()

    def poll(self):
        while True:
            try:
                callback, result = self.results.get_nowait()
            except queue.Empty:
                return
            callback(result)

    def register(self, username, password, callback):
        self.start(callback, call, "POST", "/api/register", None, {"username": username, "password": password})

    def login(self, username, password, callback):
        self.start(callback, call, "POST", "/api/login", None, {"username": username, "password": password})

    def submit_score(self, token, score, wave_reached, won, callback):
        body = {"score": score, "wave_reached": wave_reached, "won": won}
        self.start(callback, call, "POST", "/scores", token, body)

    def leaderboard(self, token, callback, limit=10):
        self.start(callback, call, "GET", f"/leaderboard?limit={limit}", token)

    def me(self, token, callback):
        self.start(callback, call, "GET", "/me", token)