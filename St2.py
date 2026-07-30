half = ROAD_WIDTH / 2
                # Crosswalk stripes on all four approaches.
                for dx, dy, horizontal in (
                    (0, -half - 30, True), (0, half + 15, True),
                    (-half - 30, 0, False), (half + 15, 0, False),
                ):
                    self._draw_crosswalk(cx + dx, cy + dy, horizontal)

    def _draw_crosswalk(self, cx: float, cy: float, horizontal: bool) -> None:
        stripe_len = 24
        gap = 8
        count = 6
        for i in range(count):
            if horizontal:
                x = cx - (count * (stripe_len + gap)) / 2 + i * (stripe_len + gap)
                rect = pygame.Rect(int(x), int(cy - 6), stripe_len, 12)
            else:
                y = cy - (count * (stripe_len + gap)) / 2 + i * (stripe_len + gap)
                rect = pygame.Rect(int(cx - 6), int(y), 12, stripe_len)
            pygame.draw.rect(self.surface, (230, 230, 225), rect)

    def _draw_traffic_lights(self) -> None:
        for v_seg in (s for s in self.road_segments if s.orientation == "v"):
            for h_seg in (s for s in self.road_segments if s.orientation == "h"):
                cx, cy = v_seg.offset, h_seg.offset
                half = ROAD_WIDTH / 2
                for px, py in (
                    (cx - half - 12, cy - half - 12),
                    (cx + half + 12, cy - half - 12),
                    (cx - half - 12, cy + half + 12),
                    (cx + half + 12, cy + half + 12),
                ):
                    pygame.draw.rect(self.surface, (25, 25, 28), (int(px) - 4, int(py) - 10, 8, 20))
                    pygame.draw.circle(self.surface, (60, 200, 90), (int(px), int(py) - 10), 4)

    def _maybe_draw_roundabout(self, rng: random.Random) -> None:
        if (self.chunk_x + self.chunk_y) % 4 != 0:
            return
        cx, cy = CHUNK_ROAD_OFFSETS[0], CHUNK_ROAD_OFFSETS[1]
        outer_r = ROAD_WIDTH * 0.9
        inner_r = ROAD_WIDTH * 0.4
        pygame.draw.circle(self.surface, (150, 148, 145), (int(cx), int(cy)), int(outer_r))
        pygame.draw.circle(self.surface, (48, 48, 52), (int(cx), int(cy)), int(outer_r - 10))
        pygame.draw.circle(self.surface, (70, 130, 70), (int(cx), int(cy)), int(inner_r))

    def _generate_blocks(self, rng: random.Random, palette: dict) -> None:
        world_x0, world_y0 = self.world_origin()
        offsets = (0.0,) + CHUNK_ROAD_OFFSETS + (CHUNK_SIZE,)
        margin = ROAD_WIDTH / 2 + SIDEWALK_WIDTH + 10

        for i in range(len(offsets) - 1):
            for j in range(len(offsets) - 1):
                bx0 = offsets[i] + margin
                bx1 = offsets[i + 1] - margin
                by0 = offsets[j] + margin
                by1 = offsets[j + 1] - margin
                if bx1 <= bx0 or by1 <= by0:
                    continue

                block_rect_local = pygame.Rect(int(bx0), int(by0), int(bx1 - bx0), int(by1 - by0))
                block_world = block_rect_local.move(world_x0, world_y0)
                if self._overlaps_easter_egg_clearing(block_world):
                    continue

                roll = rng.random()
                if roll < 0.18:
                    self._fill_park(block_rect_local, block_world, rng)
                elif roll < 0.26:
                    self._fill_parking_lot(block_rect_local, block_world)
                else:
                    self._fill_buildings(block_rect_local, block_world, rng, palette)

    def _fill_park(self, local_rect: pygame.Rect, world_rect: pygame.Rect, rng: random.Random) -> None:
        pygame.draw.rect(self.surface, (74, 128, 68), local_rect, border_radius=10)
        for _ in range(6):
            tx = rng.randint(local_rect.left + 10, max(local_rect.left + 11, local_rect.right - 10))
            ty = rng.randint(local_rect.top + 10, max(local_rect.top + 11, local_rect.bottom - 10))
            pygame.draw.circle(self.surface, (54, 100, 50), (tx, ty), rng.randint(8, 16))
        self.parks.append(world_rect)

    def _fill_parking_lot(self, local_rect: pygame.Rect, world_rect: pygame.Rect) -> None:
        pygame.draw.rect(self.surface, (72, 72, 78), local_rect)
        stripe_gap = 34
        x = local_rect.left + 10
        while x < local_rect.right - 10:
            pygame.draw.line(
                self.surface, (200, 200, 200),
                (x, local_rect.top + 6), (x, local_rect.bottom - 6), 3,
            )
            x += stripe_gap
        self.parking_lots.append(world_rect)

    def _fill_buildings(
        self, local_rect: pygame.Rect, world_rect: pygame.Rect, rng: random.Random, palette: dict
    ) -> None:
        weights = DISTRICT_BUILDING_WEIGHTS[self.district]
        lot_size = 78
        gap = 12
        y = local_rect.top
        while y + lot_size <= local_rect.bottom:
            x = local_rect.left
            while x + lot_size <= local_rect.right:
                if rng.random() < 0.85:
                    kind = weighted_choice(rng, weights)
                    w = lot_size - rng.randint(0, 10)
                    h = lot_size - rng.randint(0, 10)
                    local_b_rect = pygame.Rect(x, y, w, h)
                    world_b_rect = local_b_rect.move(*self.world_origin())
                    if not self._overlaps_easter_egg_clearing(world_b_rect):
                        base = tuple(
                            min(255, max(0, c + rng.randint(-14, 14))) for c in palette["base"]
                        )
                        trim = palette["trim"]
                        pygame.draw.rect(self.surface, trim, local_b_rect.inflate(6, 6))
                        pygame.draw.rect(self.surface, BUILDING_KIND_COLORS[kind], local_b_rect, width=0)
                        inner = local_b_rect.inflate(-8, -8)
                        pygame.draw.rect(self.surface, base, inner)
                        has_tram_stop = kind == "office" and rng.random() < 0.1
                        self.buildings.append(
                            Building(
                                rect=world_b_rect, kind=kind, district=self.district,
                                base_color=base, trim_color=trim, has_tram_stop=has_tram_stop,
                            )
                        )
                x += lot_size + gap
            y += lot_size + gap

    def _overlaps_easter_egg_clearing(self, world_rect: pygame.Rect) -> bool:
        ex, ey = EASTER_EGG_WORLD_POS
        closest_x = max(world_rect.left, min(ex, world_rect.right))
        closest_y = max(world_rect.top, min(ey, world_rect.bottom))
        return math.hypot(ex - closest_x, ey - closest_y) < EASTER_EGG_CLEAR_RADIUS

    def _carve_easter_egg_clearing(self) -> None:
        ex, ey = EASTER_EGG_WORLD_POS
        wx0, wy0 = self.world_origin()
        local_x, local_y = ex - wx0, ey - wy0
        if -EASTER_EGG_CLEAR_RADIUS <= local_x <= CHUNK_SIZE + EASTER_EGG_CLEAR_RADIUS and \
           -EASTER_EGG_CLEAR_RADIUS <= local_y <= CHUNK_SIZE + EASTER_EGG_CLEAR_RADIUS:
            pygame.draw.circle(
                self.surface, (86, 132, 78), (int(local_x), int(local_y)), EASTER_EGG_CLEAR_RADIUS
            )


