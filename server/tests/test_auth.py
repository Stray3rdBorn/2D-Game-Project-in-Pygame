import os

import jwt


PASSWORD = "a-strong-pass-77"


def post_json(client, path, data):
    return client.post(path, data=data, content_type="application/json")


def register(client, username="alice"):
    return post_json(client, "/api/register", {"username": username, "password": PASSWORD})


def test_register_returns_a_token_and_the_username(django_client):
    response = register(django_client)
    assert response.status_code == 201
    assert response.json()["username"] == "alice"
    assert response.json()["token"]


def test_register_rejects_a_taken_username(django_client):
    register(django_client)
    response = register(django_client)
    assert response.status_code == 400
    assert "detail" in response.json()


def test_register_rejects_a_weak_password(django_client):
    response = post_json(django_client, "/api/register", {"username": "alice", "password": "123"})
    assert response.status_code == 400


def test_register_rejects_a_missing_or_broken_body(django_client):
    assert django_client.post("/api/register", data="not json", content_type="application/json").status_code == 400
    assert post_json(django_client, "/api/register", {}).status_code == 400


def test_login_with_the_right_password_returns_a_token(django_client):
    register(django_client)
    response = post_json(django_client, "/api/login", {"username": "alice", "password": PASSWORD})
    assert response.status_code == 200
    assert response.json()["username"] == "alice"


def test_login_with_the_wrong_password_is_rejected(django_client):
    register(django_client)
    response = post_json(django_client, "/api/login", {"username": "alice", "password": "wrong"})
    assert response.status_code == 401


def test_login_only_accepts_post(django_client):
    assert django_client.get("/api/login").status_code == 405


def test_token_expires_after_one_day(django_client):
    token = register(django_client).json()["token"]
    claims = jwt.decode(token, os.environ["JWT_SECRET"], algorithms=["HS256"])
    assert claims["exp"] - claims["iat"] == 24 * 60 * 60
    assert claims["username"] == "alice"


def test_a_token_from_django_is_accepted_by_fastapi(django_client, client):
    token = register(django_client).json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    body = {"score": 700, "wave_reached": 1, "won": False}
    assert client.post("/scores", json=body, headers=headers).status_code == 201
    assert client.get("/me", headers=headers).json()["total_runs"] == 1


def test_the_admin_page_is_served_through_fastapi(client):
    response = client.get("/admin/login/")
    assert response.status_code == 200
    assert "Django administration" in response.text