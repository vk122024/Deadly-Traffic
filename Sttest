  "garage.upgrade_brakes": "Freins",
        "garage.upgrade_handling": "Maniabilité",
        "garage.upgrade_tires": "Pneus",
        "garage.upgrade_nitro": "Nitro",
        "garage.upgrade_paint": "Peinture",
        "shop.title": "Boutique",
        "shop.buy": "Acheter",
        "shop.owned": "Possédé",
        "shop.price": "Prix",
        "stats.title": "Statistiques",
        "stats.distance": "Distance",
        "stats.coins": "Pièces",
        "stats.top_speed": "Vitesse maximale",
        "stats.crashes": "Accidents",
        "stats.near_misses": "Quasi-accidents",
        "stats.cars_owned": "Voitures possédées",
        "stats.time_played": "Temps de jeu",
        "credits.title": "Crédits",
        "hud.coins": "Pièces",
        "hud.speed": "km/h",
        "hud.gear": "Vitesse",
        "hud.fps": "FPS",
        "weather.sunny": "Ensoleillé",
        "weather.cloudy": "Nuageux",
        "weather.rain": "Pluie",
        "weather.fog": "Brouillard",
        "weather.night": "Nuit",
        "weather.sunset": "Coucher de soleil",
    },
    "it": {
        "menu.title": "Prague Drive",
        "menu.play": "Gioca",
        "menu.garage": "Garage",
        "menu.shop": "Negozio",
        "menu.settings": "Impostazioni",
        "menu.statistics": "Statistiche",
        "menu.credits": "Crediti",
        "menu.exit": "Esci",
        "menu.back": "Indietro",
        "settings.title": "Impostazioni",
        "settings.fullscreen": "Schermo intero",
        "settings.resolution": "Risoluzione",
        "settings.music_volume": "Volume musica",
        "settings.effects_volume": "Volume effetti",
        "settings.language": "Lingua",
        "settings.fps": "Mostra FPS",
        "settings.controls": "Comandi",
        "garage.title": "Garage",
        "garage.select": "Seleziona",
        "garage.upgrade_engine": "Motore",
        "garage.upgrade_brakes": "Freni",
        "garage.upgrade_handling": "Maneggevolezza",
        "garage.upgrade_tires": "Pneumatici",
        "garage.upgrade_nitro": "Nitro",
        "garage.upgrade_paint": "Vernice",
        "shop.title": "Negozio",
        "shop.buy": "Compra",
        "shop.owned": "Posseduto",
        "shop.price": "Prezzo",
        "stats.title": "Statistiche",
        "stats.distance": "Distanza",
        "stats.coins": "Monete",
        "stats.top_speed": "Velocità massima",
        "stats.crashes": "Incidenti",
        "stats.near_misses": "Quasi incidenti",
        "stats.cars_owned": "Auto possedute",
        "stats.time_played": "Tempo di gioco",
        "credits.title": "Crediti",
        "hud.coins": "Monete",
        "hud.speed": "km/h",
        "hud.gear": "Marcia",
        "hud.fps": "FPS",
        "weather.sunny": "Soleggiato",
        "weather.cloudy": "Nuvoloso",
        "weather.rain": "Pioggia",
        "weather.fog": "Nebbia",
        "weather.night": "Notte",
        "weather.sunset": "Tramonto",
    },
    "uk": {
        "menu.title": "Prague Drive",
        "menu.play": "Грати",
        "menu.garage": "Гараж",
        "menu.shop": "Магазин",
        "menu.settings": "Налаштування",
        "menu.statistics": "Статистика",
        "menu.credits": "Автори",
        "menu.exit": "Вихід",
        "menu.back": "Назад",
        "settings.title": "Налаштування",
        "settings.fullscreen": "Повний екран",
        "settings.resolution": "Роздільна здатність",
        "settings.music_volume": "Гучність музики",
        "settings.effects_volume": "Гучність ефектів",
        "settings.language": "Мова",
        "settings.fps": "Показати FPS",
        "settings.controls": "Керування",
        "garage.title": "Гараж",
        "garage.select": "Вибрати",
        "garage.upgrade_engine": "Двигун",
        "garage.upgrade_brakes": "Гальма",
        "garage.upgrade_handling": "Керованість",
        "garage.upgrade_tires": "Шини",
        "garage.upgrade_nitro": "Нітро",
        "garage.upgrade_paint": "Фарба",
        "shop.title": "Магазин",
        "shop.buy": "Купити",
        "shop.owned": "У власності",
        "shop.price": "Ціна",
        "stats.title": "Статистика",
        "stats.distance": "Відстань",
        "stats.coins": "Монети",
        "stats.top_speed": "Максимальна швидкість",
        "stats.crashes": "Аварії",
        "stats.near_misses": "Ледь не аварії",
        "stats.cars_owned": "Кількість авто",
        "stats.time_played": "Час гри",
        "credits.title": "Автори",
        "hud.coins": "Монети",
        "hud.speed": "км/год",
        "hud.gear": "Передача",
        "hud.fps": "FPS",
        "weather.sunny": "Сонячно",
        "weather.cloudy": "Хмарно",
        "weather.rain": "Дощ",
        "weather.fog": "Туман",
        "weather.night": "Ніч",
        "weather.sunset": "Захід сонця",
    },
}


