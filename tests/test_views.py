import json
import time

import pygame
import pytest

import app
import main
import storage
import views
from network import Result

TOKEN_BODY = {"sub": "1", "username": "alice", "exp": int(time.time()) + 3600}


class FakeNetwork:
    """Records every request. Tests answer them by hand with resolve()."""

    def __init__(self):
        self.calls = []

    def poll(self):
        pass

    def _record(self, name, callback, **details):
        self.calls.append({"name": name, "callback": callback, **details})

    def register(self, username, password, callback):
        self._record("register", callback, username=username, password=password)

    def login(self, username, password, callback):
        self._record("login", callback, username=username, password=password)

    def submit_score(self, token, score, wave_reached, won, callback):
        self._record("submit", callback, token=token, score=score, wave=wave_reached, won=won)

    def leaderboard(self, token, callback, limit=10):
        self._record("leaderboard", callback, token=token)

    def me(self, token, callback):
        self._record("me", callback, token=token)

    def names(self):
        return [call["name"] for call in self.calls]

    def resolve(self, name, result):
        call = [c for c in self.calls if c["name"] == name][-1]
        call["callback"](result)


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "SESSION_FILE", tmp_path / "DecaDome" / "session.json")
    monkeypatch.setattr(main, "HIGHSCORE_FILE", tmp_path / "highscore.json")


@pytest.fixture
def world():
    game = main.Game()
    network = FakeNetwork()
    manager = app.build(game, storage.Session(), network)
    manager.switch("menu")
    yield manager
    pygame.quit()


def good_token():
    import base64
    body = base64.urlsafe_b64encode(json.dumps(TOKEN_BODY).encode()).decode().rstrip("=")
    return f"h.{body}.s"


def login_as(manager, name="alice"):
    manager.session.login(good_token(), name)


def click(widget):
    x, y = widget.rect.center
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(x, y), button=1)


def press(manager, key, character=""):
    manager.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key, unicode=character))


def type_text(manager, text):
    for character in text:
        press(manager, ord(character), character)


def button_named(buttons, text):
    return next(b for b in buttons if b.text == text)


def draw_all(manager):
    surface = pygame.display.get_surface()
    manager.draw(surface)


def ok(**data):
    return Result(True, data)


def entry(rank, name, score):
    return {"rank": rank, "player_name": name, "score": score}


RUN = {"score": 700, "wave": 4, "won": False}


# board rows

def test_board_rows_marks_own_row_inside_the_top_list():
    rows = views.board_rows([entry(1, "bob", 900), entry(2, "alice", 700)], entry(2, "alice", 700))
    assert [row["mine"] for row in rows] == [False, True]


def test_board_rows_adds_a_separator_and_own_row_when_outside_the_top_list():
    entries = [entry(n, f"p{n}", 1000 - n) for n in range(1, 11)]
    rows = views.board_rows(entries, entry(37, "alice", 120))
    assert len(rows) == 12
    assert rows[10] is None
    assert rows[11] == {"rank": 37, "name": "alice", "score": 120, "mine": True}


def test_board_rows_for_a_guest_has_no_highlight_and_no_separator():
    rows = views.board_rows([entry(1, "bob", 900)], None)
    assert rows == [{"rank": 1, "name": "bob", "score": 900, "mine": False}]


def test_two_players_with_the_same_name_are_told_apart_by_rank():
    rows = views.board_rows([entry(1, "sam", 900), entry(2, "sam", 800)], entry(2, "sam", 800))
    assert [row["mine"] for row in rows] == [False, True]


def test_malformed_server_data_gives_no_rows_instead_of_crashing():
    assert views.rows_from({}) is None
    assert views.rows_from({"entries": [{"rank": 1}]}) is None
    assert views.rows_from({"entries": None}) is None


# menu

def test_menu_for_a_guest_offers_login_and_register(world):
    labels = [b.text for b in world.current.buttons]
    assert labels == ["Start Game", "Log in", "Register", "Leaderboard"]


