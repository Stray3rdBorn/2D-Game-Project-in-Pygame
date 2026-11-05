import base64
import json
import os
import time
from pathlib import Path

SESSION_FILE = Path(os.getenv("APPDATA") or Path.home()) / "ArenaSurvival" / "session.json"


def token_expiry(token):
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        return int(json.loads(base64.urlsafe_b64decode(payload))["exp"])
    except (AttributeError, IndexError, KeyError, TypeError, ValueError):
        return None


def save_session(token, username):
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    temp_file = SESSION_FILE.with_suffix(".tmp")
    temp_file.write_text(json.dumps({"token": token, "username": username}))
    os.chmod(temp_file, 0o600)
    temp_file.replace(SESSION_FILE)


def clear_session():
    try:
        SESSION_FILE.unlink()
    except OSError:
        pass


def load_session():
    try:
        data = json.loads(SESSION_FILE.read_text())
        token, username = data["token"], data["username"]
    except (OSError, KeyError, TypeError, ValueError):
        return None
    expiry = token_expiry(token)
    if not isinstance(username, str) or expiry is None or expiry <= time.time():
        clear_session()
        return None
    return {"token": token, "username": username}


class Session:
    def __init__(self):
        saved = load_session()
        self.token = saved["token"] if saved else None
        self.username = saved["username"] if saved else None

    @property
    def logged_in(self):
        return self.token is not None

    def login(self, token, username):
        self.token = token
        self.username = username
        try:
            save_session(token, username)
        except OSError:
            pass

    def logout(self):
        clear_session()
        self.token = None
        self.username = None