def tr(lang: str, key: str) -> str:
    """Translate a key into the given language, falling back to Czech
    (the authoritative default) and finally to the raw key if truly
    missing anywhere, so a missing string never crashes the game."""
    table = TRANSLATIONS.get(lang, TRANSLATIONS["cs"])
    if key in table:
        return table[key]
    return TRANSLATIONS["cs"].get(key, key)


# --------------------------------------------------------------------------
# SETTINGS
# --------------------------------------------------------------------------


@dataclass
class Settings:
    fullscreen: bool = False
    resolution: tuple[int, int] = DEFAULT_RESOLUTION
    music_volume: float = 0.6
    effects_volume: float = 0.8
    language: str = "cs"
    show_fps: bool = True

    def to_dict(self) -> dict:
        d = asdict(self)
        d["resolution"] = list(self.resolution)
        return d

    @staticmethod
    def from_dict(d: dict) -> "Settings":
        s = Settings()
        s.fullscreen = bool(d.get("fullscreen", s.fullscreen))
        res = d.get("resolution", list(s.resolution))
        s.resolution = (int(res[0]), int(res[1]))
        s.music_volume = float(d.get("music_volume", s.music_volume))
        s.effects_volume = float(d.get("effects_volume", s.effects_volume))
        s.language = d.get("language", s.language)
        if s.language not in SUPPORTED_LANGUAGES:
            s.language = "cs"
        s.show_fps = bool(d.get("show_fps", s.show_fps))
        return s


# --------------------------------------------------------------------------
# STATISTICS
# --------------------------------------------------------------------------


@dataclass
class Statistics:
    distance_meters: float = 0.0
    coins_earned_total: int = 0
    top_speed_kmh: float = 0.0
    crash_count: int = 0
    near_miss_count: int = 0
    cars_owned_count: int = 1
    time_played_seconds: float = 0.0

    # Adaptive-gameplay inputs (not machine learning: these are simple
    # running statistics that later blocks read to bias traffic AI).
    preferred_speed_kmh: float = 0.0
    preferred_lane_bias: float = 0.0  # -1 left .. +1 right, running average
    reaction_time_samples: list[float] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        return d

    @staticmethod
    def from_dict(d: dict) -> "Statistics":
        s = Statistics()
        for f in (
            "distance_meters",
            "coins_earned_total",
            "top_speed_kmh",
            "crash_count",
            "near_miss_count",
            "cars_owned_count",
            "time_played_seconds",
            "preferred_speed_kmh",
            "preferred_lane_bias",
        ):
            if f in d:
                setattr(s, f, d[f])
        s.reaction_time_samples = list(d.get("reaction_time_samples", []))
        return s


# --------------------------------------------------------------------------
# SAVE GAME (coins, owned cars, upgrades, settings, language, stats)
# --------------------------------------------------------------------------


