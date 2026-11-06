from datetime import timedelta

import redis

from app import cache, ranking


def post_score(client, headers, score, wave=1, won=False):
    body = {"score": score, "wave_reached": wave, "won": won}
    return client.post("/scores", json=body, headers=headers)


def test_health_endpoint(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_submit_without_token_is_rejected(client):
    assert post_score(client, {}, 100).status_code == 401


def test_submit_with_garbage_token_is_rejected(client):
    assert post_score(client, {"Authorization": "Bearer not-a-token"}, 100).status_code == 401


def test_submit_with_token_signed_by_someone_else_is_rejected(client, make_user):
    headers = make_user(1, "alice", secret="a-different-secret-that-is-long-enough-too")
    assert post_score(client, headers, 100).status_code == 401


def test_submit_with_expired_token_is_rejected(client, make_user):
    headers = make_user(1, "alice", lifetime=timedelta(seconds=-1))
    assert post_score(client, headers, 100).status_code == 401


def test_submit_with_valid_token_saves_score_under_the_account_name(client, make_user):
    response = post_score(client, make_user(1, "alice"), 1200, wave=4)
    assert response.status_code == 201
    assert response.json()["player_name"] == "alice"
    assert response.json()["score"] == 1200


def test_invalid_scores_are_rejected(client, make_user):
    headers = make_user(1, "alice")
    assert post_score(client, headers, -5).status_code == 422
    assert post_score(client, headers, 5_000_000).status_code == 422
    assert post_score(client, headers, 100, wave=99).status_code == 422


def test_long_usernames_are_cut_to_twenty_characters(client, make_user):
    headers = make_user(1, "a_very_long_username_over_twenty_chars")
    assert post_score(client, headers, 100).json()["player_name"] == "a_very_long_username"


def test_leaderboard_ranks_players_by_best_score(client, make_user):
    alice = make_user(1, "alice")
    bob = make_user(2, "bob")
    post_score(client, alice, 500)
    post_score(client, bob, 900)
    post_score(client, alice, 300)
    post_score(client, alice, 700)
    board = client.get("/leaderboard").json()
    assert board["entries"] == [
        {"rank": 1, "player_name": "bob", "score": 900},
        {"rank": 2, "player_name": "alice", "score": 700},
    ]


def test_leaderboard_for_a_guest_has_no_own_row(client, make_user):
    post_score(client, make_user(1, "alice"), 500)
    assert client.get("/leaderboard").json()["me"] is None


def test_leaderboard_for_a_bad_token_is_treated_as_a_guest(client, make_user):
    post_score(client, make_user(1, "alice"), 500)
    response = client.get("/leaderboard", headers={"Authorization": "Bearer not-a-token"})
    assert response.status_code == 200
    assert response.json()["me"] is None


def test_leaderboard_returns_own_row_even_outside_the_top(client, make_user):
    for number in range(1, 6):
        post_score(client, make_user(number, f"player{number}"), 100 * number)
    board = client.get("/leaderboard?limit=2", headers=make_user(1, "player1")).json()
    assert [entry["player_name"] for entry in board["entries"]] == ["player5", "player4"]
    assert board["me"] == {"rank": 5, "player_name": "player1", "score": 100}


def test_leaderboard_own_row_is_empty_before_the_first_run(client, make_user):
    post_score(client, make_user(1, "alice"), 500)
    assert client.get("/leaderboard", headers=make_user(2, "bob")).json()["me"] is None


def test_a_worse_run_does_not_replace_the_best_score(client, make_user):
    alice = make_user(1, "alice")
    post_score(client, alice, 800)
    post_score(client, alice, 100)
    assert client.get("/leaderboard").json()["entries"][0]["score"] == 800


def test_leaderboard_respects_the_limit(client, make_user):
    for number in range(5):
        post_score(client, make_user(number + 1, f"player{number}"), 100 * (number + 1))
    board = client.get("/leaderboard?limit=3").json()["entries"]
    assert [entry["player_name"] for entry in board] == ["player4", "player3", "player2"]
    assert client.get("/leaderboard?limit=0").status_code == 422


def test_me_requires_a_token(client):
    assert client.get("/me").status_code == 401


def test_me_counts_every_run_and_shows_best_score_and_rank(client, make_user):
    alice = make_user(1, "alice")
    post_score(client, make_user(2, "bob"), 900)
    post_score(client, alice, 500)
    post_score(client, alice, 300)
    assert client.get("/me", headers=alice).json() == {
        "username": "alice",
        "total_runs": 2,
        "best_score": 500,
        "rank": 2,
    }


def test_me_before_the_first_run(client, make_user):
    assert client.get("/me", headers=make_user(1, "alice")).json() == {
        "username": "alice",
        "total_runs": 0,
        "best_score": None,
        "rank": None,
    }


def test_leaderboard_falls_back_to_the_database_when_redis_is_empty(client, make_user, fake_redis):
    alice = make_user(1, "alice")
    post_score(client, alice, 600)
    fake_redis.flushall()
    board = client.get("/leaderboard", headers=alice).json()
    assert board["entries"] == [{"rank": 1, "player_name": "alice", "score": 600}]
    assert board["me"] == {"rank": 1, "player_name": "alice", "score": 600}


def test_leaderboard_stays_complete_when_redis_comes_back_empty(client, make_user, fake_redis):
    post_score(client, make_user(1, "alice"), 600)
    fake_redis.flushall()
    post_score(client, make_user(2, "bob"), 300)
    board = client.get("/leaderboard").json()["entries"]
    assert [entry["player_name"] for entry in board] == ["alice", "bob"]


class BrokenRedis:
    def __getattr__(self, name):
        def fail(*args, **kwargs):
            raise redis.ConnectionError("redis is down")

        return fail


def test_everything_still_works_when_redis_is_down(client, make_user, monkeypatch):
    alice = make_user(1, "alice")
    monkeypatch.setattr(cache, "redis_client", BrokenRedis())
    assert post_score(client, alice, 450).status_code == 201
    board = client.get("/leaderboard", headers=alice).json()
    assert board["entries"] == [{"rank": 1, "player_name": "alice", "score": 450}]
    assert board["me"] == {"rank": 1, "player_name": "alice", "score": 450}


def test_rebuild_restores_redis_from_the_database(client, make_user, db_session, fake_redis):
    post_score(client, make_user(1, "alice"), 250)
    fake_redis.flushall()
    ranking.rebuild(db_session)
    assert fake_redis.zcard(cache.LEADERBOARD_KEY) == 1

    

# CORS: which websites may read the API from a browser
def test_my_landing_page_may_read_the_leaderboard(client):
    response = client.get("/leaderboard", headers={"Origin": "https://arena-test.pages.dev"})
    assert response.headers["access-control-allow-origin"] == "https://arena-test.pages.dev"


def test_other_websites_get_no_permission(client):
    response = client.get("/leaderboard", headers={"Origin": "https://evil.example.com"})
    assert "access-control-allow-origin" not in response.headers


def test_cookies_are_never_allowed_across_websites(client):
    response = client.get("/leaderboard", headers={"Origin": "https://arena-test.pages.dev"})
    assert "access-control-allow-credentials" not in response.headers


def test_a_browser_may_not_post_scores_from_another_website(client):
    preflight = client.options(
        "/scores",
        headers={"Origin": "https://arena-test.pages.dev", "Access-Control-Request-Method": "POST"},
    )
    assert preflight.status_code == 400