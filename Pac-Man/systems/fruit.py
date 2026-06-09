import math
import random

import pygame


class Fruit:

    FRUIT_TYPES = {
        1: ("cherry", 100, (255, 0, 0)),
        2: ("strawberry", 300, (255, 80, 80)),
        3: ("orange", 500, (255, 165, 0)),
        4: ("apple", 700, (255, 0, 120)),
        5: ("melon", 1000, (0, 255, 120)),
        6: ("galaxian", 2000, (0, 255, 255)),
        7: ("bell", 3000, (255, 255, 0)),
        8: ("key", 5000, (255, 255, 255)),
    }

    def __init__(self, level, map_obj):

        self.level = min(level, 8)
        self.name, self.score_value, self.color = self.FRUIT_TYPES[self.level]

        # ✅ positions (compatibilité Game)
        self.x = map_obj.cols // 2
        self.y = map_obj.rows // 2 + 3

        # alias (optionnel mais safe)
        self.grid_x = self.x
        self.grid_y = self.y

        self.visible = False
        self.timer = 0

        # animation
        self.anim_timer = 0
        self.anim_scale = 1.0

    # =========================
    # SPAWN
    # =========================
    def spawn(self):

        self.visible = True

        # ⏱️ 9 à 10 secondes (~60 FPS)
        self.timer = random.randint(540, 600)

    # =========================
    # UPDATE
    # =========================
    def update(self):

        if not self.visible:
            return

        self.timer -= 1

        if self.timer <= 0:
            self.visible = False
            return

        # animation pulse
        self.anim_timer += 1
        self.anim_scale = 1 + 0.1 * math.sin(self.anim_timer * 0.2)

    # =========================
    # COLLISION PLAYER
    # =========================
    def check_collision(self, player):

        if not self.visible:
            return 0

        if player.grid_x == self.x and player.grid_y == self.y:

            self.visible = False
            return self.score_value

        return 0

    # =========================
    # DRAW
    # =========================
    def draw(self, screen, offset_x, offset_y, tile_size):

        if not self.visible:
            return

        px = offset_x + self.x * tile_size
        py = offset_y + self.y * tile_size

        center = (
            px + tile_size // 2,
            py + tile_size // 2
        )

        radius = int(tile_size // 3 * self.anim_scale)

        # 🍒 Cherry
        if self.name == "cherry":

            pygame.draw.circle(screen, (200, 0, 0), center, radius)
            pygame.draw.circle(
                screen,
                (255, 255, 255),
                (center[0] - radius // 3, center[1] - radius // 3),
                radius // 4
            )

        # 🍊 Orange
        elif self.name == "orange":
            pygame.draw.circle(screen, (255, 165, 0), center, radius)

        # 🍎 Apple
        elif self.name == "apple":
            pygame.draw.circle(screen, (255, 0, 100), center, radius)

        # 🍈 Melon
        elif self.name == "melon":
            pygame.draw.circle(screen, (0, 200, 100), center, radius)

        # 🔔 Bell
        elif self.name == "bell":
            pygame.draw.circle(screen, (255, 255, 0), center, radius)

        # 🔑 Key
        elif self.name == "key":
            pygame.draw.circle(screen, (240, 240, 240), center, radius)

        else:
            pygame.draw.circle(screen, self.color, center, radius)