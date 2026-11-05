import pygame

import views
from main import FPS, Game
from network import Network
from screens import ScreenManager
from storage import Session


def build(game, session, network):
    manager = ScreenManager(session, network)
    fonts = {"normal": game.font, "big": game.big_font, "small": pygame.font.SysFont(None, 26)}
    manager.add("menu", views.MenuScreen(manager, fonts))
    manager.add("login", views.AuthScreen(manager, fonts, "login"))
    manager.add("register", views.AuthScreen(manager, fonts, "register"))
    manager.add("leaderboard", views.LeaderboardScreen(manager, fonts))
    manager.add("dashboard", views.DashboardScreen(manager, fonts))
    manager.add("game_over", views.GameOverScreen(manager, fonts))
    manager.add("play", views.PlayScreen(manager, game))
    return manager


def run():
    game = Game()
    manager = build(game, Session(), Network())
    manager.switch("menu")
    running = True
    while running:
        dt = min(game.clock.tick(FPS) / 1000, 0.05)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                manager.handle_event(event)
        manager.update(dt)
        game.screen.fill((20, 20, 28))
        manager.draw(game.screen)
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    run()