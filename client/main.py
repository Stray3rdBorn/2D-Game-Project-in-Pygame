import json
import random           # for random enemy spawn positions and tank chance

from paths import data_folder
from audio import audio

import pygame

# Window
WIDTH, HEIGHT = 900, 650
FPS = 60
HIGHSCORE_FILE = data_folder() / "highscore.json"   # saved in the game folder in app data, not next to the code

# Player
PLAYER_SPEED = 300      # pixels per second
PLAYER_RADIUS = 14
PLAYER_HP = 5

# Bullets
BULLET_SPEED = 800
BULLET_RADIUS = 4
FIRE_COOLDOWN = 0.10    # seconds between shots (so you can’t spam)

# Enemies and waves
ENEMY_RADIUS = 13
SPAWN_INTERVAL = 0.6    # seconds between each enemy in a wave
WAVE_PAUSE = 3.0        

TANK_HP = 3
TANK_RADIUS = 20
TANK_SPEED_FACTOR = 0.6 # tanks move at 60% of normal enemy speed
TANK_POINTS = 30

TOTAL_WAVES = 10

def load_highscore():    # returns the highscore from the file, or 0 if the file doesn't exist or is invalid
    try:
        return json.loads(HIGHSCORE_FILE.read_text())["highscore"]
    except (FileNotFoundError, KeyError, ValueError):
        return 0


def save_highscore(score):  #saves the highscore to the file
    HIGHSCORE_FILE.parent.mkdir(parents=True, exist_ok=True)   # the folder may not exist on the first run
    HIGHSCORE_FILE.write_text(json.dumps({"highscore": score}))


def collides(pos_a, radius_a, pos_b, radius_b):     
    return pos_a.distance_to(pos_b) < radius_a + radius_b  # True if the two circles overlap, means a hit


def random_edge_position():     # returns a random position just outside the window on one of the four edges so enemies can spawn offscreen
    side = random.choice(["top", "bottom", "left", "right"])
    if side == "top":
        return pygame.Vector2(random.uniform(0, WIDTH), -20)
    if side == "bottom":
        return pygame.Vector2(random.uniform(0, WIDTH), HEIGHT + 20)
    if side == "left":
        return pygame.Vector2(-20, random.uniform(0, HEIGHT))
    return pygame.Vector2(WIDTH + 20, random.uniform(0, HEIGHT))


class Player:
    def __init__(self):  #Creates a new player and puts it in the starting state
        self.reset()

    def reset(self):    #Resets position, health, cooldown and invulnerability
        self.pos = pygame.Vector2(WIDTH / 2, HEIGHT / 2)    #start in the center
        self.hp = PLAYER_HP
        self.cooldown = 0.0     #time until player can shoot again
        self.invulnerable = 0.0 #time player is immune after being hit

    def update(self, dt, keys):
        dx = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])
        dy = (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP])
        direction = pygame.Vector2(dx, dy)
        if direction.length() > 0:
            direction = direction.normalize()
        self.pos += direction * PLAYER_SPEED * dt
        self.pos.x = max(PLAYER_RADIUS, min(WIDTH - PLAYER_RADIUS, self.pos.x))
        self.pos.y = max(PLAYER_RADIUS, min(HEIGHT - PLAYER_RADIUS, self.pos.y))
        self.cooldown = max(0.0, self.cooldown - dt)
        self.invulnerable = max(0.0, self.invulnerable - dt)

    def can_shoot(self):
        return self.cooldown == 0.0

    def shoot(self, target):
        direction = target - self.pos
        if direction.length() == 0:
            return None
        self.cooldown = FIRE_COOLDOWN
        return Bullet(self.pos, direction.normalize())

    def hit(self):
        if self.invulnerable > 0:
            return
        self.hp -= 1
        self.invulnerable = 1.0

    def draw(self, screen):
        # Skip drawing on alternate tenths of a second so the player blinks
        if self.invulnerable > 0 and int(self.invulnerable * 10) % 2 == 0:
            return
        pygame.draw.circle(screen, (80, 200, 255), self.pos, PLAYER_RADIUS)   

