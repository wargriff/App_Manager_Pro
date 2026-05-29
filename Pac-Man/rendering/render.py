import pygame

# couleurs simples
COLOR_WALL = (0, 0, 255)
COLOR_FLOOR = (0, 0, 0)
COLOR_DOT = (255, 255, 255)
COLOR_POWER = (255, 255, 0)


def draw_map(screen, map_obj, offset_x=0, offset_y=0):

    tile_size = map_obj.tile_size

    for y in range(map_obj.rows):
        for x in range(map_obj.cols):

            tile = map_obj.maze[y][x]

            px = offset_x + x * tile_size
            py = offset_y + y * tile_size

            rect = pygame.Rect(px, py, tile_size, tile_size)

            # ===== FLOOR =====
            pygame.draw.rect(screen, COLOR_FLOOR, rect)

            # ===== WALL =====
            if tile == "#":
                pygame.draw.rect(screen, COLOR_WALL, rect)

            # ===== DOT =====
            elif tile == ".":
                pygame.draw.circle(
                    screen,
                    COLOR_DOT,
                    rect.center,
                    tile_size // 6
                )

            # ===== POWER =====
            elif tile == "o":
                pygame.draw.circle(
                    screen,
                    COLOR_POWER,
                    rect.center,
                    tile_size // 3
                )