class City:
    """Owns all loaded chunks and answers world-level queries: draw the
    visible area for a camera, and check collision/road-surface state
    at a world point. Chunks are generated lazily and cached forever
    (the world is deterministic, so re-generating would be wasteful and
    would also invalidate any per-chunk state added by later blocks)."""

    def __init__(self, assets: Assets) -> None:
        self.assets = assets
        self.chunks: dict[tuple[int, int], Chunk] = {}

    def get_chunk(self, chunk_x: int, chunk_y: int) -> Chunk:
        key = (chunk_x, chunk_y)
        chunk = self.chunks.get(key)
        if chunk is None:
            chunk = Chunk(chunk_x, chunk_y, self.assets)
            self.chunks[key] = chunk
        return chunk

    def chunk_coords_for_point(self, world_x: float, world_y: float) -> tuple[int, int]:
        return (math.floor(world_x / CHUNK_SIZE), math.floor(world_y / CHUNK_SIZE))

    def draw(self, surface: pygame.Surface, camera_x: float, camera_y: float) -> None:
        view_w, view_h = surface.get_size()
        half_w, half_h = view_w / 2, view_h / 2

        start_cx = math.floor((camera_x - half_w) / CHUNK_SIZE) - 1
        end_cx = math.floor((camera_x + half_w) / CHUNK_SIZE) + 1
        start_cy = math.floor((camera_y - half_h) / CHUNK_SIZE) - 1
        end_cy = math.floor((camera_y + half_h) / CHUNK_SIZE) + 1

        for cx in range(start_cx, end_cx + 1):
            for cy in range(start_cy, end_cy + 1):
                chunk = self.get_chunk(cx, cy)
                screen_x = int(cx * CHUNK_SIZE - camera_x + half_w)
                screen_y = int(cy * CHUNK_SIZE - camera_y + half_h)
                surface.blit(chunk.surface, (screen_x, screen_y))

    def collides_with_building(self, world_rect: pygame.Rect) -> Optional[Building]:
        """Check only the (at most 3x3) chunks the rect could touch."""
        cx0, cy0 = self.chunk_coords_for_point(world_rect.left, world_rect.top)
        cx1, cy1 = self.chunk_coords_for_point(world_rect.right, world_rect.bottom)
        for cx in range(cx0, cx1 + 1):
            for cy in range(cy0, cy1 + 1):
                chunk = self.get_chunk(cx, cy)
                for b in chunk.buildings:
                    if b.rect.colliderect(world_rect):
                        return b
        return None

    def is_on_road(self, world_x: float, world_y: float) -> bool:
        cx, cy = self.chunk_coords_for_point(world_x, world_y)
        chunk = self.get_chunk(cx, cy)
        if chunk.is_river:
            return False
        local_x = world_x - cx * CHUNK_SIZE
        local_y = world_y - cy * CHUNK_SIZE
        half = ROAD_WIDTH / 2
        for seg in chunk.road_segments:
            if seg.orientation == "v" and abs(local_x - seg.offset) <= half:
                return True
            if seg.orientation == "h" and abs(local_y - seg.offset) <= half:
                return True
        return False

    def district_at(self, world_x: float, world_y: float) -> str:
        cx, cy = self.chunk_coords_for_point(world_x, world_y)
        return self.get_chunk(cx, cy).district


