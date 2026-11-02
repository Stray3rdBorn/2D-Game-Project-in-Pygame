import os

# Must be set before the app is imported: the tests never touch a real database
os.environ["DATABASE_URL"] = "sqlite://"

import fakeredis  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app import cache, models  # noqa: E402
from app.database import Base, DjangoBase, get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    DjangoBase.metadata.create_all(engine)
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
def make_user(db_session):
    def _make(username, key):
        user = models.DjangoUser(username=username)
        db_session.add(user)
        db_session.commit()
        db_session.add(models.ApiKey(user_id=user.id, key=key))
        db_session.commit()
        return {"X-API-Key": key}

    return _make