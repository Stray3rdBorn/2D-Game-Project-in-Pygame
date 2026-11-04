import threading
import time

import pytest
import requests

import network


class FakeResponse:
    def __init__(self, status_code, body):
        self.status_code = status_code
        self.ok = status_code < 400
        self.body = body

    def json(self):
        if self.body is None:
            raise ValueError("no json")
        return self.body


class Sent(list):
    """The requests that were sent; .replies holds what the fake server answers."""


@pytest.fixture
def sent(monkeypatch):
    calls = Sent()
    replies = {"response": FakeResponse(200, {"token": "t", "username": "alice"})}

    def fake_request(method, url, **kwargs):
        calls.append({"method": method, "url": url, **kwargs})
        reply = replies["response"]
        if isinstance(reply, Exception):
            raise reply
        return reply

    monkeypatch.setattr(network.requests, "request", fake_request)
    monkeypatch.setattr(network, "API_URL", "http://127.0.0.1:8000")
    calls.replies = replies
    return calls


def test_successful_call_returns_the_data(sent):
    result = network.call("POST", "/api/login", body={"username": "alice", "password": "x"})
    assert result.ok
    assert result.data["token"] == "t"
    assert sent[0]["url"] == "http://127.0.0.1:8000/api/login"
    assert sent[0]["json"] == {"username": "alice", "password": "x"}


def test_token_is_sent_as_a_bearer_header_and_redirects_are_off(sent):
    network.call("GET", "/me", token="abc")
    assert sent[0]["headers"] == {"Authorization": "Bearer abc"}
    assert sent[0]["allow_redirects"] is False
    assert sent[0]["timeout"] == network.TIMEOUT


def test_no_token_means_no_authorization_header(sent):
    network.call("GET", "/leaderboard")
    assert sent[0]["headers"] == {}


def test_401_with_a_token_means_the_session_expired(sent):
    sent.replies["response"] = FakeResponse(401, {"detail": "Invalid or expired token"})
    result = network.call("GET", "/me", token="abc")
    assert not result.ok
    assert result.expired


def test_401_on_login_is_a_wrong_password_not_an_expired_session(sent):
    sent.replies["response"] = FakeResponse(401, {"detail": "Wrong username or password"})
    result = network.call("POST", "/api/login", body={})
    assert not result.expired
    assert result.error == "Wrong username or password"


def test_server_error_text_is_passed_on(sent):
    sent.replies["response"] = FakeResponse(400, {"detail": "A user with that username already exists."})
    assert network.call("POST", "/api/register", body={}).error == "A user with that username already exists."


def test_unreadable_answers_become_a_plain_message(sent):
    sent.replies["response"] = FakeResponse(500, None)
    assert network.call("GET", "/me", token="abc").error == "Server error"
    sent.replies["response"] = FakeResponse(422, {"detail": [{"msg": "bad"}]})
    assert network.call("POST", "/scores", token="abc").error == "Server error"
    sent.replies["response"] = FakeResponse(200, ["not", "a", "dict"])
    assert not network.call("GET", "/leaderboard").ok


def test_a_redirect_is_not_followed_or_trusted(sent):
    sent.replies["response"] = FakeResponse(302, None)
    assert not network.call("POST", "/api/login", body={}).ok


def test_unreachable_server_gives_a_friendly_error(sent):
    sent.replies["response"] = requests.ConnectionError("down")
    assert network.call("GET", "/leaderboard").error == "Cannot reach the server"
    sent.replies["response"] = requests.Timeout("slow")
    assert network.call("GET", "/leaderboard").error == "Cannot reach the server"


def test_plain_http_to_a_real_server_is_refused_before_anything_is_sent(sent, monkeypatch):
    monkeypatch.setattr(network, "API_URL", "http://arena.example.com")
    result = network.call("POST", "/api/login", body={"username": "a", "password": "b"})
    assert not result.ok
    assert sent == []


def test_https_and_localhost_are_allowed():
    assert network.is_safe_url("https://arena.example.com")
    assert network.is_safe_url("http://localhost:8000")
    assert network.is_safe_url("http://127.0.0.1:8000")
    assert not network.is_safe_url("http://arena.example.com")
    assert not network.is_safe_url("ftp://localhost")
    assert not network.is_safe_url("http://localhost.evil.com")


def test_callbacks_run_on_the_calling_thread_when_polled(sent):
    net = network.Network()
    seen = []
    net.login("alice", "x", lambda result: seen.append((result.ok, threading.current_thread())))
    deadline = time.time() + 2
    while not seen and time.time() < deadline:
        net.poll()
        time.sleep(0.01)
    assert seen == [(True, threading.current_thread())]


def test_each_helper_sends_the_right_request(sent):
    net = network.Network()
    done = []
    net.register("alice", "pw", done.append)
    net.login("alice", "pw", done.append)
    net.submit_score("tok", 500, 3, True, done.append)
    net.leaderboard("tok", done.append, limit=5)
    net.me("tok", done.append)
    deadline = time.time() + 2
    while len(done) < 5 and time.time() < deadline:
        net.poll()
        time.sleep(0.01)
    summary = sorted((c["method"], c["url"].replace("http://127.0.0.1:8000", "")) for c in sent)
    assert summary == sorted([
        ("POST", "/api/register"),
        ("POST", "/api/login"),
        ("POST", "/scores"),
        ("GET", "/leaderboard?limit=5"),
        ("GET", "/me"),
    ])
    score_call = next(c for c in sent if c["url"].endswith("/scores"))
    assert score_call["json"] == {"score": 500, "wave_reached": 3, "won": True}