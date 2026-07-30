import pygame
import settings


class SettingsMenu:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont("Arial", 40)

        self.selected = 0
        self.options = ["FPS", "Fullscreen", "Zpět"]

        self.fps_values = [30, 60, 120]
        self.fps_index = self.fps_values.index(settings.FPS)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % len(self.options)

            elif event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % len(self.options)

            elif event.key == pygame.K_LEFT:
                if self.selected == 0:
                    self.fps_index = (self.fps_index - 1) % len(self.fps_values)
                    settings.FPS = self.fps_values[self.fps_index]

            elif event.key == pygame.K_RIGHT:
                if self.selected == 0:
                    self.fps_index = (self.fps_index + 1) % len(self.fps_values)
                    settings.FPS = self.fps_values[self.fps_index]

            elif event.key == pygame.K_RETURN:

                if self.selected == 1:
                    settings.FULLSCREEN = not settings.FULLSCREEN
                    return "fullscreen_changed"

                elif self.selected == 2:
                    return "menu"

            elif event.key == pygame.K_ESCAPE:
                return "menu"

        return None

    def update(self, dt):
        pass

    def draw(self):
        self.screen.fill((25, 25, 25))

        title = self.font.render("NASTAVENÍ", True, (255, 255, 255))
        self.screen.blit(title, (settings.WIDTH // 2 - title.get_width() // 2, 80))

        texts = [
            f"FPS: {settings.FPS}",
            f"Fullscreen: {'ON' if settings.FULLSCREEN else 'OFF'}",
            "Zpět"
        ]

        y = 220

        for i, text in enumerate(texts):

            color = (255, 220, 0) if i == self.selected else (255, 255, 255)

            render = self.font.render(text, True, color)
            self.screen.blit(render, (settings.WIDTH // 2 - render.get_width() // 2, y))

            y += 70
