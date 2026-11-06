import importlib.util

import pytest

from config import settings


@pytest.fixture
def load_settings(monkeypatch):
    # load a fresh copy of the settings file with different environment values and look at the result
    def _load(**env):
        for name in ("DEBUG", "ALLOWED_HOSTS", "CSRF_TRUSTED_ORIGINS", "DATABASE_URL"):
            monkeypatch.delenv(name, raising=False)
        for name, value in env.items():
            monkeypatch.setenv(name, value)
        spec = importlib.util.spec_from_file_location("settings_under_test", settings.__file__)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    return _load


def test_debug_is_off_unless_asked_for(load_settings):
    assert load_settings(DATABASE_URL="sqlite://").DEBUG is False
    assert load_settings(DATABASE_URL="sqlite://", DEBUG="0").DEBUG is False
    assert load_settings(DATABASE_URL="sqlite://", DEBUG="1").DEBUG is True


def test_a_real_server_gets_the_https_protections(load_settings):
    loaded = load_settings(DATABASE_URL="sqlite://")
    assert loaded.SESSION_COOKIE_SECURE is True
    assert loaded.CSRF_COOKIE_SECURE is True
    assert loaded.SECURE_HSTS_SECONDS >= 31536000
    assert loaded.SECURE_PROXY_SSL_HEADER == ("HTTP_X_FORWARDED_PROTO", "https")


def test_debug_mode_on_my_computer_skips_the_https_protections(load_settings):
    loaded = load_settings(DATABASE_URL="sqlite://", DEBUG="1")
    assert not hasattr(loaded, "SESSION_COOKIE_SECURE")
    assert not hasattr(loaded, "SECURE_HSTS_SECONDS")


def test_allowed_hosts_default_to_localhost_only(load_settings):
    assert load_settings(DATABASE_URL="sqlite://").ALLOWED_HOSTS == ["localhost", "127.0.0.1"]


def test_allowed_hosts_and_trusted_origins_come_from_the_environment(load_settings):
    loaded = load_settings(
        DATABASE_URL="sqlite://",
        ALLOWED_HOSTS="arena.onrender.com",
        CSRF_TRUSTED_ORIGINS="https://arena.onrender.com,https://other.example.com",
    )
    assert loaded.ALLOWED_HOSTS == ["arena.onrender.com"]
    assert loaded.CSRF_TRUSTED_ORIGINS == ["https://arena.onrender.com", "https://other.example.com"]


def test_no_trusted_origins_means_an_empty_list_not_an_empty_string(load_settings):
    assert load_settings(DATABASE_URL="sqlite://").CSRF_TRUSTED_ORIGINS == []


def test_database_address_options_like_sslmode_reach_the_driver(load_settings):
    url = "postgresql+psycopg://user:pw@host.neon.tech/arena?sslmode=require&channel_binding=require"
    database = load_settings(DATABASE_URL=url).DATABASES["default"]
    assert database["OPTIONS"] == {"sslmode": "require", "channel_binding": "require"}
    assert database["HOST"] == "host.neon.tech"
    assert database["NAME"] == "arena"


def test_database_address_without_options_gives_empty_options(load_settings):
    url = "postgresql+psycopg://user:pw@localhost:5432/arena"
    assert load_settings(DATABASE_URL=url).DATABASES["default"]["OPTIONS"] == {}