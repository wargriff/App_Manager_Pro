import os

import pygame


# ==========================================================
# ASSET MANAGER
# ==========================================================

class AssetManager:

    _images = {}

    @classmethod
    def image(cls, full_path):

        if full_path not in cls._images:

            cls._images[full_path] = pygame.image.load(full_path).convert_alpha()

        return cls._images[full_path]


# ==========================================================
# ANIMATION
# ==========================================================

class Animation:

    def __init__(self, folder_path, tile_size, speed=8, loop=True):

        self.frames = []
        self.speed = speed
        self.timer = 0
        self.current_frame = 0
        self.loop = loop
        self.finished = False

        # ✅ chemin direct (déjà correct depuis config.paths)
        folder = folder_path

        if not os.path.exists(folder):
            raise FileNotFoundError(f"❌ Dossier introuvable : {folder}")

        # ======================================================
        # TRI ROBUSTE
        # ======================================================

        files = sorted(
            [f for f in os.listdir(folder) if f.endswith(".png")],
            key=self._natural_sort
        )

        print("✅ Loaded frames:", files)

        # ======================================================
        # LOAD IMAGES
        # ======================================================

        for file in files:

            full_path = os.path.join(folder, file)

            img = AssetManager.image(full_path)
            img = pygame.transform.scale(img, (tile_size, tile_size))

            self.frames.append(img)

        if not self.frames:
            raise ValueError(f"❌ Aucune image trouvée dans {folder}")

    # ==========================================================
    # TRI NATUREL (fix 1,2,10)
    # ==========================================================

    def _natural_sort(self, filename):

        import re

        return [
            int(text) if text.isdigit() else text.lower()
            for text in re.split(r'(\d+)', filename)
        ]

    # ==========================================================
    # UPDATE
    # ==========================================================

    def update(self):

        if self.finished or not self.frames:
            return

        self.timer += 1

        if self.timer >= self.speed:

            self.timer = 0

            if self.loop:
                self.current_frame = (self.current_frame + 1) % len(self.frames)

            else:
                if self.current_frame < len(self.frames) - 1:
                    self.current_frame += 1
                else:
                    self.finished = True

    # ==========================================================
    # RESET
    # ==========================================================

    def reset(self):

        self.current_frame = 0
        self.timer = 0
        self.finished = False

    # ==========================================================
    # GET FRAME
    # ==========================================================

    def get_frame(self):

        if not self.frames:
            return None

        return self.frames[self.current_frame]