def test_menu_for_a_logged_in_player_offers_dashboard_and_logout(world):
    login_as(world)
    world.switch("menu")
    assert [b.text for b in world.current.buttons] == ["Start Game", "Dashboard", "Leaderboard", "Log out"]


def test_menu_buttons_switch_screens(world):
    world.handle_event(click(button_named(world.current.buttons, "Register")))
    assert world.current is world.screens["register"]


def test_logout_forgets_the_session_and_any_unsaved_run(world):
    login_as(world)
    world.pending_run = dict(RUN)
    world.switch("menu")
    world.handle_event(click(button_named(world.current.buttons, "Log out")))
    assert not world.session.logged_in
    assert world.pending_run is None
    assert not storage.SESSION_FILE.exists()


# login and register screens

def test_empty_fields_are_not_sent(world):
    world.switch("login")
    press(world, pygame.K_RETURN)
    assert world.network.calls == []
    assert "Enter" in world.current.message


def test_login_sends_the_typed_values_and_locks_the_button(world):
    world.switch("login")
    type_text(world, "alice")
    press(world, pygame.K_TAB)
    type_text(world, "secret-pass-1")
    press(world, pygame.K_RETURN)
    call = world.network.calls[0]
    assert (call["name"], call["username"], call["password"]) == ("login", "alice", "secret-pass-1")
    assert world.current.submit.enabled is False
    assert world.current.password.text == ""


def test_a_second_submit_while_waiting_sends_nothing(world):
    world.switch("login")
    type_text(world, "alice")
    press(world, pygame.K_TAB)
    type_text(world, "pw")
    press(world, pygame.K_RETURN)
    type_text(world, "pw")
    press(world, pygame.K_RETURN)
    assert world.network.names() == ["login"]


def test_successful_login_stores_the_session_and_opens_the_menu(world):
    world.switch("login")
    type_text(world, "alice")
    press(world, pygame.K_TAB)
    type_text(world, "pw")
    press(world, pygame.K_RETURN)
    world.network.resolve("login", ok(token=good_token(), username="alice"))
    assert world.session.logged_in
    assert storage.SESSION_FILE.exists()
    assert world.current is world.screens["menu"]


def test_failed_login_shows_the_error_and_unlocks_the_button(world):
    world.switch("login")
    type_text(world, "alice")
    press(world, pygame.K_TAB)
    type_text(world, "pw")
    press(world, pygame.K_RETURN)
    world.network.resolve("login", Result(False, error="Wrong username or password"))
    assert world.current.message == "Wrong username or password"
    assert world.current.submit.enabled
    assert not world.session.logged_in


def test_a_strange_server_answer_does_not_log_anyone_in(world):
    world.switch("login")
    type_text(world, "alice")
    press(world, pygame.K_TAB)
    type_text(world, "pw")
    press(world, pygame.K_RETURN)
    world.network.resolve("login", ok(something="else"))
    assert not world.session.logged_in
    assert world.current is world.screens["login"]


def test_an_answer_that_arrives_after_pressing_back_is_ignored(world):
    world.switch("login")
    type_text(world, "alice")
    press(world, pygame.K_TAB)
    type_text(world, "pw")
    press(world, pygame.K_RETURN)
    press(world, pygame.K_ESCAPE)
    world.network.resolve("login", ok(token=good_token(), username="alice"))
    assert not world.session.logged_in
    assert world.current is world.screens["menu"]


def test_register_limits_the_username_to_twenty_characters(world):
    world.switch("register")
    type_text(world, "a" * 30)
    assert len(world.current.username.text) == 20
    world.switch("login")
    type_text(world, "a" * 30)
    assert len(world.current.username.text) == 30


def test_register_uses_the_register_request(world):
    world.switch("register")
    type_text(world, "alice")
    press(world, pygame.K_TAB)
    type_text(world, "pw")
    press(world, pygame.K_RETURN)
    assert world.network.names() == ["register"]


