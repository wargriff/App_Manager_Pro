import os
import random

import pygame

from core.ai import GhostAI
from rendering.animation import Animation


class Ghost:

    DIRECTIONS = {
        "right": (1, 0),
        "left": (-1, 0),
        "down": (0, 1),
        "up": (0, -1)
    }

    def __init__(self, x, y, folder_path, tile_size, speed):

        # =============================
        # POSITION
        # =============================
        self.spawn_x = x
        self.spawn_y = y
        self.grid_x = x
        self.grid_y = y
        self.dx = 0
        self.dy = 0
        self.x = x
        self.y = y

        # =============================
        # CONFIG
        # =============================
        self.tile_size = tile_size

        self.base_speed = speed
        self.speed = speed

        self.timer = 0
        self.spawn_delay = 60   # 1 seconde

        # nom du ghost
        self.name = os.path.basename(folder_path).lower()

        # =============================
        # ANIMATIONS
        # =============================
        self.animations = self.load_animations(folder_path)

        if self.animations:
            self.current_direction = next(iter(self.animations))
        else:
            self.current_direction = "left"

        # =============================
        # BOSS
        # =============================
        self.is_boss = "boss" in self.name

        if self.is_boss:
            self.max_hp = 10
        else:
            self.max_hp = 1

        self.hp = self.max_hp
        self.phase = 1

        # teleport boss
        self.teleport_cooldown = 0
        self.max_teleport_cooldown = 120

        # IA
        self.ai = GhostAI(self)

    # ==========================================================
    # LOAD ANIMATIONS
    # ==========================================================

    def load_animations(self, base_path):

        animations = {}

        if not os.path.exists(base_path):
            print("❌ Ghost folder missing:", base_path)
            return animations

        subfolders = [
            f for f in os.listdir(base_path)
            if os.path.isdir(os.path.join(base_path, f))
        ]

        # ==========================
        # CAS NORMAL (ghost classique)
        # ==========================
        if subfolders:

            for direction in subfolders:

                dir_lower = direction.lower()

                if dir_lower in self.DIRECTIONS:
                    path = os.path.join(base_path, direction)

                    animations[dir_lower] = Animation(
                        path,
                        self.tile_size,
                        speed=10
                    )

        # ==========================
        # CAS BOSS (images directes)
        # ==========================
        else:
            print(f"👹 Boss detected (no directions): {base_path}")

            animations["default"] = Animation(
                base_path,
                self.tile_size,
                speed=8
            )

        return animations

    # ==========================================================
    # UPDATE
    # ==========================================================

    def update(self, map_obj, player_x, player_y):

        maze = map_obj.maze

        # spawn delay
        if self.spawn_delay > 0:
            self.spawn_delay -= 1
            self.update_animation()
            return

        # timer mouvement
        self.timer += 1

        if self.timer < self.speed:
            self.update_animation()
            return

        self.timer = 0

        # direction IA
        dx, dy = self.choose_direction(maze, player_x, player_y)

        new_x = self.x + dx
        new_y = self.y + dy

        # validation mouvement
        if self.is_valid_move(maze, new_x, new_y):

            self.x = new_x
            self.y = new_y
            self.grid_x = self.x
            self.grid_y = self.y
            self.update_direction(dx, dy)

        else:
            # fallback random
            dx, dy = self.random_move(maze)

            self.x += dx
            self.y += dy
            self.grid_x = self.x
            self.grid_y = self.y

            self.update_direction(dx, dy)

        # tunnel
        self.handle_tunnel(map_obj)

        # animation
        self.update_animation()

    # ==========================================================
    # VALID MOVE
    # ==========================================================

    def is_valid_move(self, maze, x, y):

        if 0 <= y < len(maze) and 0 <= x < len(maze[0]):
            return maze[y][x] != "#"

        return False

    # ==========================================================
    # UPDATE DIRECTION
    # ==========================================================

    def update_direction(self, dx, dy):

        for name, (dir_x, dir_y) in self.DIRECTIONS.items():

            if (dx, dy) == (dir_x, dir_y):

                self.current_direction = name
                return

    # ==========================================================
    # IA
    # ==========================================================

    def choose_direction(self, maze, player_x, player_y):

        distance = abs(self.x - player_x) + abs(self.y - player_y)

        if self.name == "blinky":

            return self.move_towards(maze, player_x, player_y)

        elif self.name == "pinky":

            return self.move_towards(maze, player_x + 2, player_y)

        elif self.name == "inky":

            if random.random() < 0.7:
                return self.move_towards(maze, player_x, player_y)

            return self.random_move(maze)

        elif self.name == "clyde":

            if distance < 5:
                return self.move_away(maze, player_x, player_y)

            return self.move_towards(maze, player_x, player_y)

        return self.random_move(maze)

    # ==========================================================
    # MOVE TOWARDS / AWAY
    # ==========================================================

    def move_towards(self, maze, target_x, target_y):

        return self.best_move(maze, target_x, target_y, reverse=False)

    def move_away(self, maze, target_x, target_y):

        return self.best_move(maze, target_x, target_y, reverse=True)

    def best_move(self, maze, target_x, target_y, reverse=False):

        best_move = None
        best_distance = -1 if reverse else float("inf")

        for dx, dy in self.DIRECTIONS.values():

            nx = self.x + dx
            ny = self.y + dy

            if not self.is_valid_move(maze, nx, ny):
                continue

            distance = abs(nx - target_x) + abs(ny - target_y)

            if (reverse and distance > best_distance) or \
               (not reverse and distance < best_distance):

                best_distance = distance
                best_move = (dx, dy)

        if best_move is None:
            return self.random_move(maze)

        return best_move

    # ==========================================================
    # RANDOM MOVE
    # ==========================================================

    def random_move(self, maze):

        directions = list(self.DIRECTIONS.values())
        random.shuffle(directions)

        for dx, dy in directions:

            nx = self.x + dx
            ny = self.y + dy

            if self.is_valid_move(maze, nx, ny):
                return dx, dy

        return 0, 0

    # ==========================================================
    # TUNNEL
    # ==========================================================

    def handle_tunnel(self, map_obj):

        if self.x < 0:
            self.x = map_obj.cols - 1

        elif self.x >= map_obj.cols:
            self.x = 0

        self.grid_x = self.x
        self.grid_y = self.y

    # ==========================================================
    # ANIMATION
    # ==========================================================

    def update_animation(self):

        if not self.animations:
            return

        anim = self.animations.get(self.current_direction)

        if not anim:
            anim = self.animations.get("default")

        if anim is None:
            anim = next(iter(self.animations.values()))

        # noinspection PyUnresolvedReferences
        anim.update()

    # ==========================================================
    # DRAW
    # ==========================================================

    def draw(self, screen, offset_x, offset_y):

        if not self.animations:
            return

        anim = self.animations.get(self.current_direction)

        if anim is None:
            anim = next(iter(self.animations.values()))

        # noinspection PyUnresolvedReferences
        frame = anim.get_frame()

        screen.blit(
            frame,
            (
                offset_x + self.x * self.tile_size,
                offset_y + self.y * self.tile_size
            )
        )

    # ==========================================================
    # RESET
    # ==========================================================

    def reset(self):

        self.x = self.spawn_x
        self.y = self.spawn_y
        self.grid_x = self.spawn_x
        self.grid_y = self.spawn_y

        self.current_direction = "left"

        self.timer = 0

        # respawn delay comme Pac-Man
        self.spawn_delay = 120

    def reset_position(self):

        self.x = self.spawn_x
        self.y = self.spawn_y
        self.grid_x = self.spawn_x
        self.grid_y = self.spawn_y

    def set_tile_size(self, tile_size: int):
        self.tile_size = tile_size

        for anim in self.animations.values():
            if hasattr(anim, "frames"):
                anim.frames = [
                    pygame.transform.scale(img, (tile_size, tile_size))
                    for img in anim.frames
                ]

        # rescale sprite
        if hasattr(self, "frames"):
            for direction in self.frames:
                # noinspection PyUnresolvedReferences
                self.frames[direction] = [
                    pygame.transform.scale(img, (tile_size, tile_size))
                    for img in self.frames[direction]
                ]
