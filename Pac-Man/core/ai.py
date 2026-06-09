import random
from collections import deque


class GhostAI:

    def __init__(self, ghost):
        self.ghost = ghost
        self.timer = 0

        self.mode = "CHASE"
        self.mode_timer = 0
        self.frightened_timer = 0

        self.scatter_target = (0, 0)
        self.last_move = (0, 0)

        # Ghost un peu plus rapide
        self.base_speed = ghost.speed
        self.chase_speed = max(ghost.speed - 1, 1)
        self.frightened_speed = ghost.speed + 1

    # --------------------------------------------------
    # UPDATE
    # --------------------------------------------------
    def update(self, maze, player_x, player_y):

        self.mode_timer += 1

        # ===== GESTION MODE FRIGHTENED =====
        if self.mode == "FRIGHTENED":
            self.frightened_timer -= 1
            if self.frightened_timer <= 0:
                self.mode = "CHASE"

        else:
            # Alterne CHASE / SCATTER
            if self.mode_timer > 400:
                self.mode = "SCATTER" if self.mode == "CHASE" else "CHASE"
                self.mode_timer = 0

        # ===== VITESSE SELON MODE =====
        if self.mode == "CHASE":
            speed = self.chase_speed
        elif self.mode == "SCATTER":
            speed = self.base_speed
        else:
            speed = self.frightened_speed

        self.timer += 1
        if self.timer < speed:
            return 0, 0

        self.timer = 0

        move = self.choose_direction(maze, player_x, player_y)
        self.last_move = move
        return move

    # --------------------------------------------------
    # CHOIX DIRECTION (BFS INTELLIGENT)
    # --------------------------------------------------
    def choose_direction(self, maze, player_x, player_y):

        if self.mode == "FRIGHTENED":
            return self.frightened_move(maze, player_x, player_y)

        if self.mode == "CHASE":
            target = (player_x, player_y)
        else:
            target = self.scatter_target

        return self.bfs_next_step(maze, target)

    # --------------------------------------------------
    # BFS PATHFINDING
    # --------------------------------------------------
    def bfs_next_step(self, maze, target):

        start = (self.ghost.x, self.ghost.y)
        queue = deque([start])
        came_from = {start: None}

        directions = [(1,0),(-1,0),(0,1),(0,-1)]

        while queue:
            x, y = queue.popleft()

            if (x, y) == target:
                break

            for dx, dy in directions:
                nx, ny = x + dx, y + dy

                if not self.valid_tile(maze, nx, ny):
                    continue

                if (nx, ny) not in came_from:
                    queue.append((nx, ny))
                    came_from[(nx, ny)] = (x, y)

        # Pas trouvé
        if target not in came_from:
            return self.random_move(maze)

        # Remonte chemin
        current = target
        while came_from[current] != start:
            current = came_from[current]
            if current is None:
                return self.random_move(maze)

        dx = current[0] - start[0]
        dy = current[1] - start[1]

        # Empêche demi-tour immédiat
        if (dx, dy) == (-self.last_move[0], -self.last_move[1]):
            return self.random_move(maze)

        return dx, dy

    # --------------------------------------------------
    # FRIGHTENED (FUIT JOUEUR)
    # --------------------------------------------------
    def frightened_move(self, maze, player_x, player_y):

        directions = [(1,0),(-1,0),(0,1),(0,-1)]
        random.shuffle(directions)

        best_move = (0, 0)
        best_distance = -1

        for dx, dy in directions:

            nx = self.ghost.x + dx
            ny = self.ghost.y + dy

            if not self.valid_tile(maze, nx, ny):
                continue

            # Empêche demi-tour
            if (dx, dy) == (-self.last_move[0], -self.last_move[1]):
                continue

            distance = abs(nx - player_x) + abs(ny - player_y)

            if distance > best_distance:
                best_distance = distance
                best_move = (dx, dy)

        return best_move

    # --------------------------------------------------
    # RANDOM MOVE SAFE
    # --------------------------------------------------
    def random_move(self, maze):

        directions = [(1,0),(-1,0),(0,1),(0,-1)]
        random.shuffle(directions)

        for dx, dy in directions:
            nx = self.ghost.x + dx
            ny = self.ghost.y + dy

            if not self.valid_tile(maze, nx, ny):
                continue

            if (dx, dy) == (-self.last_move[0], -self.last_move[1]):
                continue

            return dx, dy

        return 0, 0

    # --------------------------------------------------
    # VALIDATION CASE
    # --------------------------------------------------
    def valid_tile(self, maze, x, y):
        if y < 0 or y >= len(maze):
            return False
        if x < 0 or x >= len(maze[0]):
            return False
        if maze[y][x] == "#":
            return False
        return True

    # --------------------------------------------------
    # ACTIVE FRIGHTENED MODE
    # --------------------------------------------------
    def frighten(self, duration=300):
        self.mode = "FRIGHTENED"
        self.frightened_timer = duration