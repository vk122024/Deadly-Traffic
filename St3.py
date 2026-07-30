rendering as of block 2, via the free test camera.
        # Block 3 swaps in the player sprite/physics on top of this;
        # the City.draw() call itself will not need to change.
        self.city.draw(self.screen, self._camera_x, self._camera_y)

        # Debug marker for the reserved easter egg location so its
        # cleared, building-free plot is visible while testing.
        ex, ey = EASTER_EGG_WORLD_POS
        screen_x = int(ex - self._camera_x + self.screen.get_width() / 2)
        screen_y = int(ey - self._camera_y + self.screen.get_height() / 2)
        pygame.draw.circle(self.screen, COLOR_ACCENT, (screen_x, screen_y), 8, width=2)

        district = self.city.district_at(self._camera_x, self._camera_y)
        info_surf = self.fonts.small.render(
            f"{district}  |  WASD/arrows to look around  |  Esc: {self.t('menu.back')}",
            True, COLOR_TEXT_DIM,
        )
        self.screen.blit(info_surf, (10, 10))

    def _draw_fps(self) -> None:
        fps = self.clock.get_fps()
        surf = self.fonts.small.render(f"{self.t('hud.fps')}: {fps:0.0f}", True, COLOR_TEXT_DIM)
        rect = surf.get_rect(topright=(self.screen.get_width() - 10, 10))
        self.screen.blit(surf, rect)


# --------------------------------------------------------------------------
# ENTRY POINT
# --------------------------------------------------------------------------


def main() -> None:
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
  