# --------------------------------------------------------------------------
# SIMPLE UI HELPERS (placeholder-level for block 1; the menu/HUD block
# will build richer widgets on top of these primitives without needing
# to change them).
# --------------------------------------------------------------------------


class Fonts:
    def __init__(self) -> None:
        pygame.font.init()
        self.small = pygame.font.SysFont("arial", 18)
        self.medium = pygame.font.SysFont("arial", 26)
        self.large = pygame.font.SysFont("arial", 48)
        self.huge = pygame.font.SysFont("arial", 72)


COLOR_BG = (18, 18, 22)
COLOR_TEXT = (235, 235, 240)
COLOR_TEXT_DIM = (150, 150, 158)
COLOR_ACCENT = (240, 190, 60)  # a Prague-gold accent used across menus/HUD
COLOR_PANEL = (32, 32, 38)
COLOR_ERROR = (220, 80, 80)


# --------------------------------------------------------------------------
# MAIN GAME CLASS
# --------------------------------------------------------------------------


class Game:
    def __init__(self) -> None:
        pygame.init()
        self.save = SaveGame.load()
        self.settings = self.save.settings

        flags = pygame.FULLSCREEN if self.settings.fullscreen else 0
        self.screen = pygame.display.set_mode(self.settings.resolution, flags)
        pygame.display.set_caption(WINDOW_TITLE)

        self.clock = pygame.time.Clock()
        self.fonts = Fonts()

        self.assets = Assets()
        self.assets.load()
        for err in self.assets.load_errors:
            print(f"[Assets] {err}", file=sys.stderr)

        self.state: AppState = AppState.MAIN_MENU
        self.running = True

        self._last_autosave_time = time.monotonic()
        self._autosave_interval_seconds = 10.0

        self._session_start_time = time.monotonic()

        # World is real as of block 2. Player/traffic/weather are still
        # populated by later blocks; driving state reuses this City
        # instance rather than rebuilding it.
        self.city: City = City(self.assets)
        self.player = None
        self.traffic = None
        self.weather_system = None

        # TEMPORARY free-look test camera for block 2, so the world can
        # be inspected while driving state exists but player physics
        # doesn't yet. Block 3 replaces every use of _camera_x/_camera_y
        # below with the real player's world position.
        self._camera_x, self._camera_y = EASTER_EGG_WORLD_POS
        self._camera_speed = 500.0  # world units / second

        # Placeholder-menu selection state used until the real menu
        # block replaces _handle_main_menu / _draw_main_menu.
        self._main_menu_options = [
            ("menu.play", AppState.DRIVING),
            ("menu.garage", AppState.GARAGE),
            ("menu.shop", AppState.SHOP),
            ("menu.settings", AppState.SETTINGS),
            ("menu.statistics", AppState.STATISTICS),
            ("menu.credits", AppState.CREDITS),
        ]
        self._main_menu_index = 0

    # ---------------------------------------------------------- language --
    @property
    def lang(self) -> str:
        return self.settings.language

    def t(self, key: str) -> str:
        return tr(self.lang, key)

    # -------------------------------------------------------------- loop --
    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(TARGET_FPS) / 1000.0
            dt = min(dt, 0.05)  # clamp huge stalls (alt-tab, breakpoints)

            self._handle_events()
            self._update(dt)
            self._draw()
            self._maybe_autosave()

        self.save.save()
        pygame.quit()

    def _maybe_autosave(self) -> None:
        now = time.monotonic()
        if now - self._last_autosave_time >= self._autosave_interval_seconds:
            self.save.statistics.time_played_seconds += now - self._last_autosave_time
            self.save.save()
            self._last_autosave_time = now

    # ------------------------------------------------------------ events --
    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event)

    def _handle_keydown(self, event: pygame.event.Event) -> None:
        if self.state == AppState.MAIN_MENU:
            self._handle_main_menu_keydown(event)
        elif self.state in (
            AppState.GARAGE,
            AppState.SHOP,
            AppState.SETTINGS,
            AppState.STATISTICS,
            AppState.CREDITS,
        ):
            if event.key == pygame.K_ESCAPE:
                self.state = AppState.MAIN_MENU
        elif self.state == AppState.DRIVING:
            if event.key == pygame.K_ESCAPE:
                self.state = AppState.MAIN_MENU

    def _handle_main_menu_keydown(self, event: pygame.event.Event) -> None:
        if event.key == pygame.K_UP:
            self._main_menu_index = (self._main_menu_index - 1) % len(self._main_menu_options)
        elif event.key == pygame.K_DOWN:
            self._main_menu_index = (self._main_menu_index + 1) % len(self._main_menu_options)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            _, target_state = self._main_menu_options[self._main_menu_index]
            self.state = target_state
        elif event.key == pygame.K_ESCAPE:
            self.running = False

    # ----------------------------------------------------------- update --
    def _update(self, dt: float) -> None:
        if self.state == AppState.DRIVING:
            self._update_driving(dt)
        # Other states are static placeholder screens for now; the
        # menu/garage/shop block will give them real update logic.

    def _update_driving(self, dt: float) -> None:
        # TEMPORARY: pans a free camera with WASD/arrows so the world
        # generated in block 2 can be inspected. Block 3 (vehicle
        # physics) removes this method's body entirely and drives
        # self._camera_x/_camera_y from the real player object instead.
        keys = pygame.key.get_pressed()
        dx = dy = 0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= 1.0
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += 1.0
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy -= 1.0
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += 1.0
        if dx or dy:
            length = math.hypot(dx, dy)
            dx, dy = dx / length, dy / length
        self._camera_x += dx * self._camera_speed * dt
        self._camera_y += dy * self._camera_speed * dt

    # ------------------------------------------------------------- draw --
    def _draw(self) -> None:
        self.screen.fill(COLOR_BG)

        if self.state == AppState.MAIN_MENU:
            self._draw_main_menu()
        elif self.state == AppState.DRIVING:
            self._draw_driving_placeholder()
        else:
            self._draw_generic_placeholder_screen()

        if self.settings.show_fps:
            self._draw_fps()

        pygame.display.flip()

    def _draw_main_menu(self) -> None:
        title_surf = self.fonts.huge.render(self.t("menu.title"), True, COLOR_ACCENT)
        title_rect = title_surf.get_rect(center=(self.screen.get_width() // 2, 140))
        self.screen.blit(title_surf, title_rect)

        start_y = 280
        gap = 48
        for i, (key, _state) in enumerate(self._main_menu_options):
            selected = i == self._main_menu_index
            color = COLOR_ACCENT if selected else COLOR_TEXT
            label = self.t(key)
            prefix = "> " if selected else "  "
            surf = self.fonts.medium.render(prefix + label, True, color)
            rect = surf.get_rect(center=(self.screen.get_width() // 2, start_y + i * gap))
            self.screen.blit(surf, rect)

        hint_surf = self.fonts.small.render(
            "Arrows to navigate, Enter to select, Esc to quit", True, COLOR_TEXT_DIM
        )
        hint_rect = hint_surf.get_rect(
            center=(self.screen.get_width() // 2, self.screen.get_height() - 40)
        )
        self.screen.blit(hint_surf, hint_rect)

        if self.assets.load_errors:
            self._draw_asset_warnings()

    def _draw_asset_warnings(self) -> None:
        y = 10
        for err in self.assets.load_errors[:6]:
            surf = self.fonts.small.render(err, True, COLOR_ERROR)
            self.screen.blit(surf, (10, y))
            y += 20

    def _draw_generic_placeholder_screen(self) -> None:
        # Every non-menu, non-driving state currently shares this
        # placeholder. Each will get its own real _draw_* method in the
        # menu/garage/shop block; this keeps block 1 runnable meanwhile.
        state_title_key = {
            AppState.GARAGE: "garage.title",
            AppState.SHOP: "shop.title",
            AppState.SETTINGS: "settings.title",
            AppState.STATISTICS: "stats.title",
            AppState.CREDITS: "credits.title",
        }.get(self.state, "menu.title")

        title_surf = self.fonts.large.render(self.t(state_title_key), True, COLOR_ACCENT)
        title_rect = title_surf.get_rect(center=(self.screen.get_width() // 2, 100))
        self.screen.blit(title_surf, title_rect)

        hint_surf = self.fonts.small.render("Esc: " + self.t("menu.back"), True, COLOR_TEXT_DIM)
        hint_rect = hint_surf.get_rect(
            center=(self.screen.get_width() // 2, self.screen.get_height() - 40)
        )
        self.screen.blit(hint_surf, hint_rect)

    def _draw_driving_placeholder(self) -> None:
        # Real worl