class SaveGame:
    """Owns all persistent player state and knows how to serialize
    itself to/from SAVE_PATH as JSON. Later blocks (garage/shop) will
    read/write `owned_car_ids` and `car_upgrades` through this object;
    nothing here needs to change when they do."""

    def __init__(self) -> None:
        self.coins: int = 500
        self.owned_car_ids: list[int] = [0]
        self.selected_car_id: int = 0
        # car_upgrades[car_id] -> {"engine": int, "brakes": int, ...}
        self.car_upgrades: dict[str, dict[str, int]] = {}
        self.settings: Settings = Settings()
        self.statistics: Statistics = Statistics()

    def to_dict(self) -> dict:
        return {
            "coins": self.coins,
            "owned_car_ids": self.owned_car_ids,
            "selected_car_id": self.selected_car_id,
            "car_upgrades": self.car_upgrades,
            "settings": self.settings.to_dict(),
            "statistics": self.statistics.to_dict(),
        }

    def save(self) -> None:
        tmp_path = SAVE_PATH + ".tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, SAVE_PATH)
        except OSError as exc:
            print(f"[SaveGame] Failed to save: {exc}", file=sys.stderr)

    @staticmethod
    def load() -> "SaveGame":
        sg = SaveGame()
        if not os.path.exists(SAVE_PATH):
            return sg
        try:
            with open(SAVE_PATH, "r", encoding="utf-8") as f:
                d = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"[SaveGame] Failed to load, using defaults: {exc}", file=sys.stderr)
            return sg

        sg.coins = int(d.get("coins", sg.coins))
        sg.owned_car_ids = list(d.get("owned_car_ids", sg.owned_car_ids))
        sg.selected_car_id = int(d.get("selected_car_id", sg.selected_car_id))
        sg.car_upgrades = dict(d.get("car_upgrades", {}))
        if "settings" in d:
            sg.settings = Settings.from_dict(d["settings"])
        if "statistics" in d:
            sg.statistics = Statistics.from_dict(d["statistics"])
        return sg


# --------------------------------------------------------------------------
# ASSET LOADING
# --------------------------------------------------------------------------


class Assets:
    """Central registry for every loaded image. Loaded once at startup.
    Vehicle sprites are indexed by their tile number (0..32, skipping the
    known-blank slots) so later blocks can look them up by id without
    caring about file naming."""

    def __init__(self) -> None:
        self.vehicle_sprites: dict[int, pygame.Surface] = {}
        self.road_texture: Optional[pygame.Surface] = None
        self.road_tile_vertical: Optional[pygame.Surface] = None
        self.road_tile_horizontal: Optional[pygame.Surface] = None
        self.load_errors: list[str] = []

    def load(self) -> None:
        self._load_vehicle_sprites()
        self._load_road_texture()

    def _load_vehicle_sprites(self) -> None:
        for i in range(TOTAL_VEHICLE_TILE_SLOTS):
            if i in BLANK_VEHICLE_INDICES:
                continue
            filename = f"tile{i:03d}.png"
            path = os.path.join(ASSET_DIR, filename)
            if not os.path.exists(path):
                self.load_errors.append(f"Missing vehicle sprite: {filename}")
                continue
            try:
                surf = pygame.image.load(path).convert_alpha()
            except pygame.error as exc:
                self.load_errors.append(f"Failed to load {filename}: {exc}")
                continue
            self.vehicle_sprites[i] = surf

    def _load_road_texture(self) -> None:
        path = os.path.join(ASSET_DIR, ROAD_TEXTURE_FILENAME)
        if not os.path.exists(path):
            self.load_errors.append(f"Missing road texture: {ROAD_TEXTURE_FILENAME}")
            return
        try:
            self.road_texture = pygame.image.load(path).convert_alpha()
        except pygame.error as exc:
            self.load_errors.append(f"Failed to load {ROAD_TEXTURE_FILENAME}: {exc}")
            return

        # The source texture's lane markings run along its HEIGHT axis, so
        # it tiles cleanly for a road that travels top-to-bottom (a
        # "vertical" road on screen). Scale it down to ROAD_WIDTH across
        # and derive the matching repeat length along travel direction.
        self.road_tile_vertical = pygame.transform.smoothscale(
            self.road_texture, (ROAD_WIDTH, ROAD_TILE_REPEAT_LENGTH)
        )
        # A horizontal road is the same strip rotated 90 degrees.
        self.road_tile_horizontal = pygame.transform.rotate(self.road_tile_vertical, 90)

    def vehicle_ids_sorted(self) -> list[int]:
        return sorted(self.vehicle_sprites.keys())


