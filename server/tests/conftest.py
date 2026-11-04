import os
from datetime import datetime, timedelta, timezone

# Must be set before the app is imported: the tests never touch a real database
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["JWT_SECRET"] = "test-jwt-secret-that-is-long-enough-for-hs256"

import fakeredis  # noqa: E402
import jwt  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app import cache  # noqa: E402
from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402  (loads Django, so Django imports must come after)

from django.core.management import call_command  # noqa: E402
from django.test import Client  # noqa: E402
from django.test.utils import setup_test_environment  # noqa: E402


setup_test_environment()


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


@pytest.fixture
def fake_redis(monkeypatch):
    fake = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(cache, "redis_client", fake)
    return fake


@pytest.fixture
def client(db_session, fake_redis):
    app.dependency_overrides[get_db] = lambda: db_session
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def make_user():
    def _make(user_id, username, lifetime=timedelta(days=1), secret=os.environ["JWT_SECRET"]):
        now = datetime.now(timezone.utc)
        claims = {"sub": str(user_id), "username": username, "iat": now, "exp": now + lifetime}
        token = jwt.encode(claims, secret, algorithm="HS256")
        return {"Authorization": f"Bearer {token}"}

    return _make


@pytest.fixture
def django_db():
    call_command("migrate", verbosity=0)
    yield
    call_command("flush", verbosity=0, interactive=False)


@pytest.fixture
def django_client(django_db):
    return Client()