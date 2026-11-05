import os
import sys
from pathlib import Path

# Pygame must run without a real window or sound device in CI
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "client"))

import pygame  # noqa: E402
import pytest  # noqa: E402

import main  # noqa: E402

Vector2 = pygame.Vector2


class Keys(dict):
    """Stands in for pygame.key.get_pressed(): any key not set is not pressed."""

    def __missing__(self, key):
        return False


@pytest.fixture(autouse=True)
def isolated_highscore(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "HIGHSCORE_FILE", tmp_path / "highscore.json")


def test_collides_when_circles_overlap():
    assert main.collides(Vector2(0, 0), 10, Vector2(15, 0), 10)


def test_no_collision_when_circles_are_apart():
    assert not main.collides(Vector2(0, 0), 10, Vector2(25, 0), 10)


def test_player_cannot_leave_the_screen():
    player = main.Player()
    keys = Keys({pygame.K_a: True, pygame.K_w: True})
    for _ in range(100):
        player.update(0.1, keys)
    assert player.pos.x == main.PLAYER_RADIUS
    assert player.pos.y == main.PLAYER_RADIUS


def test_diagonal_movement_is_not_faster_than_straight_movement():
    straight = main.Player()
    start = Vector2(straight.pos)
    straight.update(0.1, Keys({pygame.K_d: True}))

    diagonal = main.Player()
    diagonal.update(0.1, Keys({pygame.K_d: True, pygame.K_s: True}))

    assert straight.pos.distance_to(start) == pytest.approx(diagonal.pos.distance_to(start))


def test_player_hit_grants_temporary_immunity():
    player = main.Player()
    hp = player.hp
    player.hit()
    player.hit()
    assert player.hp == hp - 1


def test_bullet_leaving_the_screen_is_detected():
    bullet = main.Bullet(Vector2(main.WIDTH + 10, 10), Vector2(1, 0))
    assert bullet.off_screen()


def test_enemy_moves_toward_the_target():
    enemy = main.Enemy(Vector2(0, 0), 100)
    target = Vector2(500, 0)
    before = enemy.pos.distance_to(target)
    enemy.update(0.5, target)
    assert enemy.pos.distance_to(target) < before


def test_highscore_round_trip():
    assert main.load_highscore() == 0
    main.save_highscore(42)
    assert main.load_highscore() == 42


def test_corrupted_highscore_file_falls_back_to_zero():
    main.HIGHSCORE_FILE.write_text("not json")
    assert main.load_highscore() == 0


def test_game_starts_in_the_menu():
    assert main.Game().state == "menu"


def test_game_runs_headless_for_ten_seconds():
    game = main.Game()
    game.start_game()
    for _ in range(600):
        game.update_playing(1 / 60)
        game.draw()
        if game.state != "playing":
            break
    assert game.state in ("playing", "game_over")


def test_no_tanks_in_wave_one():
    game = main.Game()
    game.wave = 1
    game.enemy_speed = 80
    assert all(game.spawn_enemy().hp == 1 for _ in range(300))


def test_tanks_appear_in_later_waves():
    game = main.Game()
    game.wave = 7
    game.enemy_speed = 100
    hp_values = [game.spawn_enemy().hp for _ in range(300)]
    assert main.TANK_HP in hp_values
    assert 1 in hp_values


def test_each_wave_is_bigger_than_the_last():
    game = main.Game()
    game.start_wave()
    first = game.to_spawn
    game.start_wave()
    assert game.to_spawn > first


def test_tank_survives_hits_and_dies_on_the_last_one():
    game = main.Game()
    game.start_game()
    game.to_spawn = 5          # keeps the wave logic from advancing
    game.spawn_timer = 100     # keeps new enemies from spawning
    tank = main.Enemy(Vector2(100, 100), 0, hp=main.TANK_HP, radius=main.TANK_RADIUS,
                      points=main.TANK_POINTS)
    game.enemies = [tank]

    for hits_so_far in range(1, main.TANK_HP + 1):
        game.bullets = [main.Bullet(Vector2(100, 100), Vector2(0, 0))]
        game.update_playing(0.001)
        if hits_so_far < main.TANK_HP:
            assert tank in game.enemies

    assert tank not in game.enemies
    assert game.score == main.TANK_POINTS