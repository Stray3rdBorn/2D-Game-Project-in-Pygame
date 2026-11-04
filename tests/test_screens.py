import pytest

import screens


class Recorder(screens.Screen):
    def __init__(self, manager):
        super().__init__(manager)
        self.log = []

    def on_enter(self, **data):
        self.log.append(("enter", data))

    def handle_event(self, event):
        self.log.append(("event", event))

    def update(self, dt):
        self.log.append(("update", dt))

    def draw(self, surface):
        self.log.append(("draw", surface))


class FakeNetwork:
    def __init__(self):
        self.polled = 0

    def poll(self):
        self.polled += 1


@pytest.fixture
def manager():
    manager = screens.ScreenManager(session="session", network=FakeNetwork())
    manager.add("menu", Recorder(manager))
    manager.add("login", Recorder(manager))
    return manager


def test_switch_makes_a_screen_current_and_passes_data(manager):
    manager.switch("menu")
    manager.switch("login", reason="expired")
    assert manager.current is manager.screens["login"]
    assert manager.screens["login"].log == [("enter", {"reason": "expired"})]


def test_events_update_and_draw_go_only_to_the_current_screen(manager):
    manager.switch("menu")
    manager.handle_event("click")
    manager.update(0.016)
    manager.draw("surface")
    assert manager.screens["menu"].log[1:] == [("event", "click"), ("update", 0.016), ("draw", "surface")]
    assert manager.screens["login"].log == []


def test_update_collects_network_results_first(manager):
    manager.switch("menu")
    manager.update(0.016)
    assert manager.network.polled == 1


def test_switching_to_an_unknown_screen_fails_loudly(manager):
    with pytest.raises(KeyError):
        manager.switch("nowhere")


def test_screens_can_reach_the_shared_session_through_the_manager(manager):
    assert manager.screens["menu"].manager.session == "session"