import pygame

import ui
from main import WIDTH
from screens import Screen

CENTER = WIDTH // 2
WHITE = (255, 255, 255)
GREY = (190, 190, 200)
YELLOW = (255, 230, 90)
RED = (235, 80, 80)
GREEN = (110, 230, 130)
ROW_HEIGHT = 28
BUTTON_WIDTH = 260
BUTTON_HEIGHT = 46


def draw_text(surface, font, text, color, **anchor):
    image = font.render(text, True, color)
    surface.blit(image, image.get_rect(**anchor))


def board_rows(entries, me):
    rows = [
        {"rank": e["rank"], "name": e["player_name"], "score": e["score"], "mine": bool(me) and e["rank"] == me["rank"]}
        for e in entries
    ]
    if me and me["rank"] > len(entries):
        rows.append(None)
        rows.append({"rank": me["rank"], "name": me["player_name"], "score": me["score"], "mine": True})
    return rows


def rows_from(data):
    try:
        return board_rows(data["entries"], data.get("me"))
    except (KeyError, TypeError):
        return None


def draw_board(surface, font, rows, top):
    for index, row in enumerate(rows):
        y = top + index * ROW_HEIGHT
        if row is None:
            draw_text(surface, font, "...", GREY, center=(CENTER, y))
            continue
        if row["mine"]:
            pygame.draw.rect(surface, (50, 50, 75), pygame.Rect(CENTER - 200, y - 13, 400, 26), border_radius=4)
        color = YELLOW if row["mine"] else WHITE
        draw_text(surface, font, f"{row['rank']}.", color, midright=(CENTER - 120, y))
        draw_text(surface, font, str(row["name"]), color, midleft=(CENTER - 100, y))
        draw_text(surface, font, str(row["score"]), color, midright=(CENTER + 190, y))


