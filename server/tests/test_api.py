import redis

from app import cache, ranking


def post_score(client, headers, score, wave=1, won=False):
    body = {"score": score, "wave_reached": wave, "won": won}
    return client.post("/scores", json=body, headers=headers)


def test_health_endpoint(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_submit_without_key_is_rejected(client):
    assert post_score(client, {}, 100).status_code == 401


def test_submit_with_wrong_key_is_rejected(client, make_user):
    make_user("alice", "real-key")
    assert post_score(client, {"X-API-Key": "wrong-key"}, 100).status_code == 401


def test_submit_with_valid_key_saves_score_under_the_account_name(client, make_user):
    headers = make_user("alice", "key-a")
    response = post_score(client, headers, 1200, wave=4)
    assert response.status_code == 201
    assert response.json()["player_name"] == "alice"
    assert response.json()["score"] == 1200


def test_invalid_scores_are_rejected(client, make_user):
    headers = make_user("alice", "key-a")
    assert post_score(client, headers, -5).status_code == 422
    assert post_score(client, headers, 5_000_000).status_code == 422
    assert post_score(client, headers, 100, wave=99).status_code == 422


def test_long_usernames_are_cut_to_twenty_characters(client, make_user):
    headers = make_user("a_very_long_username_over_twenty_chars", "key-a")
    assert post_score(client, headers, 100).json()["player_name"] == "a_very_long_username"


def test_leaderboard_ranks_players_by_best_score(client, make_user):
    alice = make_user("alice", "key-a")
    bob = make_user("bob", "key-b")
    post_score(client, alice, 500)
    post_score(client, bob, 900)
    post_score(client, alice, 300)
    post_score(client, alice, 700)
    board = client.get("/leaderboard").json()
    assert board == [
        {"rank": 1, "player_name": "bob", "score": 900},
        {"rank": 2, "player_name": "alice", "score": 700},
    ]


def test_a_worse_run_does_not_replace_the_best_score(client, make_user):
    alice = make_user("alice", "key-a")
    post_score(client, alice, 800)
    post_score(client, alice, 100)
    assert client.get("/leaderboard").json()[0]["score"] == 800


def test_leaderboard_respects_the_limit(client, make_user):
    for number in range(5):
        headers = make_user(f"player{number}", f"key-{number}")
        post_score(client, headers, 100 * (number + 1))
    board = client.get("/leaderboard?limit=3").json()
    assert [entry["player_name"] for entry in board] == ["player4", "player3", "player2"]
    assert client.get("/leaderboard?limit=0").status_code == 422


def test_leaderboard_falls_back_to_the_database_when_redis_is_empty(client, make_user, fake_redis):
    alice = make_user("alice", "key-a")
    post_score(client, alice, 600)
    fake_redis.flushall()
    assert client.get("/leaderboard").json() == [{"rank": 1, "player_name": "alice", "score": 600}]


def test_leaderboard_stays_complete_when_redis_comes_back_empty(client, make_user, fake_redis):
    alice = make_user("alice", "key-a")
    bob = make_user("bob", "key-b")
    post_score(client, alice, 600)
    fake_redis.flushall()
    post_score(client, bob, 300)
    board = client.get("/leaderboard").json()
    assert [entry["player_name"] for entry in board] == ["alice", "bob"]


class BrokenRedis:
    def __getattr__(self, name):
        def fail(*args, **kwargs):
            raise redis.ConnectionError("redis is down")

        return fail


def test_everything_still_works_when_redis_is_down(client, make_user, monkeypatch):
    alice = make_user("alice", "key-a")
    monkeypatch.setattr(cache, "redis_client", BrokenRedis())
    assert post_score(client, alice, 450).status_code == 201
    assert client.get("/leaderboard").json() == [{"rank": 1, "player_name": "alice", "score": 450}]


def test_rebuild_restores_redis_from_the_database(client, make_user, db_session, fake_redis):
    alice = make_user("alice", "key-a")
    post_score(client, alice, 250)
    fake_redis.flushall()
    ranking.rebuild(db_session)
    assert fake_redis.zcard(cache.LEADERBOARD_KEY) == 1