def test_tab_moves_focus_between_the_two_boxes(world):
    world.switch("login")
    assert world.current.username.focused
    press(world, pygame.K_TAB)
    assert world.current.password.focused and not world.current.username.focused
    press(world, pygame.K_TAB)
    assert world.current.username.focused


def test_the_login_screen_shows_the_message_it_was_given(world):
    world.switch("login", message="Session expired, please log in again")
    assert world.current.message == "Session expired, please log in again"


def test_a_failed_session_file_write_does_not_crash_login(world, monkeypatch):
    def broken(*args):
        raise PermissionError("no")

    monkeypatch.setattr(storage, "save_session", broken)
    world.session.login(good_token(), "alice")
    assert world.session.logged_in


# leaderboard and dashboard

def test_leaderboard_screen_requests_the_board_with_the_token_and_shows_rows(world):
    login_as(world)
    world.switch("leaderboard")
    assert world.network.calls[0]["token"] == world.session.token
    world.network.resolve("leaderboard", ok(entries=[entry(1, "bob", 900)], me=entry(1, "bob", 900)))
    assert len(world.current.rows) == 1
    draw_all(world)


def test_leaderboard_screen_works_for_guests(world):
    world.switch("leaderboard")
    assert world.network.calls[0]["token"] is None
    world.network.resolve("leaderboard", ok(entries=[], me=None))
    assert world.current.status == "No scores yet"


def test_leaderboard_screen_shows_the_error_when_the_server_is_down(world):
    world.switch("leaderboard")
    world.network.resolve("leaderboard", Result(False, error="Cannot reach the server"))
    assert world.current.status == "Cannot reach the server"
    draw_all(world)


def test_dashboard_shows_runs_best_score_and_rank(world):
    login_as(world)
    world.switch("dashboard")
    world.network.resolve("me", ok(username="alice", total_runs=7, best_score=900, rank=2))
    assert world.current.lines == ["alice", "Total runs: 7", "Best score: 900", "Rank: #2"]
    draw_all(world)


def test_dashboard_for_a_new_account(world):
    login_as(world)
    world.switch("dashboard")
    world.network.resolve("me", ok(username="alice", total_runs=0, best_score=None, rank=None))
    assert world.current.lines[2:] == ["Best score: no runs yet", "Rank: unranked"]


def test_dashboard_with_an_expired_token_logs_out_and_opens_login(world):
    login_as(world)
    world.switch("dashboard")
    world.network.resolve("me", Result(False, error="Session expired, please log in again", expired=True))
    assert not world.session.logged_in
    assert world.current is world.screens["login"]
    assert "expired" in world.current.message


# game over

def test_a_guest_run_is_kept_not_sent_and_the_player_is_asked_to_log_in(world):
    world.switch("game_over", run=dict(RUN))
    assert world.network.names() == ["leaderboard"]
    assert world.pending_run == RUN
    assert "Log in or register" in world.current.status
    labels = [b.text for b in world.current.visible_buttons()]
    assert labels == ["Play again", "Menu", "Log in", "Register"]
    draw_all(world)


def test_a_logged_in_run_is_submitted_once_with_the_token_and_values(world):
    login_as(world)
    world.switch("game_over", run=dict(RUN))
    submits = [c for c in world.network.calls if c["name"] == "submit"]
    assert len(submits) == 1
    assert (submits[0]["score"], submits[0]["wave"], submits[0]["won"]) == (700, 4, False)
    assert submits[0]["token"] == world.session.token


def test_after_the_run_is_saved_the_board_is_loaded_and_the_run_is_no_longer_pending(world):
    login_as(world)
    world.switch("game_over", run=dict(RUN))
    world.network.resolve("submit", ok(id=1))
    assert world.pending_run is None
    assert world.current.status == "Run saved"
    world.network.resolve("leaderboard", ok(entries=[entry(1, "alice", 700)], me=entry(1, "alice", 700)))
    assert world.current.rows[0]["mine"]
    draw_all(world)


