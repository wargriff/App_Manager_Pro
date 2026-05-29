import pygame


class Menu:

    def __init__(self, screen):

        self.screen = screen

        self.font_big = pygame.font.SysFont("Arial", 70, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 32)

    # ----------------------------------
    # DRAW MENU
    # ----------------------------------
    def draw(self):

        width = self.screen.get_width()
        height = self.screen.get_height()
        center_x = width // 2

        title = self.font_big.render("PAC-MAN", True, (255, 255, 0))
        start_text = self.font_small.render(
            "Appuie sur ENTREE pour jouer",
            True,
            (255, 255, 255)
        )

        self.screen.blit(
            title,
            (center_x - title.get_width() // 2, int(height * 0.3))
        )

        self.screen.blit(
            start_text,
            (center_x - start_text.get_width() // 2, int(height * 0.45))
        )


class GameOverUI:

    def __init__(self, screen):
        self.screen = screen

        self.font_big = pygame.font.SysFont("Arial", 90, bold=True)
        self.font_button = pygame.font.SysFont("Arial", 40, bold=True)

        self.button_rect = pygame.Rect(0, 0, 280, 90)

    def draw(self):

        width = self.screen.get_width()
        height = self.screen.get_height()

        center_x = width // 2
        center_y = height // 2

        # Overlay sombre
        overlay = pygame.Surface((width, height))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Titre
        title = self.font_big.render("GAME OVER", True, (255, 0, 0))
        self.screen.blit(
            title,
            (center_x - title.get_width() // 2, center_y - 180)
        )

        # Position bouton
        self.button_rect.center = (center_x, center_y)

        mouse_pos = pygame.mouse.get_pos()
        hovered = self.button_rect.collidepoint(mouse_pos)

        # Couleur dynamique
        color = (255, 60, 60) if hovered else (180, 0, 0)

        # Ombre
        shadow = self.button_rect.copy()
        shadow.y += 6
        pygame.draw.rect(self.screen, (0, 0, 0), shadow, border_radius=18)

        # Bouton
        pygame.draw.rect(self.screen, color, self.button_rect, border_radius=18)

        # Bordure
        pygame.draw.rect(self.screen, (255, 255, 255), self.button_rect, 3, border_radius=18)

        # Texte
        text = self.font_button.render("RESTART", True, (255, 255, 255))
        self.screen.blit(
            text,
            (
                self.button_rect.centerx - text.get_width() // 2,
                self.button_rect.centery - text.get_height() // 2
            )
        )

    def handle_event(self, event):

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.button_rect.collidepoint(event.pos):
                    return True

        return False