# --------------------------------------------------------------------------
# WORLD MODEL: buildings, roads, chunks, city (BLOCK 2)
# --------------------------------------------------------------------------


def chunk_district(chunk_x: int, chunk_y: int) -> str:
    """Deterministic district lookup so the same chunk always maps to
    the same district without storing any explicit assignment."""
    idx = (chunk_x * 928371 + chunk_y * 517933) % len(DISTRICT_NAMES)
    return DISTRICT_NAMES[idx]


def weighted_choice(rng: random.Random, weights: dict[str, int]) -> str:
    total = sum(weights.values())
    r = rng.uniform(0, total)
    upto = 0.0
    for key, weight in weights.items():
        upto += weight
        if r <= upto:
            return key
    return next(iter(weights))


@dataclass
class Building:
    rect: pygame.Rect  # world-space collision rect
    kind: str
    district: str
    base_color: tuple[int, int, int]
    trim_color: tuple[int, int, int]
    has_tram_stop: bool = False


@dataclass
class RoadSegment:
    """A single straight road centerline within a chunk, in LOCAL chunk
    coordinates. orientation is 'v' (runs top-to-bottom) or 'h' (runs
    left-to-right). has_tram is True if tram tracks run along it."""
    orientation: str
    offset: float  # local x (if vertical) or local y (if horizontal)
    has_tram: bool


