import base64
import json
import time

import pytest

import storage


def make_token(expires_in):
    payload = json.dumps({"sub": "1", "username": "alice", "exp": int(time.time() + expires_in)})
    body = base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")
    return f"header.{body}.signature"


@pytest.fixture(autouse=True)
def temp_session_file(tmp_path, monkeypatch):
    # Tests must never touch the real session file
    monkeypatch.setattr(storage, "SESSION_FILE", tmp_path / "DecaDome" / "session.json")


def test_token_expiry_reads_the_exp_claim():
    token = make_token(100)
    assert abs(storage.token_expiry(token) - (time.time() + 100)) < 5


def test_token_expiry_of_garbage_is_none():
    assert storage.token_expiry("garbage") is None
    assert storage.token_expiry("a.b.c") is None
    assert storage.token_expiry(None) is None


def test_saved_session_loads_back():
    token = make_token(3600)
    storage.save_session(token, "alice")
    assert storage.load_session() == {"token": token, "username": "alice"}


def test_expired_session_is_dropped_and_the_file_deleted():
    storage.save_session(make_token(-10), "alice")
    assert storage.load_session() is None
    assert not storage.SESSION_FILE.exists()


def test_missing_corrupted_or_wrong_shape_files_give_no_session():
    assert storage.load_session() is None
    storage.SESSION_FILE.parent.mkdir(parents=True)
    storage.SESSION_FILE.write_text("not json")
    assert storage.load_session() is None
    storage.SESSION_FILE.write_text(json.dumps({"token": 5, "username": "alice"}))
    assert storage.load_session() is None
    storage.SESSION_FILE.write_text(json.dumps([1, 2]))
    assert storage.load_session() is None


def test_clear_session_works_even_when_there_is_no_file():
    storage.clear_session()
    storage.save_session(make_token(3600), "alice")
    storage.clear_session()
    assert not storage.SESSION_FILE.exists()


def test_the_password_is_never_written_to_the_file():
    storage.save_session(make_token(3600), "alice")
    assert set(json.loads(storage.SESSION_FILE.read_text())) == {"token", "username"}


def test_session_object_login_and_logout():
    session = storage.Session()
    assert not session.logged_in
    token = make_token(3600)
    session.login(token, "alice")
    assert session.logged_in
    assert storage.Session().username == "alice"
    session.logout()
    assert not session.logged_in
    assert not storage.Session().logged_in