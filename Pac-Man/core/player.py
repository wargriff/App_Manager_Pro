# file: core/player.py

import os

import pygame

from config.paths import SPRITES_PATH
from rendering.animation import Animation


class Player:

    def __init__(self, x, y, tile_size, audio):
        self.tile_size = None
        self.radius = None
        self.collision_radius = None
        self.speed = None
        self.x = None
        self.y = None
        self.animations = None
        self.audio = audio

        self.spawn_x = x
        self.spawn_y = y

        self.grid_x = x
        self.grid_y = y

        self.dx = 0
        self.dy = 0
        self.next_dx = 0
        self.next_dy = 0

        self.direction = "RIGHT"

        self.score = 0
        self.max_lives = 3
        self.lives = self.max_lives

        self.is_dead = False
        self.game_over = False

        self.power_mode = False
        self.power_timer = 0
        self.power_duration = 300

        self.invincible = False
        self.invincible_timer = 0
        self.invincible_duration = 120

        self.set_tile_size(tile_size)
        self.snap_to_grid()
        self.load_animations()

    # =========================
    # SIZE
    # =========================
    def set_tile_size(self, tile_size):
        self.tile_size = tile_size

        # 🔥 PLUS GROS
        self.radius = int(tile_size * 0.45)

        # 🔥 HITBOX plus clean
        self.collision_radius = int(self.radius * 0.8)

        self.speed = max(1, tile_size // 8)

        self.load_animations()
    # =========================
    # POSITION
    # =========================
    def snap_to_grid(self):
        self.x = self.grid_x * self.tile_size + self.tile_size // 2
        self.y = self.grid_y * self.tile_size + self.tile_size // 2

    # =========================
    # ANIMATIONS
    # =========================
    def load_animations(self):
        pac_folder = os.path.join(SPRITES_PATH, "Pac-Man")
        self.animations = {}

        for d in ["RIGHT", "LEFT", "UP", "DOWN"]:
            folder = os.path.join(pac_folder, d.lower())

            if not os.path.exists(folder):
                continue

            self.animations[d] = Animation(
                folder,
                int(self.tile_size * 1.2),  # 🔥 scale sprite
                speed=6,
                loop=True
            )

    def update_animation(self):
        anim = self.animations.get(self.direction)
        if anim:
            anim.update()

    # =========================
    # INPUT (ZQSD + FLÈCHES)
    # =========================
    def player_move(self):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT] or keys[pygame.K_q]:
            self.next_dx, self.next_dy = -1, 0
            self.direction = "LEFT"

        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.next_dx, self.next_dy = 1, 0
            self.direction = "RIGHT"

        elif keys[pygame.K_UP] or keys[pygame.K_z]:
            self.next_dx, self.next_dy = 0, -1
            self.direction = "UP"

        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.next_dx, self.next_dy = 0, 1
            self.direction = "DOWN"

    # =========================
    # COLLISION (AMÉLIORÉE)
    # =========================
    def can_move(self, dx, dy, game_map):
        if dx == 0 and dy == 0:
            return True

        next_x = self.x + dx * self.speed
        next_y = self.y + dy * self.speed

        r = self.collision_radius

        points = [
            (next_x - r, next_y),
            (next_x + r, next_y),
            (next_x, next_y - r),
            (next_x, next_y + r),
        ]

        for px, py in points:
            gx = int(px // self.tile_size)
            gy = int(py // self.tile_size)

            if game_map.is_wall(gx, gy):
                return False

        return True

    # =========================
    # CENTER CHECK
    # =========================
    def is_centered(self):
        cx = self.grid_x * self.tile_size + self.tile_size // 2
        cy = self.grid_y * self.tile_size + self.tile_size // 2
        return abs(self.x - cx) < 2 and abs(self.y - cy) < 2

    # =========================
    # UPDATE
    # =========================
    def update(self, game_map):

        if self.is_dead or self.game_over:
            return

        self.player_move()

        if self.is_centered():
            if self.can_move(self.next_dx, self.next_dy, game_map):
                self.dx = self.next_dx
                self.dy = self.next_dy

        if not self.can_move(self.dx, self.dy, game_map):
            self.dx = 0
            self.dy = 0

        self.x += self.dx * self.speed
        self.y += self.dy * self.speed

        self.update_grid_position()

        result = game_map.eat_dot(self.grid_x, self.grid_y)

        if result == "dot":
            self.score += 10
        elif result == "power":
            self.score += 50
            self.power_mode = True
            self.power_timer = self.power_duration

        self.update_timers()
        self.update_animation()

    def update_grid_position(self):
        self.grid_x = int(self.x // self.tile_size)
        self.grid_y = int(self.y // self.tile_size)

    def update_timers(self):
        if self.power_mode:
            self.power_timer -= 1
            if self.power_timer <= 0:
                self.power_mode = False

        if self.invincible:
            self.invincible_timer -= 1
            if self.invincible_timer <= 0:
                self.invincible = False

    def reset_position(self):
        self.grid_x = self.spawn_x
        self.grid_y = self.spawn_y
        self.snap_to_grid()

        self.dx = self.dy = 0
        self.next_dx = self.next_dy = 0
        self.is_dead = False

    # =========================
    # DRAW
    # =========================
    def draw(self, surface, offset_x, offset_y):

        screen_x = offset_x + int(self.x)
        screen_y = offset_y + int(self.y)

        anim = self.animations.get(self.direction)

        if not anim:
            pygame.draw.circle(surface, (255, 255, 0), (screen_x, screen_y), self.radius)
            return

        frame = anim.get_frame()

        if frame is None:
            return

        rect = frame.get_rect(center=(screen_x, screen_y))
        surface.blit(frame, rect)