def stacked_buttons(manager, font, items, top):
    buttons = []
    for index, (label, action) in enumerate(items):
        rect = (CENTER - BUTTON_WIDTH // 2, top + index * (BUTTON_HEIGHT + 14), BUTTON_WIDTH, BUTTON_HEIGHT)
        buttons.append(ui.Button(rect, label, font, action))
    return buttons


def back_button(font, action, top=580):
    return ui.Button((CENTER - BUTTON_WIDTH // 2, top, BUTTON_WIDTH, BUTTON_HEIGHT), "Back", font, action)


def lost_session(screen, result):
    screen.manager.session.logout()
    screen.manager.switch("login", message=result.error)


class MenuScreen(Screen):
    def __init__(self, manager, fonts):
        super().__init__(manager)
        self.fonts = fonts
        self.buttons = []

    def on_enter(self, **data):
        manager = self.manager
        items = [("Start Game", lambda: manager.switch("play"))]
        if manager.session.logged_in:
            items += [
                ("Dashboard", lambda: manager.switch("dashboard")),
                ("Leaderboard", lambda: manager.switch("leaderboard")),
                ("Log out", self.log_out),
            ]
        else:
            items += [
                ("Log in", lambda: manager.switch("login")),
                ("Register", lambda: manager.switch("register")),
                ("Leaderboard", lambda: manager.switch("leaderboard")),
            ]
        self.buttons = stacked_buttons(manager, self.fonts["normal"], items, 270)

    def log_out(self):
        self.manager.session.logout()
        self.manager.pending_run = None
        self.manager.last_run = None
        self.manager.switch("menu")

    def handle_event(self, event):
        for button in self.buttons:
            button.handle_event(event)

    def draw(self, surface):
        draw_text(surface, self.fonts["big"], "DecaDome", WHITE, center=(CENTER, 110))
        draw_text(surface, self.fonts["small"], "Move: WASD or arrows   Aim: mouse   Shoot: hold left click",
                  GREY, center=(CENTER, 175))
        session = self.manager.session
        if session.logged_in:
            draw_text(surface, self.fonts["small"], f"Logged in as {session.username}", GREEN, center=(CENTER, 215))
        else:
            draw_text(surface, self.fonts["small"], "Log in to get on the leaderboard", YELLOW,
                      center=(CENTER, 215))
        for button in self.buttons:
            button.draw(surface)


class AuthScreen(Screen):
    def __init__(self, manager, fonts, mode):
        super().__init__(manager)
        self.fonts = fonts
        self.mode = mode
        self.title = "Log in" if mode == "login" else "Register"
        name_limit = 150 if mode == "login" else 20
        font = fonts["normal"]
        self.username = ui.TextInput((CENTER - 150, 250, 300, 42), font, max_length=name_limit, placeholder="Username")
        self.password = ui.TextInput((CENTER - 150, 310, 300, 42), font, max_length=128, hidden=True,
                                     placeholder="Password")
        self.submit = ui.Button((CENTER - 150, 380, 300, BUTTON_HEIGHT), self.title, font, self.send)
        self.back = back_button(font, self.go_back, top=440)
        self.message = ""
        self.busy = False

    def on_enter(self, message="", **data):
        self.username.clear()
        self.password.clear()
        self.username.focused = True
        self.password.focused = False
        self.message = message
        self.busy = False
        self.submit.enabled = True

    def go_back(self):
        self.manager.switch("game_over" if self.manager.pending_run else "menu")

    def send(self):
        if self.busy:
            return
        username = self.username.text.strip()
        password = self.password.text
        if not username or not password:
            self.message = "Enter a username and password"
            return
        self.busy = True
        self.submit.enabled = False
        self.message = "Please wait..."
        self.password.clear()
        network = self.manager.network
        action = network.login if self.mode == "login" else network.register
        action(username, password, self.on_result)

    def on_result(self, result):
        if self.manager.current is not self:
            return
        self.busy = False
        self.submit.enabled = True
        if not result.ok:
            self.message = result.error
            return
        token = result.data.get("token")
        username = result.data.get("username")
        if not isinstance(token, str) or not isinstance(username, str):
            self.message = "Unexpected answer from the server"
            return
        self.manager.session.login(token, username)
        self.manager.switch("game_over" if self.manager.pending_run else "menu")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                focus_password = self.username.focused
                self.username.focused = not focus_password
                self.password.focused = focus_password
            elif event.key == pygame.K_RETURN:
                self.send()
            elif event.key == pygame.K_ESCAPE:
                self.go_back()
        for widget in (self.username, self.password, self.submit, self.back):
            widget.handle_event(event)

    def draw(self, surface):
        draw_text(surface, self.fonts["big"], self.title, WHITE, center=(CENTER, 130))
        color = GREY if self.busy else RED
        draw_text(surface, self.fonts["small"], self.message, color, center=(CENTER, 215))
        for widget in (self.username, self.password, self.submit, self.back):
            widget.draw(surface)


class LeaderboardScreen(Screen):
    def __init__(self, manager, fonts):
        super().__init__(manager)
        self.fonts = fonts
        self.back = back_button(fonts["normal"], lambda: manager.switch("menu"))
        self.rows = []
        self.status = ""

    def on_enter(self, **data):
        self.rows = []
        self.status = "Loading..."
        self.manager.network.leaderboard(self.manager.session.token, self.on_result)

    def on_result(self, result):
        if self.manager.current is not self:
            return
        rows = rows_from(result.data) if result.ok else None
        if rows is None:
            self.status = result.error or "Unexpected answer from the server"
            return
        self.rows = rows
        self.status = "" if rows else "No scores yet"

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.manager.switch("menu")
        self.back.handle_event(event)

    def draw(self, surface):
        draw_text(surface, self.fonts["big"], "LEADERBOARD", WHITE, center=(CENTER, 70))
        if self.status:
            draw_text(surface, self.fonts["normal"], self.status, GREY, center=(CENTER, 300))
        draw_board(surface, self.fonts["normal"], self.rows, 150)
        self.back.draw(surface)


class DashboardScreen(Screen):
    def __init__(self, manager, fonts):
        super().__init__(manager)
        self.fonts = fonts
        self.back = back_button(fonts["normal"], lambda: manager.switch("menu"))
        self.lines = []
        self.status = ""

    def on_enter(self, **data):
        self.lines = []
        self.status = "Loading..."
        self.manager.network.me(self.manager.session.token, self.on_result)

    def on_result(self, result):
        if self.manager.current is not self:
            return
        if result.expired:
            lost_session(self, result)
            return
        if not result.ok:
            self.status = result.error
            return
        data = result.data
        best = data.get("best_score")
        rank = data.get("rank")
        self.status = ""
        self.lines = [
            str(data.get("username", "")),
            f"Total runs: {data.get('total_runs', 0)}",
            f"Best score: {best}" if best is not None else "Best score: no runs yet",
            f"Rank: #{rank}" if rank is not None else "Rank: unranked",
        ]

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.manager.switch("menu")
        self.back.handle_event(event)

    def draw(self, surface):
        draw_text(surface, self.fonts["big"], "DASHBOARD", WHITE, center=(CENTER, 100))
        if self.status:
            draw_text(surface, self.fonts["normal"], self.status, GREY, center=(CENTER, 300))
        for index, line in enumerate(self.lines):
            color = YELLOW if index == 0 else WHITE
            draw_text(surface, self.fonts["normal"], line, color, center=(CENTER, 220 + index * 50))
        self.back.draw(surface)


class GameOverScreen(Screen):
    def __init__(self, manager, fonts):
        super().__init__(manager)
        self.fonts = fonts
        font = fonts["normal"]
        self.play_again = ui.Button((0, 0, 190, 44), "Play again", font, lambda: manager.switch("play"))
        self.menu = ui.Button((0, 0, 190, 44), "Menu", font, lambda: manager.switch("menu"))
        self.login = ui.Button((0, 0, 190, 44), "Log in", font, lambda: manager.switch("login"))
        self.register = ui.Button((0, 0, 190, 44), "Register", font, lambda: manager.switch("register"))
        self.retry = ui.Button((0, 0, 190, 44), "Retry", font, self.save_run)
        self.rows = []
        self.status = ""
        self.board_status = ""
        self.failed = False

    def on_enter(self, run=None, **data):
        manager = self.manager
        if run:
            manager.last_run = run
            manager.pending_run = run
        if manager.last_run is None:
            manager.switch("menu")
            return
        self.rows = []
        self.board_status = "Loading..."
        self.save_run()

    def save_run(self):
        manager = self.manager
        self.failed = False
        if manager.pending_run and manager.session.logged_in:
            self.status = "Saving your run..."
            run = manager.pending_run
            manager.network.submit_score(manager.session.token, run["score"], run["wave"], run["won"], self.on_saved)
        elif manager.pending_run:
            self.status = "Log in or register to save this run"
            self.load_board()
        else:
            self.status = "Run saved"
            self.load_board()

    def on_saved(self, result):
        manager = self.manager
        if result.ok:
            manager.pending_run = None
            self.status = "Run saved"
        elif result.expired:
            manager.session.logout()
            self.status = "Session expired. Log in to save this run"
        else:
            self.status = result.error
            self.failed = True
        if manager.current is self:
            self.load_board()

    def load_board(self):
        self.manager.network.leaderboard(self.manager.session.token, self.on_board)

    def on_board(self, result):
        if self.manager.current is not self:
            return
        rows = rows_from(result.data) if result.ok else None
        if rows is None:
            self.board_status = "Leaderboard unavailable"
            return
        self.rows = rows
        self.board_status = "" if rows else "No scores yet"

    def visible_buttons(self):
        buttons = [self.play_again, self.menu]
        if self.failed:
            buttons.append(self.retry)
        if self.manager.pending_run and not self.manager.session.logged_in:
            buttons += [self.login, self.register]
        left = CENTER - (len(buttons) * 190 + (len(buttons) - 1) * 16) // 2
        for index, button in enumerate(buttons):
            button.rect.topleft = (left + index * 206, 590)
        return buttons

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.manager.switch("play")
            elif event.key == pygame.K_ESCAPE:
                self.manager.switch("menu")
        for button in self.visible_buttons():
            button.handle_event(event)

    def draw(self, surface):
        run = self.manager.last_run
        title, color = ("YOU WIN", GREEN) if run["won"] else ("GAME OVER", RED)
        draw_text(surface, self.fonts["big"], title, color, center=(CENTER, 60))
        draw_text(surface, self.fonts["normal"], f"Score: {run['score']}   Wave: {run['wave']}", WHITE,
                  center=(CENTER, 118))
        status_color = RED if self.failed else YELLOW
        draw_text(surface, self.fonts["small"], self.status, status_color, center=(CENTER, 152))
        if self.board_status:
            draw_text(surface, self.fonts["small"], self.board_status, GREY, center=(CENTER, 300))
        draw_board(surface, self.fonts["small"], self.rows, 195)
        for button in self.visible_buttons():
            button.draw(surface)


class PlayScreen(Screen):
    def __init__(self, manager, game):
        super().__init__(manager)
        self.game = game

    def on_enter(self, **data):
        self.game.start_game()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.manager.switch("menu")

    def update(self, dt):
        game = self.game
        game.update_playing(dt)
        if game.state in ("game_over", "victory"):
            run = {"score": game.score, "wave": game.wave, "won": game.state == "victory"}
            self.manager.switch("game_over", run=run)

    def draw(self, surface):
        self.game.draw_playing()