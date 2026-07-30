import pygame
import sys
import settings

from menu import MainMenu
from game import Game
from shop import Shop
from garage import Garage
from settings_menu import SettingsMenu
from save import SaveManager





def main():
    pygame.init()
   


    flags = pygame.FULLSCREEN if settings.FULLSCREEN else 0
    menu = MainMenu(screen)
    game = Game(screen)

    shop = Shop(screen)
    save = SaveManager()
    save.load()

    garage = Garage(screen, save, screen)

    settings = SettingsMenu(screen)
    screen = pygame.display.set_mode(
        (settings.WIDTH, settings.HEIGHT),
        flags
    )

    pygame.display.set_caption("Pražská honička")

    clock = pygame.time.Clock()

    menu = MainMenu(screen)
    game = Game(screen)
    shop = Shop(screen)
    garage = Garage(screen)
    settings_menu = SettingsMenu(screen)

    state = "menu"

    while True:

        dt = clock.tick(settings.FPS) / 1000.0

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # ================= MENU =================

            if state == "menu":

                result = menu.handle_event(event)

                if result == "start":
                    game.reset()
                    state = "game"

                elif result == "shop":
                    state = "shop"

                elif result == "garage":
                    state = "garage"

                elif result == "settings":
                    state = "settings"

                elif result == "quit":
                    pygame.quit()
                    sys.exit()

            # ================= GAME =================

            elif state == "game":

                result = game.handle_event(event)

                if result == "menu":
                    state = "menu"

            # ================= SHOP =================

            elif state == "shop":

                result = shop.handle_event(event)

                if result == "menu":
                    state = "menu"

            # ================= GARAGE =================

            elif state == "garage":

                result = garage.handle_event(event)

                if result == "menu":
                    state = "menu"

            # ================= SETTINGS =================

            elif state == "settings":

                result = settings_menu.handle_event(event)

                if result == "menu":
                    state = "menu"

                elif result == "fullscreen_changed":

                    flags = pygame.FULLSCREEN if settings.FULLSCREEN else 0

                    screen = pygame.display.set_mode(
                        (settings.WIDTH, settings.HEIGHT),
                        flags
                    )

                    menu.screen = screen
                    game.screen = screen
                    shop.screen = screen
                    garage.screen = screen
                    settings_menu.screen = screen

        # ================= DRAW =================

        if state == "menu":

            menu.update(dt)
            menu.draw()

        elif state == "game":

            game.update(dt)
            game.draw()

            if game.game_over:
                state = "menu"

        elif state == "shop":

            shop.update(dt)
            shop.draw()

        elif state == "garage":

            garage.update(dt)
            garage.draw()

        elif state == "settings":

            settings_menu.update(dt)
            settings_menu.draw()

        pygame.display.flip()


if __name__ == "__main__":
    main()