def test_game_over_shows_the_separator_and_own_row_outside_the_top_ten(world):
    login_as(world)
    world.switch("game_over", run=dict(RUN))
    world.network.resolve("submit", ok(id=1))
    entries = [entry(n, f"p{n}", 5000 - n) for n in range(1, 11)]
    world.network.resolve("leaderboard", ok(entries=entries, me=entry(42, "alice", 700)))
    assert world.current.rows[10] is None
    assert world.current.rows[11]["rank"] == 42
    draw_all(world)


def test_an_expired_session_during_saving_keeps_the_run_and_asks_for_login(world):
    login_as(world)
    world.switch("game_over", run=dict(RUN))
    world.network.resolve("submit", Result(False, error="Session expired", expired=True))
    assert not world.session.logged_in
    assert world.pending_run == RUN
    assert "Log in" in world.current.status
    assert "Log in" in [b.text for b in world.current.visible_buttons()]


def test_a_network_failure_keeps_the_run_and_offers_a_retry(world):
    login_as(world)
    world.switch("game_over", run=dict(RUN))
    world.network.resolve("submit", Result(False, error="Cannot reach the server"))
    assert world.pending_run == RUN
    assert world.current.failed
    retry = button_named(world.current.visible_buttons(), "Retry")
    world.handle_event(click(retry))
    assert world.network.names().count("submit") == 2


def test_logging_in_from_the_game_over_screen_saves_the_waiting_run(world):
    world.switch("game_over", run=dict(RUN))
    world.handle_event(click(button_named(world.current.visible_buttons(), "Log in")))
    assert world.current is world.screens["login"]
    type_text(world, "alice")
    press(world, pygame.K_TAB)
    type_text(world, "pw")
    press(world, pygame.K_RETURN)
    world.network.resolve("login", ok(token=good_token(), username="alice"))
    assert world.current is world.screens["game_over"]
    submits = [c for c in world.network.calls if c["name"] == "submit"]
    assert len(submits) == 1 and submits[0]["score"] == 700


def test_going_back_from_login_returns_to_the_waiting_run(world):
    world.switch("game_over", run=dict(RUN))
    world.switch("login")
    press(world, pygame.K_ESCAPE)
    assert world.current is world.screens["game_over"]


def test_a_win_shows_the_win_title(world):
    login_as(world)
    world.switch("game_over", run={"score": 3000, "wave": 10, "won": True})
    draw_all(world)
    assert world.last_run["won"]


def test_a_late_save_answer_after_leaving_still_clears_the_pending_run(world):
    login_as(world)
    world.switch("game_over", run=dict(RUN))
    world.switch("menu")
    world.network.resolve("submit", ok(id=1))
    assert world.pending_run is None


def test_the_game_over_screen_without_any_run_goes_back_to_the_menu(world):
    world.switch("game_over")
    assert world.current is world.screens["menu"]


# play

def test_start_game_begins_a_round_and_escape_leaves_without_saving(world):
    world.handle_event(click(button_named(world.current.buttons, "Start Game")))
    assert world.current is world.screens["play"]
    assert world.screens["play"].game.state == "playing"
    world.update(0.016)
    draw_all(world)
    press(world, pygame.K_ESCAPE)
    assert world.current is world.screens["menu"]
    assert world.pending_run is None
    assert world.network.calls == []


def test_dying_opens_the_game_over_screen_with_the_run(world):
    world.switch("play")
    game = world.screens["play"].game
    game.score = 450
    game.wave = 3
    game.to_spawn = 5
    game.player.hp = 0
    world.update(0.016)
    assert world.current is world.screens["game_over"]
    assert world.last_run == {"score": 450, "wave": 3, "won": False}


def test_winning_marks_the_run_as_won(world):
    world.switch("play")
    game = world.screens["play"].game
    game.score = 4000
    game.wave = 10
    game.to_spawn = 5
    game.state = "victory"
    world.update(0.016)
    assert world.last_run == {"score": 4000, "wave": 10, "won": True}