# file: core/game.py

import os

import pygame

from config.paths import SPRITES_PATH, MAP_PATH
from core.ghost import Ghost
from core.map_system import MapSystem
from core.player import Player
from systems.audio import Audio
from systems.fruit import Fruit


class Game:

    def __init__(self, screen):
        self.initial_dots = None
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()

        self.level = 1
        self.game_over = False

        # ================= MAP =================
        map_paths = [
            os.path.join(MAP_PATH, f"map_{i}.png")
            for i in range(1, 11)
        ]
        self.map = MapSystem(map_paths)

        # ================= HUD =================
        self.HUD_RATIO = 0.07
        self.hud_height = int(self.height * self.HUD_RATIO)

        # ================= AUDIO =================
        self.audio = Audio()

        # ================= TILE SIZE =================
        self.update_tile_size()

        # ================= SPAWN =================
        self.PLAYER_SPAWN = self.find_player_spawn()
        if self.map.is_wall(*self.PLAYER_SPAWN):
            self.PLAYER_SPAWN = (1, 1)

        # ================= PLAYER =================
        self.player = Player(
            *self.PLAYER_SPAWN,
            self.map.tile_size,
            self.audio
        )

        # ================= GHOST CONFIG =================
        self.ghost_config = [
            (1, 14, 10, "Blinky"),
            (3, 13, 10, "Pinky"),
            (5, 15, 10, "Inky"),
            (7, 14, 9, "Clyde"),
        ]
        self.ghosts = []

        # ================= SYSTEMS =================
        self.fruit = None
        self.fruit_spawn_count = 0

        # ================= UI =================
        self.hud_font = pygame.font.SysFont("Arial", 22)
        self.big_font = pygame.font.SysFont("Arial", 48, bold=True)

        # ================= INIT LEVEL =================
        self.create_level()
        self.audio.play_start()

    # ================= LEVEL =================
    def create_level(self):

        self.map.load_random_map()
        self.update_tile_size()

        spawn_x, spawn_y = self.find_player_spawn()

        self.player.grid_x = spawn_x
        self.player.grid_y = spawn_y
        self.player.set_tile_size(self.map.tile_size)
        self.player.snap_to_grid()

        self.player.invincible = False
        self.player.power_mode = False

        self.fruit = Fruit(self.level, self.map)
        self.fruit_spawn_count = 0

        self.initial_dots = sum(
            tile in (".", "o")
            for row in self.map.maze
            for tile in row
        )

        self.ghosts.clear()
        base_speed = max(14 - self.level, 5)

        for lvl, x, y, name in self.ghost_config:
            if self.level < lvl:
                continue

            folder = os.path.join(SPRITES_PATH, name)
            if not os.path.exists(folder):
                continue

            self.ghosts.append(
                Ghost(x, y, folder, self.map.tile_size, base_speed)
            )

    # ================= SPAWN =================
    def find_player_spawn(self):

        cx = self.map.cols // 2
        cy = self.map.rows // 2

        if not self.map.is_wall(cx, cy):
            return cx, cy

        return self.map.get_random_empty_tile()

    # ================= TILE SIZE =================
    # file: core/game.py

    # ⚠️ SEULE MODIF IMPORTANTE ICI :
    # remplacer set_tile_size ghost par safe call

    def update_tile_size(self):

        w = self.screen.get_width()
        h = self.screen.get_height() - self.hud_height

        scale = min(w / self.map.cols, h / self.map.rows)
        tile_size = max(2, int(scale))

        self.map.set_tile_size(tile_size)

        if hasattr(self.map, "surface"):
            self.map.scaled_surface = pygame.transform.scale(
                self.map.surface,
                (self.map.cols * tile_size, self.map.rows * tile_size)
            )

        if hasattr(self, "player"):
            self.player.set_tile_size(tile_size)

        # ✅ FIX CRASH ICI
        for ghost in getattr(self, "ghosts", []):
            if hasattr(ghost, "set_tile_size"):
                ghost.set_tile_size(tile_size)
            else:
                ghost.tile_size = tile_size  # fallback

    # ================= RESIZE =================
    def resize(self, width, height):

        self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        self.width = width
        self.height = height
        self.hud_height = int(self.height * self.HUD_RATIO)
        self.update_tile_size()

        if hasattr(self, "player"):
            self.player.snap_to_grid()

        for ghost in self.ghosts:
            ghost.set_tile_size(self.map.tile_size)

    # ================= UPDATE =================
    def update(self):

        if self.game_over:
            return

        self.player.update(self.map)

        for ghost in self.ghosts:
            ghost.update(self.map, self.player.grid_x, self.player.grid_y)

        # collision ghosts
        for ghost in self.ghosts:
            if (ghost.x, ghost.y) == (self.player.grid_x, self.player.grid_y):

                if self.player.power_mode:
                    ghost.reset()
                    self.player.score += 200
                    continue

                if not self.player.invincible:
                    self.player.lives -= 1
                    self.player.reset_position()

                    if self.player.lives <= 0:
                        self.game_over = True
                    return

        # level complete
        if not self.map.remaining_dots():
            self.level += 1
            self.create_level()
            return

        # fruit logic
        remaining = sum(tile in (".", "o") for r in self.map.maze for tile in r)

        if self.initial_dots:
            progress = 1 - (remaining / self.initial_dots)

            if self.fruit_spawn_count == 0 and progress >= 0.3:
                self.fruit.spawn()
                self.fruit_spawn_count += 1

            elif self.fruit_spawn_count == 1 and progress >= 0.7:
                self.fruit.spawn()
                self.fruit_spawn_count += 1

        self.fruit.update()

        score = self.fruit.check_collision(self.player)
        if score:
            self.player.score += score

    # ================= DRAW =================
    def draw(self):

        w, h = self.screen.get_size()
        self.screen.fill((0, 0, 0))

        hud_h = int(h * self.HUD_RATIO)
        self._draw_hud(w, hud_h)

        ox, oy = self._compute_offset(w, h, hud_h)

        self._draw_map(ox, oy)
        self._draw_dots(ox, oy)
        self._draw_entities(ox, oy)

        if self.game_over:
            self._draw_game_over(w, h)

    # ================= DRAW HELPERS =================
    def _draw_hud(self, w, h):
        pygame.draw.rect(self.screen, (20, 20, 40), (0, 0, w, h))

        text = self.hud_font.render(f"Score: {self.player.score}", True, (255, 255, 0))
        self.screen.blit(text, (20, 5))

    def _compute_offset(self, w, h, hud_h):
        map_w = self.map.cols * self.map.tile_size
        map_h = self.map.rows * self.map.tile_size

        return (
            (w - map_w) // 2,
            hud_h + (h - hud_h - map_h) // 2
        )

    def _draw_map(self, ox, oy):
        if hasattr(self.map, "scaled_surface"):
            self.screen.blit(self.map.scaled_surface, (ox, oy))

    def _draw_dots(self, ox, oy):
        ts = self.map.tile_size

        for y, row in enumerate(self.map.maze):
            for x, tile in enumerate(row):

                px = ox + x * ts + ts // 2
                py = oy + y * ts + ts // 2

                if tile == ".":
                    pygame.draw.circle(self.screen, (255, 255, 0), (px, py), ts // 8)

                elif tile == "o":
                    pygame.draw.circle(self.screen, (255, 255, 255), (px, py), ts // 4)

    def _draw_entities(self, ox, oy):

        if self.fruit:
            self.fruit.draw(self.screen, ox, oy, self.map.tile_size)

        for ghost in self.ghosts:
            ghost.draw(self.screen, ox, oy)

        self.player.draw(self.screen, ox, oy)

    def _draw_game_over(self, w, h):
        overlay = pygame.Surface((w, h))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        text = self.big_font.render("GAME OVER", True, (255, 0, 0))
        self.screen.blit(
            text,
            (w // 2 - text.get_width() // 2, h // 2 - 40)
        )
    # ==================================================
    # UPDATE
    # ==================================================
    def update(self):

        if self.game_over:
            if pygame.mouse.get_pressed()[0]:
                self.restart_game()
            return

        # =============================
        # UPDATE PLAYER
        # =============================
        self.player.update(self.map)

        # =============================
        # UPDATE GHOSTS
        # =============================
        for ghost in self.ghosts:
            ghost.update(self.map, self.player.grid_x, self.player.grid_y)

        # =============================
        # COLLISIONS PLAYER / GHOSTS
        # =============================
        for ghost in self.ghosts:

            if ghost.spawn_delay > 0:
                continue

            if (ghost.x, ghost.y) == (self.player.grid_x, self.player.grid_y):

                # POWER MODE → mange ghost
                if self.player.power_mode:
                    ghost.reset()
                    self.player.score += 200
                    self.audio.play_chomp()
                    continue

                # PLAYER HIT
                if not self.player.invincible:

                    self.player.lives -= 1
                    self.player.is_dead = True

                    if self.player.lives <= 0:
                        self.player.game_over = True
                        self.game_over = True
                        return

                    # reset positions
                    self.player.reset_position()

                    for g in self.ghosts:
                        g.reset()

                    return

        # =============================
        # CHECK FIN DE LEVEL
        # =============================
        if not self.map.remaining_dots():
            self.level += 1
            self.create_level()
            return

        # =============================
        # FRUIT SYSTEM
        # =============================
        total_remaining = sum(
            tile in (".", "o")
            for row in self.map.maze
            for tile in row
        )

        if not hasattr(self, "initial_dots"):
            self.initial_dots = total_remaining

        progress = 1 - (total_remaining / self.initial_dots)

        if self.fruit_spawn_count == 0 and progress >= 0.3:
            self.fruit.spawn()
            self.fruit_spawn_count += 1

        elif self.fruit_spawn_count == 1 and progress >= 0.7:
            self.fruit.spawn()
            self.fruit_spawn_count += 1

        self.fruit.update()

        # =============================
        # COLLISION PLAYER / FRUIT (FIX CLEAN)
        # =============================
        score = self.fruit.check_collision(self.player)

        if score > 0:
            self.player.score += score
            self.audio.play_eatghost()

        # =============================
        # COLLISION PLAYER / FRUIT
        # =============================
        if self.fruit.visible:

            if (self.player.grid_x, self.player.grid_y) == (self.fruit.grid_x, self.fruit.grid_y):
                self.player.score += self.fruit.score_value
                self.fruit.visible = False
                self.audio.play_eatghost()

    # ==================================================
    # DRAW
    # ==================================================
    def draw(self):
        screen_w = self.screen.get_width()
        screen_h = self.screen.get_height()

        self.screen.fill((0, 0, 0))

        # ================= HUD =================
        hud_h = int(screen_h * self.HUD_RATIO)
        self._draw_hud(screen_w, hud_h)

        # ================= MAP OFFSET =================
        offset_x, offset_y = self._compute_map_offset(screen_w, screen_h, hud_h)

        # ================= MAP =================
        self._draw_map(offset_x, offset_y)

        # ================= DOTS (FIX VISUEL) =================
        self._draw_dots(offset_x, offset_y)

        # ================= ENTITIES =================
        self._draw_entities(offset_x, offset_y)

        # ================= GAME OVER =================
        if self.game_over:
            self._draw_game_over(screen_w, screen_h)

            print("Player screen:", offset_x + self.player.x, offset_y + self.player.y)

    # ==================================================
    # HUD
    # ==================================================
    def _draw_hud(self, screen_w, hud_h):
        pygame.draw.rect(self.screen, (15, 15, 35), (0, 0, screen_w, hud_h))

        score = self.hud_font.render(f"Score: {self.player.score}", True, (255, 255, 0))
        lives = self.hud_font.render(f"Vies: {self.player.lives}", True, (255, 255, 255))
        level = self.hud_font.render(f"Niveau: {self.level}", True, (0, 255, 255))

        y = hud_h // 2 - score.get_height() // 2

        self.screen.blit(score, (20, y))
        self.screen.blit(lives, (screen_w // 2 - lives.get_width() // 2, y))
        self.screen.blit(level, (screen_w - level.get_width() - 20, y))

    # ==================================================
    # OFFSET MAP
    # ==================================================
    def _compute_map_offset(self, screen_w, screen_h, hud_h):
        map_w = self.map.cols * self.map.tile_size
        map_h = self.map.rows * self.map.tile_size

        offset_x = (screen_w - map_w) // 2
        offset_y = hud_h + (screen_h - hud_h - map_h) // 2

        return offset_x, offset_y

    # ==================================================
    # MAP
    # ==================================================
    # noinspection PyUnresolvedReferences
    def _draw_map(self, offset_x, offset_y):
        if hasattr(self.map, "scaled_surface"):
            self.screen.blit(self.map.scaled_surface, (offset_x, offset_y))
        else:
            return

    # ==================================================
    # DOTS (CRUCIAL)
    # ==================================================
    def _draw_dots(self, offset_x, offset_y):
        ts = self.map.tile_size

        for y, row in enumerate(self.map.maze):
            for x, tile in enumerate(row):

                px = offset_x + x * ts + ts // 2
                py = offset_y + y * ts + ts // 2

                if tile == ".":
                    pygame.draw.circle(self.screen, (255, 255, 0), (px, py), ts // 8)

                elif tile == "o":
                    pygame.draw.circle(self.screen, (255, 255, 255), (px, py), ts // 4)

    # ==================================================
    # ENTITIES
    # ==================================================
    def _draw_entities(self, offset_x, offset_y):

        if self.fruit:
            self.fruit.draw(self.screen, offset_x, offset_y, self.map.tile_size)

        for ghost in self.ghosts:
            ghost.draw(self.screen, offset_x, offset_y)

        self.player.draw(self.screen, offset_x, offset_y)  # 🔥 TOUJOURS EN DERNIER

    # ==================================================
    # GAME OVER
    # ==================================================
    # noinspection PyUnresolvedReferences
    def _draw_game_over(self, screen_w, screen_h):
        overlay = pygame.Surface(self.screen.get_size())
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        go = self.big_font.render("GAME OVER", True, (255, 0, 0))
        restart = self.hud_font.render("Press R to Restart", True, (255, 255, 255))

        self.screen.blit(go, (screen_w // 2 - go.get_width() // 2, screen_h // 2 - 40))
        self.screen.blit(restart, (screen_w // 2 - restart.get_width() // 2, screen_h // 2 + 10))

    # ==================================================
    # RESET GAME
    # ==================================================
    def reset_full_game(self):
        self.level = 1
        self.player.lives = self.player.max_lives
        self.player.score = 0
        self.player.game_over = False
        self.player.is_dead = False
        self.game_over = False
        self.create_level()

    # ==================================================
    # RESTART GAME
    # ==================================================
    def restart_game(self):
        self.level = 1
        self.player.score = 0
        self.player.lives = self.player.max_lives
        self.player.game_over = False
        self.player.is_dead = False
        self.game_over = False
        self.create_level()
