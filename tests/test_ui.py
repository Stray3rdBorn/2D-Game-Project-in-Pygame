import pygame
import pytest

import ui


@pytest.fixture(autouse=True)
def pygame_ready():
    pygame.init()
    pygame.display.set_mode((300, 200))
    yield
    pygame.quit()


@pytest.fixture
def font():
    return pygame.font.Font(None, 24)


def click(x, y, button=1):
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(x, y), button=button)


def key(character, code=None):
    return pygame.event.Event(pygame.KEYDOWN, key=code or ord(character or "?"), unicode=character)


def test_button_calls_back_only_when_clicked_inside(font):
    hits = []
    button = ui.Button((10, 10, 100, 40), "Go", font, lambda: hits.append(1))
    button.handle_event(click(20, 20))
    button.handle_event(click(200, 20))
    button.handle_event(click(20, 20, button=3))
    assert hits == [1]


def test_disabled_button_ignores_clicks(font):
    hits = []
    button = ui.Button((10, 10, 100, 40), "Go", font, lambda: hits.append(1))
    button.enabled = False
    button.handle_event(click(20, 20))
    assert hits == []


def test_text_input_types_only_when_focused(font):
    box = ui.TextInput((10, 10, 200, 30), font)
    box.handle_event(key("a"))
    assert box.text == ""
    box.handle_event(click(20, 20))
    box.handle_event(key("a"))
    box.handle_event(key("b"))
    assert box.text == "ab"


def test_backspace_removes_the_last_character(font):
    box = ui.TextInput((10, 10, 200, 30), font)
    box.handle_event(click(20, 20))
    box.handle_event(key("a"))
    box.handle_event(key("b"))
    box.handle_event(key("", pygame.K_BACKSPACE))
    box.handle_event(key("", pygame.K_BACKSPACE))
    box.handle_event(key("", pygame.K_BACKSPACE))
    assert box.text == ""


def test_text_input_stops_at_max_length(font):
    box = ui.TextInput((10, 10, 200, 30), font, max_length=3)
    box.handle_event(click(20, 20))
    for character in "abcdef":
        box.handle_event(key(character))
    assert box.text == "abc"


def test_control_characters_are_ignored(font):
    box = ui.TextInput((10, 10, 200, 30), font)
    box.handle_event(click(20, 20))
    box.handle_event(key("\r", pygame.K_RETURN))
    box.handle_event(key("\t", pygame.K_TAB))
    box.handle_event(key("\x1b", pygame.K_ESCAPE))
    assert box.text == ""


def test_clicking_elsewhere_moves_focus_away(font):
    first = ui.TextInput((10, 10, 200, 30), font)
    second = ui.TextInput((10, 60, 200, 30), font)
    first.handle_event(click(20, 20))
    for box in (first, second):
        box.handle_event(click(20, 70))
    assert not first.focused
    assert second.focused


def test_hidden_input_shows_stars_and_keeps_the_real_text(font):
    box = ui.TextInput((10, 10, 200, 30), font, hidden=True)
    box.handle_event(click(20, 20))
    box.handle_event(key("p"))
    box.handle_event(key("w"))
    assert box.shown_text() == "**"
    assert box.text == "pw"
    box.clear()
    assert box.text == ""


def test_widgets_draw_without_errors(font):
    surface = pygame.display.get_surface()
    widgets = [
        ui.Label("Hello", font, ui.TEXT_COLOR, (150, 20)),
        ui.Button((10, 50, 100, 40), "Go", font, lambda: None),
        ui.TextInput((10, 100, 200, 30), font, placeholder="Name"),
    ]
    widgets[2].focused = True
    for widget in widgets:
        widget.draw(surface)
    widgets[2].focused = False
    widgets[2].draw(surface)