import os

import pygame

from core.game_play import Game
from systems.menu import Menu, GameOverUI

# Fix audio Windows / PyInstaller
os.environ["SDL_AUDIODRIVER"] = "directsound"

pygame.init()

# ==============================
# AUDIO SAFE INIT
# ==============================
try:
    pygame.mixer.init(
        frequency=44100,
        size=-16,
        channels=2,
        buffer=512
    )
    print("✅ Mixer initialized:", pygame.mixer.get_init())
except pygame.error:
    print("⚠️ Audio désactivé")

# ==============================
# WINDOW CONFIG
# ==============================
START_WIDTH = 900
START_HEIGHT = 700

screen = pygame.display.set_mode(
    (START_WIDTH, START_HEIGHT),
    pygame.RESIZABLE
)

pygame.display.set_caption("Pac-Man Python")
clock = pygame.time.Clock()

# ==============================
# STATES
# ==============================
MENU = "menu"
GAME = "game"
GAME_OVER = "game_over"
WIN = "win"

state = MENU

# ==============================
# INSTANCES
# ==============================
game = Game(screen)
menu = Menu(screen)
game_over_ui = GameOverUI(screen)

font_big = pygame.font.SysFont("Arial", 70, bold=True)
font_small = pygame.font.SysFont("Arial", 32)

running = True

# ==============================
# MAIN LOOP
# ==============================
while running:

    clock.tick(60)

    # =============================
    # EVENTS
    # =============================
    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        # ---------- RESIZE ----------
        elif event.type == pygame.VIDEORESIZE:

            screen = pygame.display.set_mode(
                (event.w, event.h),
                pygame.RESIZABLE
            )

            # Update toutes les refs écran
            game.resize(event.w, event.h)
            game.screen = screen
            menu.screen = screen
            game_over_ui.screen = screen

        # ---------- KEYBOARD ----------
        elif event.type == pygame.KEYDOWN:

            if state == MENU and event.key == pygame.K_RETURN:
                game.reset_full_game()
                state = GAME

            elif state == WIN and event.key == pygame.K_RETURN:
                game.restart_game()
                state = MENU

        # ---------- GAME OVER ----------
        elif state == GAME_OVER:
            if game_over_ui.handle_event(event):
                game.restart_game()
                state = MENU

    # =============================
    # UPDATE
    # =============================
    if state == GAME:

        game.update()

        if game.game_over:
            state = GAME_OVER

        elif game.level >= 10:
            state = WIN

    # =============================
    # DRAW
    # =============================
    screen.fill((10, 10, 25))

    if state == MENU:
        menu.draw()

    elif state == GAME:
        game.draw()

    elif state == GAME_OVER:
        game.draw()
        game_over_ui.draw()

    elif state == WIN:

        game.draw()

        width = screen.get_width()
        height = screen.get_height()

        center_x = width // 2
        center_y = height // 2

        overlay = pygame.Surface((width, height))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))

        win_text = font_big.render("VICTOIRE !", True, (0, 255, 0))
        retry_text = font_small.render(
            "Appuie sur ENTER pour rejouer",
            True,
            (255, 255, 255)
        )

        screen.blit(
            win_text,
            (center_x - win_text.get_width() // 2, center_y - 100)
        )

        screen.blit(
            retry_text,
            (center_x - retry_text.get_width() // 2, center_y)
        )

    pygame.display.flip()

pygame.quit()