class Bullet:
    def __init__(self, pos, direction):
        self.pos = pygame.Vector2(pos)
        self.vel = direction * BULLET_SPEED

    def update(self, dt):
        self.pos += self.vel * dt

    def off_screen(self):
        return not (0 <= self.pos.x <= WIDTH and 0 <= self.pos.y <= HEIGHT)

    def draw(self, screen):
        pygame.draw.circle(screen, (255, 230, 90), self.pos, BULLET_RADIUS)


class Enemy:
    def __init__(self, pos, speed, hp=1, radius=ENEMY_RADIUS, color=(235, 80, 80), points=10):
        self.pos = pygame.Vector2(pos)
        self.speed = speed
        self.hp = hp
        self.radius = radius
        self.color = color
        self.points = points

    def update(self, dt, target):
        direction = target - self.pos
        if direction.length() > 0:
            self.pos += direction.normalize() * self.speed * dt

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, self.pos, self.radius)


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("DecaDome")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 32)
        self.big_font = pygame.font.SysFont(None, 80)
        self.highscore = load_highscore()
        self.player = Player()
        self.state = "menu"
        self.running = True
        self.no_fire_zone = None    # app.py sets this to the mute button area, a click there must not shoot
        self.reset()

    def reset(self):
        self.player.reset()
        self.bullets = []
        self.enemies = []
        self.score = 0
        self.wave = 0
        self.to_spawn = 0
        self.spawn_timer = 0.0
        self.enemy_speed = 0
        self.between_waves = False
        self.wave_timer = 0.0
        # the click that started the game is still held down, so shooting stays locked until I let go
        self.fire_locked = True

    def start_game(self):
        self.reset()
        self.state = "playing"

    def start_wave(self):
        self.wave += 1
        self.to_spawn = 5 + 5 * self.wave
        self.enemy_speed = min(70 + 12 * self.wave, 220)
        self.spawn_timer = 0.0

    def end_game(self):
        if self.score > self.highscore:
            self.highscore = self.score
            save_highscore(self.highscore)
        self.state = "game_over"

    def win_game(self):
        if self.score > self.highscore:
            self.highscore = self.score
            save_highscore(self.highscore)
        self.state = "victory"

    def spawn_enemy(self):
        pos = random_edge_position()
        tank_chance = min(0.1 * (self.wave - 1), 0.6)
        if random.random() < tank_chance:
            return Enemy(pos, self.enemy_speed * TANK_SPEED_FACTOR, hp=TANK_HP,
                         radius=TANK_RADIUS, color=(190, 60, 200), points=TANK_POINTS)
        return Enemy(pos, self.enemy_speed)

    def update_playing(self, dt):
        keys = pygame.key.get_pressed()
        self.player.update(dt, keys)

        # Shooting
        if pygame.mouse.get_pressed()[0] and self.player.can_shoot():
            bullet = self.player.shoot(pygame.Vector2(pygame.mouse.get_pos()))
            if bullet:
                self.bullets.append(bullet)

        for bullet in self.bullets:
            bullet.update(dt)
        self.bullets = [b for b in self.bullets if not b.off_screen()]

        # Spawning enemies one by one
        if self.to_spawn > 0:
            self.spawn_timer -= dt
            if self.spawn_timer <= 0:
                self.enemies.append(self.spawn_enemy())
                self.to_spawn -= 1
                self.spawn_timer = SPAWN_INTERVAL

        for enemy in self.enemies:
            enemy.update(dt, self.player.pos)

        # Bullets hitting enemies
        for bullet in self.bullets[:]:
            for enemy in self.enemies[:]:
                if collides(bullet.pos, BULLET_RADIUS, enemy.pos, enemy.radius):
                    self.bullets.remove(bullet)
                    enemy.hp -= 1
                    if enemy.hp <= 0:
                        self.enemies.remove(enemy)
                        self.score += enemy.points
                    break

        # Enemies touching the player
        for enemy in self.enemies[:]:
            if collides(enemy.pos, enemy.radius, self.player.pos, PLAYER_RADIUS):
                self.enemies.remove(enemy)
                self.player.hit()

        # Wave cleared: bonus, short pause, next wave
        if self.to_spawn == 0 and not self.enemies:
            if not self.between_waves:
                self.between_waves = True
                self.wave_timer = WAVE_PAUSE
                self.score += 50 * self.wave
                if self.wave >= TOTAL_WAVES and self.player.hp > 0:
                    self.win_game()
                    return
            self.wave_timer -= dt
            if self.wave_timer <= 0:
                self.between_waves = False
                self.start_wave()

        if self.player.hp <= 0:
            self.end_game()

    def draw_text(self, text, font, color, center):
        surface = font.render(text, True, color)
        self.screen.blit(surface, surface.get_rect(center=center))

    def draw_menu(self):
        self.draw_text("DecaDome", self.big_font, (255, 255, 255), (WIDTH / 2, 200))
        self.draw_text("Move: WASD or arrows   Aim: mouse   Shoot: hold left click",
                       self.font, (190, 190, 200), (WIDTH / 2, 300))
        self.draw_text("Press SPACE to start", self.font, (255, 230, 90), (WIDTH / 2, 380))
        self.draw_text(f"High score: {self.highscore}", self.font, (190, 190, 200), (WIDTH / 2, 440))

    def draw_playing(self):
        for enemy in self.enemies:
            enemy.draw(self.screen)
        for bullet in self.bullets:
            bullet.draw(self.screen)
        self.player.draw(self.screen)

        hud = f"Score: {self.score}    Wave: {self.wave}    HP: {self.player.hp}    Best: {self.highscore}"
        self.screen.blit(self.font.render(hud, True, (255, 255, 255)), (16, 12))

        if self.between_waves:
            self.draw_text(f"Wave {self.wave + 1} incoming", self.big_font,
                           (255, 230, 90), (WIDTH / 2, HEIGHT / 2 - 120))

    def draw_game_over(self):
        self.draw_text("GAME OVER", self.big_font, (235, 80, 80), (WIDTH / 2, 200))
        self.draw_text(f"Score: {self.score}   Wave reached: {self.wave}",
                       self.font, (255, 255, 255), (WIDTH / 2, 300))
        self.draw_text(f"High score: {self.highscore}", self.font, (190, 190, 200), (WIDTH / 2, 345))
        self.draw_text("Press SPACE to play again", self.font, (255, 230, 90), (WIDTH / 2, 420))

    def draw_victory(self):
        self.draw_text("YOU WIN", self.big_font, (110, 230, 130), (WIDTH / 2, 200))
        self.draw_text(f"Score: {self.score}   HP left: {self.player.hp}",
                       self.font, (255, 255, 255), (WIDTH / 2, 300))
        self.draw_text(f"High score: {self.highscore}", self.font, (190, 190, 200), (WIDTH / 2, 345))
        self.draw_text("Press SPACE to play again", self.font, (255, 230, 90), (WIDTH / 2, 420))

    def draw(self):
        self.screen.fill((20, 20, 28))
        if self.state == "menu":
            self.draw_menu()
        elif self.state == "playing":
            self.draw_playing()
        elif self.state == "victory":
            self.draw_victory()
        else:
            self.draw_game_over()
        pygame.display.flip()

    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000, 0.05)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_SPACE and self.state in ("menu", "game_over", "victory"):
                        self.start_game()

            if self.state == "playing":
                self.update_playing(dt)

            self.draw()

        pygame.quit()


if __name__ == "__main__":
    Game().run()