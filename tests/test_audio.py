import sys

import pygame
import pytest

import audio
import paths
import screens
import ui


@pytest.fixture(autouse=True)
def pygame_ready():
    pygame.init()
    pygame.display.set_mode((300, 200))
    yield
    pygame.quit()


class FakeSound:
    def __init__(self):
        self.plays = 0

    def play(self):
        self.plays += 1


def started(folder=None):
    sound = audio.Audio(folder)
    sound.start()
    if not sound.ready:
        pytest.skip("no sound device, not even the dummy one")
    return sound


def click(pos):
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)


def test_nothing_happens_before_start(tmp_path):
    sound = audio.Audio(tmp_path)
    sound.play("kill")
    sound.play_music("menu")
    assert sound.current_music is None


def test_every_music_track_and_effect_exists_in_the_assets_folder():
    sound = audio.Audio()
    for name in audio.MUSIC:
        assert sound.find("music", name) is not None
    for name in audio.EFFECTS:
        assert sound.find("sounds", name) is not None


def test_start_loads_all_effects():
    sound = started()
    assert set(sound.sounds) == set(audio.EFFECTS)


def test_missing_files_keep_the_game_silent(tmp_path):
    sound = started(tmp_path)
    assert sound.sounds == {}
    sound.play("kill")
    sound.play_music("menu")
    assert sound.current_music is None


def test_ogg_is_used_before_mp3_and_wav(tmp_path):
    (tmp_path / "music").mkdir()
    for extension in (".wav", ".mp3", ".ogg"):
        (tmp_path / "music" / f"menu{extension}").touch()
    assert audio.Audio(tmp_path).find("music", "menu").suffix == ".ogg"


def test_same_track_is_not_restarted(monkeypatch):
    sound = started()
    loads = []
    real_load = pygame.mixer.music.load
    monkeypatch.setattr(pygame.mixer.music, "load", lambda path: (loads.append(path), real_load(path)))
    sound.play_music("menu")
    sound.play_music("menu")
    assert len(loads) == 1
    sound.play_music("play")
    assert len(loads) == 2
    assert sound.current_music == "play"


def test_muted_effects_are_not_played():
    sound = audio.Audio()
    fake = FakeSound()
    sound.sounds["kill"] = fake
    sound.play("kill")
    sound.toggle_mute()
    sound.play("kill")
    sound.toggle_mute()
    sound.play("kill")
    assert fake.plays == 2


def test_mute_silences_the_music_and_unmute_brings_it_back():
    sound = started()
    sound.play_music("menu")
    sound.toggle_mute()
    assert pygame.mixer.music.get_volume() == 0
    sound.toggle_mute()
    assert pygame.mixer.music.get_volume() == pytest.approx(audio.MUSIC_VOLUME, abs=0.01)


def test_music_started_while_muted_stays_silent():
    sound = started()
    sound.toggle_mute()
    sound.play_music("play")
    assert pygame.mixer.music.get_volume() == 0


def test_asset_folder_inside_the_exe(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    assert paths.asset_folder() == tmp_path / "assets"


def test_asset_folder_from_source():
    assert paths.asset_folder().name == "assets"
    assert paths.asset_folder().parent.name == "client"


def test_mute_button_click_toggles_and_is_taken():
    sound = audio.Audio()
    button = ui.MuteButton(sound, (100, 10, 44, 44))
    assert button.handle_event(click((120, 30))) is True
    assert sound.muted is True
    assert button.handle_event(click((500, 300))) is False
    assert sound.muted is True


def test_mute_button_ignores_other_mouse_buttons():
    sound = audio.Audio()
    button = ui.MuteButton(sound, (100, 10, 44, 44))
    right_click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=3, pos=(120, 30))
    assert button.handle_event(right_click) is False
    assert sound.muted is False


def test_mute_button_draws_both_states():
    sound = audio.Audio()
    button = ui.MuteButton(sound, (100, 10, 44, 44))
    surface = pygame.Surface((300, 100))
    button.draw(surface)
    sound.toggle_mute()
    button.draw(surface)


def test_screen_manager_gives_the_click_to_the_mute_button_first():
    class Spy(screens.Screen):
        def __init__(self, manager):
            super().__init__(manager)
            self.events = []

        def handle_event(self, event):
            self.events.append(event)

    class NoNetwork:
        def poll(self):
            pass

    manager = screens.ScreenManager(session=None, network=NoNetwork())
    spy = Spy(manager)
    manager.add("menu", spy)
    manager.switch("menu")
    sound = audio.Audio()
    manager.mute_button = ui.MuteButton(sound, (100, 10, 44, 44))

    manager.handle_event(click((120, 30)))
    assert sound.muted is True
    assert spy.events == []

    manager.handle_event(click((500, 300)))
    assert len(spy.events) == 1