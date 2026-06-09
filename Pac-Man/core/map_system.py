import os
import random
from typing import List, Tuple

import pygame
from PIL import Image

# ==========================================================
# CONSTANTES
# ==========================================================
WALL = "#"
DOT = "."
POWER = "o"
EMPTY = " "

# ==========================================================
# MAP SYSTEM (LOADER + MAP = FUSION)
# ==========================================================
class MapSystem:
    def __init__(self, image_paths: List[str], scale: float = 1.0):

        self.scale = scale
        self.tile_size = 20

        self.maps: List[Image.Image] = []
        self.maze: List[List[str]] = []

        self.cols = 0
        self.rows = 0

        self.surface = None
        self.scaled_surface = None

        self._load_images(image_paths)
        self.load_random_map()

    # ==================================================
    # LOAD IMAGES
    # ==================================================
    def _load_images(self, paths: List[str]):
        print("\n===== MAP LOADING =====")

        for path in paths:
            if not os.path.exists(path):
                print(f"❌ NOT FOUND: {path}")
                continue

            try:
                img = Image.open(path).convert("RGB")
                self.maps.append(img)
                print(f"✅ Loaded: {path} ({img.size})")
            except Exception as e:
                print(f"❌ ERROR: {path} → {e}")

        if not self.maps:
            raise RuntimeError("❌ No valid maps loaded")

        print(f"✅ TOTAL MAPS: {len(self.maps)}\n")

    # ==================================================
    # LOAD RANDOM MAP
    # ==================================================
    def load_random_map(self):
        img = random.choice(self.maps).copy()
        self._build_from_image(img)

    # ==================================================
    # BUILD GRID FROM IMAGE
    # ==================================================
    def _build_from_image(self, img: Image.Image):

        self.cols, self.rows = img.size
        pixels = img.load()

        self.maze = []
        colors = set()

        for y in range(self.rows):
            row = []
            for x in range(self.cols):

                r, g, b = pixels[x, y]
                colors.add((r, g, b))

                # WALL
                if r < 40 and g < 40 and b < 40:
                    row.append(WALL)

                # DOT
                elif r > 200 and g > 200 and b > 200:
                    row.append(DOT)

                # POWER
                elif r > 200 and g < 120 and b < 120:
                    row.append(POWER)

                else:
                    row.append(EMPTY)

            self.maze.append(row)

        print("\n===== MAP ANALYSIS =====")
        print(f"Size: {self.cols}x{self.rows}")
        print(f"Dots: {sum(row.count(DOT) for row in self.maze)}")
        print(f"Colors detected: {len(colors)}")

        # PIL → pygame
        mode = img.mode
        data = img.tobytes()
        self.surface = pygame.image.fromstring(data, img.size, mode)

        self._update_scaled_surface()

    # ==================================================
    # SCALE
    # ==================================================
    def set_tile_size(self, tile_size: int):
        self.tile_size = max(4, tile_size)
        self._update_scaled_surface()

    def _update_scaled_surface(self):
        if not self.surface:
            return

        w = self.cols * self.tile_size
        h = self.rows * self.tile_size

        self.scaled_surface = pygame.transform.scale(self.surface, (w, h))

    # ==================================================
    # GAME LOGIC
    # ==================================================
    def is_wall(self, x: int, y: int) -> bool:
        if not (0 <= x < self.cols and 0 <= y < self.rows):
            return True
        return self.maze[y][x] == WALL

    def eat_dot(self, x: int, y: int):
        if not (0 <= x < self.cols and 0 <= y < self.rows):
            return None

        tile = self.maze[y][x]

        if tile in (DOT, POWER):
            self.maze[y][x] = EMPTY
            return "power" if tile == POWER else "dot"

        return None

    def remaining_dots(self) -> bool:
        return any(tile in (DOT, POWER) for row in self.maze for tile in row)

    def wrap_position(self, x: int, y: int) -> Tuple[int, int]:
        if x < 0:
            x = self.cols - 1
        elif x >= self.cols:
            x = 0

        if y < 0:
            y = self.rows - 1
        elif y >= self.rows:
            y = 0

        return x, y

    def get_random_empty_tile(self) -> Tuple[int, int]:
        empty = [
            (x, y)
            for y in range(self.rows)
            for x in range(self.cols)
            if self.maze[y][x] == EMPTY
        ]

        return random.choice(empty) if empty else (1, 1)