class Chunk:
    """One square cell of the infinite world grid. Generates its own
    roads, district buildings, parks, parking lots, river piece, and
    bridges deterministically from (chunk_x, chunk_y), then caches a
    pre-rendered Surface plus a list of world-space collision Rects."""

    def __init__(self, chunk_x: int, chunk_y: int, assets: Assets) -> None:
        self.chunk_x = chunk_x
        self.chunk_y = chunk_y
        self.assets = assets
        self.district = chunk_district(chunk_x, chunk_y)
        self.is_river = (chunk_x == RIVER_CHUNK_COLUMN)

        self.road_segments: list[RoadSegment] = [
            RoadSegment("v", CHUNK_ROAD_OFFSETS[0], self._column_has_tram()),
            RoadSegment("v", CHUNK_ROAD_OFFSETS[1], False),
            RoadSegment("h", CHUNK_ROAD_OFFSETS[0], False),
            RoadSegment("h", CHUNK_ROAD_OFFSETS[1], False),
        ]

        # Buildings, in WORLD space, so the city-wide collision query
        # never needs to know about chunk boundaries.
        self.buildings: list[Building] = []
        # Parking lot rects, world space, for the mission/parking system.
        self.parking_lots: list[pygame.Rect] = []
        # Park rects (open, walkable/drivable-shoulder, no collision).
        self.parks: list[pygame.Rect] = []

        self.surface = pygame.Surface((CHUNK_SIZE, CHUNK_SIZE)).convert()
        self._generate()

    def _column_has_tram(self) -> bool:
        return (self.chunk_x % TRAM_TRACK_COLUMN_MODULO) == 0

    def world_origin(self) -> tuple[float, float]:
        return (self.chunk_x * CHUNK_SIZE, self.chunk_y * CHUNK_SIZE)

    # -- generation ---------------------------------------------------

    def _generate(self) -> None:
        rng = random.Random(f"chunk:{self.chunk_x}:{self.chunk_y}")
        palette = DISTRICT_PALETTES[self.district]
        self.surface.fill((60, 130, 70) if False else (58, 58, 62))  # base ground

        if self.is_river:
            self._draw_river(rng)
        else:
            self._draw_roads_and_sidewalks(rng)
            self._generate_blocks(rng, palette)

        self._carve_easter_egg_clearing()

    def _draw_river(self, rng: random.Random) -> None:
        # Sine-wave river running the length of the chunk, same technique
        # as the original prototype's river chunk, adapted to world Y.
        points_left = []
        points_right = []
        world_x0, world_y0 = self.world_origin()
        for local_y in range(-20, CHUNK_SIZE + 40, 20):
            world_y = world_y0 + local_y
            center_x = (CHUNK_SIZE / 2) + math.sin(world_y * 0.0025) * 140
            points_left.append((center_x - RIVER_WIDTH / 2, local_y))
            points_right.append((center_x + RIVER_WIDTH / 2, local_y))
        polygon = points_left + list(reversed(points_right))
        pygame.draw.polygon(self.surface, (94, 138, 176), polygon)
        # Bridges: wherever a road from the neighboring land chunks would
        # cross this column, draw a bridge deck across the river so the
        # road network connects naturally instead of dead-ending at water.
        for offset in CHUNK_ROAD_OFFSETS:
            deck_rect = pygame.Rect(0, int(offset - ROAD_WIDTH / 2), CHUNK_SIZE, ROAD_WIDTH)
            pygame.draw.rect(self.surface, (120, 118, 112), deck_rect)
            pygame.draw.rect(self.surface, (80, 78, 74), deck_rect, width=4)

    def _draw_roads_and_sidewalks(self, rng: random.Random) -> None:
        tile_v = self.assets.road_tile_vertical
        tile_h = self.assets.road_tile_horizontal

        for seg in self.road_segments:
            if seg.orientation == "v":
                x = int(seg.offset - ROAD_WIDTH / 2)
                sidewalk_rect_l = pygame.Rect(x - SIDEWALK_WIDTH, 0, SIDEWALK_WIDTH, CHUNK_SIZE)
                sidewalk_rect_r = pygame.Rect(x + ROAD_WIDTH, 0, SIDEWALK_WIDTH, CHUNK_SIZE)
                pygame.draw.rect(self.surface, (150, 148, 145), sidewalk_rect_l)
                pygame.draw.rect(self.surface, (150, 148, 145), sidewalk_rect_r)
                if tile_v is not None:
                    for ty in range(0, CHUNK_SIZE, tile_v.get_height()):
                        self.surface.blit(tile_v, (x, ty))
                else:
                    pygame.draw.rect(self.surface, (48, 48, 52), (x, 0, ROAD_WIDTH, CHUNK_SIZE))
                if seg.has_tram:
                    self._draw_tram_rails_vertical(seg.offset)
            else:
                y = int(seg.offset - ROAD_WIDTH / 2)
                sidewalk_rect_t = pygame.Rect(0, y - SIDEWALK_WIDTH, CHUNK_SIZE, SIDEWALK_WIDTH)
                sidewalk_rect_b = pygame.Rect(0, y + ROAD_WIDTH, CHUNK_SIZE, SIDEWALK_WIDTH)
                pygame.draw.rect(self.surface, (150, 148, 145), sidewalk_rect_t)
                pygame.draw.rect(self.surface, (150, 148, 145), sidewalk_rect_b)
                if tile_h is not None:
                    for tx in range(0, CHUNK_SIZE, tile_h.get_width()):
                        self.surface.blit(tile_h, (tx, y))
                else:
                    pygame.draw.rect(self.surface, (48, 48, 52), (0, y, CHUNK_SIZE, ROAD_WIDTH))

        self._draw_intersections_and_crosswalks()
        self._draw_traffic_lights()
        self._maybe_draw_roundabout(rng)

    def _draw_tram_rails_vertical(self, offset: float) -> None:
        for rail_x in (offset - TRAM_TRACK_OFFSET, offset + TRAM_TRACK_OFFSET):
            for y in range(0, CHUNK_SIZE, 24):
                pygame.draw.line(self.surface, (60, 60, 60), (rail_x, y), (rail_x, y + 14), 4)

    def _draw_intersections_and_crosswalks(self) -> None:
        for v_seg in (s for s in self.road_segments if s.orientation == "v"):
            for h_seg in (s for s in self.road_segments if s.orientation == "h"):
                cx, cy = v_seg.offset, h_seg.offset
     
