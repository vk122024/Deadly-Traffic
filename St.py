
"""
Prague Drive - a top-down open-world driving simulator.

Single-file architecture as requested. This file is being built in
ordered blocks (skeleton -> world -> physics -> rendering -> AI ->
economy -> menus/HUD -> wiring). This is BLOCK 1 of that sequence.

BLOCK 1 CONTAINS:
    - Imports
    - Global constants
    - Enums or the app state machine
    - Save/Settings system (JSON-backed, auto-saving)
    - Full translation dictionary (8 languages, Czech default)
    - Asset path constants + sprite loader helpers
    - The Game class shell: window creation, main loop skeleton,
      state dispatch (currently routes to placeholder states so the
      file is runnable end-to-end right now; later blocks replace
      the placeholder state handlers with the real menu / garage /
      driving screens without touching anything above them).

Nothing in this block will need to be rewritten by later blocks;
later blocks only ADD new classes/methods and swap placeholder
method bodies inside Game for calls into the new systems.
"""

from __future__ import annotations

import json
import math
import os
import random
import sys
import time
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from typing import Optional

import pygame

# --------------------------------------------------------------------------
# PATHS
# --------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR = os.path.join(BASE_DIR, "assets")
SAVE_PATH = os.path.join(BASE_DIR, "savegame.json")

# Tiles that are intentionally blank placeholders in the source sprite
# sheet export and must never be loaded as real vehicles.
BLANK_VEHICLE_INDICES = frozenset({10, 21, 32})
TOTAL_VEHICLE_TILE_SLOTS = 33  # tile000.png .. tile032.png

VEHICLE_TILE_WIDTH = 34
VEHICLE_TILE_HEIGHT = 64

ROAD_TEXTURE_FILENAME = "background-1.png"

# --------------------------------------------------------------------------
# WINDOW / DISPLAY CONSTANTS
# --------------------------------------------------------------------------

DEFAULT_RESOLUTION = (1280, 720)
AVAILABLE_RESOLUTIONS = [
    (1024, 576),
    (1280, 720),
    (1366, 768),
    (1600, 900),
    (1920, 1080),
]
TARGET_FPS = 60
WINDOW_TITLE = "Prague Drive"

# --------------------------------------------------------------------------
# GAMEPLAY / WORLD CONSTANTS
# --------------------------------------------------------------------------

# The road texture tiles at this size in world space (pixels at zoom=1).
# background-1.png is a 4-lane two-way road segment; we treat its native
# pixel size as the authoritative tile footprint and derive lane geometry
# from it in the world-building block rather than guessing new numbers.
ROAD_TILE_NATIVE_SIZE = (840, 650)

# Physics constants shared by all vehicles (tunable per-vehicle multipliers
# are applied on top of these in the physics block).
GRAVITY_UNUSED = 9.81  # kept for future 3D-ish effects (e.g. jumps); unused now
METERS_TO_PIXELS = 12.0  # world scale factor used by the physics block

WEATHER_TYPES = (
    "sunny",
    "cloudy",
    "rain",
    "fog",
    "night",
    "sunset",
)

DRIVER_PERSONALITIES = (
    "careful",
    "normal",
    "aggressive",
    "police",
    "taxi",
    "truck",
    "motorcycle",
)

# --------------------------------------------------------------------------
# CITY / WORLD LAYOUT CONSTANTS
# --------------------------------------------------------------------------
#
# The world is an infinite grid of square CHUNKS, each subdivided by a
# small internal road grid (offsets within a chunk), mirroring the
# proven chunk-streaming approach from the original prototype but
# rebuilt around the real road texture and real districts.

CHUNK_SIZE = 1400  # world units (pixels at zoom=1) per chunk, both axes

# Road texture is scaled down from its native multi-lane-crossing size
# into a tileable strip: width = across the road, height = one repeat
# unit along the direction of travel.
ROAD_WIDTH = 240
_road_scale = ROAD_WIDTH / ROAD_TILE_NATIVE_SIZE[0]
ROAD_TILE_REPEAT_LENGTH = round(ROAD_TILE_NATIVE_SIZE[1] * _road_scale)

SIDEWALK_WIDTH = 26
TRAM_TRACK_OFFSET = 46  # distance from road centerline to each tram rail

# Internal road offsets within a chunk (two roads per axis -> a 2x2
# grid of city blocks per chunk between them).
CHUNK_ROAD_OFFSETS = (CHUNK_SIZE * 0.28, CHUNK_SIZE * 0.72)

# Every Nth chunk column carries tram tracks on its "primary" road,
# giving the map a readable transit spine without covering every street.
TRAM_TRACK_COLUMN_MODULO = 3

# The river runs down chunk column -1 (immediately west of the origin
# chunk), exactly like the original prototype's dedicated river chunk.
RIVER_CHUNK_COLUMN = -1
RIVER_WIDTH = 260

# Districts are assigned to chunks by a deterministic hash of chunk
# coordinates, so the same chunk always renders the same district
# without having to store district assignments explicitly.
DISTRICT_NAMES = (
    "Staré Město",   # Old Town
    "Nové Město",    # New Town
    "Karlín",
    "Vinohrady",
    "Smíchov",
    "Holešovice",
)

# Each district gets a building color palette (base, trim) so districts
# feel visually distinct.
DISTRICT_PALETTES = {
    "Staré Město": {"base": (214, 196, 160), "trim": (168, 140, 96)},
    "Nové Město": {"base": (200, 200, 205), "trim": (150, 150, 158)},
    "Karlín": {"base": (188, 176, 190), "trim": (140, 128, 150)},
    "Vinohrady": {"base": (212, 178, 150), "trim": (160, 120, 90)},
    "Smíchov": {"base": (170, 182, 190), "trim": (120, 135, 145)},
    "Holešovice": {"base": (190, 190, 170), "trim": (140, 140, 118)},
}

# Weighted list of building "kinds" each district favors, used when
# picking a building kind for a generated lot.
DISTRICT_BUILDING_WEIGHTS = {
    "Staré Město": {"cafe": 4, "hotel": 3, "shop": 3, "apartment": 2},
    "Nové Město": {"office": 4, "apartment": 3, "shop": 2, "hotel": 1},
    "Karlín": {"office": 3, "apartment": 4, "cafe": 2},
    "Vinohrady": {"apartment": 5, "cafe": 2, "school": 1},
    "Smíchov": {"office": 3, "apartment": 3, "hospital": 1, "shop": 2},
    "Holešovice": {"apartment": 3, "office": 2, "school": 1, "shop": 2},
}
ALL_BUILDING_KINDS = ("apartment", "office", "cafe", "shop", "hotel", "school", "hospital")

BUILDING_KIND_COLORS = {
    "apartment": (30, 30, 35),
    "office": (40, 70, 110),
    "cafe": (150, 90, 40),
    "shop": (150, 40, 60),
    "hotel": (150, 120, 40),
    "school": (60, 120, 60),
    "hospital": (200, 60, 60),
}

# Fixed world-space anchor reserved for the ported easter egg scene
# (the "Pan Kaficko" scripted Mercedes/ambulance crash from the
# original prototype). The world generator below must never place a
# building or road inside EASTER_EGG_CLEAR_RADIUS of this point; a
# later AI/events block renders and triggers the actual scripted scene.
EASTER_EGG_WORLD_POS = (CHUNK_SIZE * 0.5, -CHUNK_SIZE * 1.5)
EASTER_EGG_CLEAR_RADIUS = 220

# --------------------------------------------------------------------------
# APP STATE MACHINE
# --------------------------------------------------------------------------


class AppState(Enum):
    MAIN_MENU = auto()
    GARAGE = auto()
    SHOP = auto()
    SETTINGS = auto()
    STATISTICS = auto()
    CREDITS = auto()
    DRIVING = auto()
    QUIT = auto()


# --------------------------------------------------------------------------
# TRANSLATIONS
# --------------------------------------------------------------------------
#
# All on-screen text must be pulled from here. Every language has the
# same key set; Czech ("cs") is authoritative/default. If a later block
# needs a new string, add the key to ALL language blocks at once so no
# language silently falls back.

SUPPORTED_LANGUAGES = (
    "cs",  # Čeština (default)
    "en",  # English
    "de",  # Deutsch
    "pl",  # Polski
    "sk",  # Slovenčina
    "es",  # Español
    "fr",  # Français
    "it",  # Italiano
    "uk",  # Українська
)

LANGUAGE_DISPLAY_NAMES = {
    "cs": "Čeština",
    "en": "English",
    "de": "Deutsch",
    "pl": "Polski",
    "sk": "Slovenčina",
    "es": "Español",
    "fr": "Français",
    "it": "Italiano",
    "uk": "Українська",
}

TRANSLATIONS: dict[str, dict[str, str]] = {
    "cs": {
        "menu.title": "Prague Drive",
        "menu.play": "Hrát",
        "menu.garage": "Garáž",
        "menu.shop": "Obchod",
        "menu.settings": "Nastavení",
        "menu.statistics": "Statistiky",
        "menu.credits": "Autoři",
        "menu.exit": "Konec",
        "menu.back": "Zpět",
        "settings.title": "Nastavení",
        "settings.fullscreen": "Celá obrazovka",
        "settings.resolution": "Rozlišení",
        "settings.music_volume": "Hlasitost hudby",
        "settings.effects_volume": "Hlasitost efektů",
        "settings.language": "Jazyk",
        "settings.fps": "Zobrazit FPS",
        "settings.controls": "Ovládání",
        "garage.title": "Garáž",
        "garage.select": "Vybrat",
        "garage.upgrade_engine": "Motor",
        "garage.upgrade_brakes": "Brzdy",
        "garage.upgrade_handling": "Řízení",
        "garage.upgrade_tires": "Pneumatiky",
        "garage.upgrade_nitro": "Nitro",
        "garage.upgrade_paint": "Lak",
        "shop.title": "Obchod",
        "shop.buy": "Koupit",
        "shop.owned": "Vlastníte",
        "shop.price": "Cena",
        "stats.title": "Statistiky",
        "stats.distance": "Vzdálenost",
        "stats.coins": "Mince",
        "stats.top_speed": "Nejvyšší rychlost",
        "stats.crashes": "Nehody",
        "stats.near_misses": "Málem nehoda",
        "stats.cars_owned": "Počet vozů",
        "stats.time_played": "Odehraný čas",
        "credits.title": "Autoři",
        "hud.coins": "Mince",
        "hud.speed": "km/h",
        "hud.gear": "Rychlost",
        "hud.fps": "FPS",
        "weather.sunny": "Slunečno",
        "weather.cloudy": "Zataženo",
        "weather.rain": "Déšť",
        "weather.fog": "Mlha",
        "weather.night": "Noc",
        "weather.sunset": "Soumrak",
    },
    "en": {
        "menu.title": "Prague Drive",
        "menu.play": "Play",
        "menu.garage": "Garage",
        "menu.shop": "Shop",
        "menu.settings": "Settings",
        "menu.statistics": "Statistics",
        "menu.credits": "Credits",
        "menu.exit": "Exit",
        "menu.back": "Back",
        "settings.title": "Settings",
        "settings.fullscreen": "Fullscreen",
        "settings.resolution": "Resolution",
        "settings.music_volume": "Music Volume",
        "settings.effects_volume": "Effects Volume",
        "settings.language": "Language",
        "settings.fps": "Show FPS",
        "settings.controls": "Controls",
        "garage.title": "Garage",
        "garage.select": "Select",
        "garage.upgrade_engine": "Engine",
        "garage.upgrade_brakes": "Brakes",
        "garage.upgrade_handling": "Handling",
        "garage.upgrade_tires": "Tires",
        "garage.upgrade_nitro": "Nitro",
        "garage.upgrade_paint": "Paint",
        "shop.title": "Shop",
        "shop.buy": "Buy",
        "shop.owned": "Owned",
        "shop.price": "Price",
        "stats.title": "Statistics",
        "stats.distance": "Distance",
        "stats.coins": "Coins",
        "stats.top_speed": "Top Speed",
        "stats.crashes": "Crashes",
        "stats.near_misses": "Near Misses",
        "stats.cars_owned": "Cars Owned",
        "stats.time_played": "Time Played",
        "credits.title": "Credits",
        "hud.coins": "Coins",
        "hud.speed": "km/h",
        "hud.gear": "Gear",
        "hud.fps": "FPS",
        "weather.sunny": "Sunny",
        "weather.cloudy": "Cloudy",
        "weather.rain": "Rain",
        "weather.fog": "Fog",
        "weather.night": "Night",
        "weather.sunset": "Sunset",
    },
    "de": {
        "menu.title": "Prague Drive",
        "menu.play": "Spielen",
        "menu.garage": "Garage",
        "menu.shop": "Geschäft",
        "menu.settings": "Einstellungen",
        "menu.statistics": "Statistik",
        "menu.credits": "Credits",
        "menu.exit": "Beenden",
        "menu.back": "Zurück",
        "settings.title": "Einstellungen",
        "settings.fullscreen": "Vollbild",
        "settings.resolution": "Auflösung",
        "settings.music_volume": "Musiklautstärke",
        "settings.effects_volume": "Effektlautstärke",
        "settings.language": "Sprache",
        "settings.fps": "FPS anzeigen",
        "settings.controls": "Steuerung",
        "garage.title": "Garage",
        "garage.select": "Auswählen",
        "garage.upgrade_engine": "Motor",
        "garage.upgrade_brakes": "Bremsen",
        "garage.upgrade_handling": "Handling",
        "garage.upgrade_tires": "Reifen",
        "garage.upgrade_nitro": "Nitro",
        "garage.upgrade_paint": "Lackierung",
        "shop.title": "Geschäft",
        "shop.buy": "Kaufen",
        "shop.owned": "Im Besitz",
        "shop.price": "Preis",
        "stats.title": "Statistik",
        "stats.distance": "Distanz",
        "stats.coins": "Münzen",
        "stats.top_speed": "Höchstgeschwindigkeit",
        "stats.crashes": "Unfälle",
        "stats.near_misses": "Beinahe-Unfälle",
        "stats.cars_owned": "Fahrzeuge",
        "stats.time_played": "Spielzeit",
        "credits.title": "Credits",
        "hud.coins": "Münzen",
        "hud.speed": "km/h",
        "hud.gear": "Gang",
        "hud.fps": "FPS",
        "weather.sunny": "Sonnig",
        "weather.cloudy": "Bewölkt",
        "weather.rain": "Regen",
        "weather.fog": "Nebel",
        "weather.night": "Nacht",
        "weather.sunset": "Sonnenuntergang",
    },
    "pl": {
        "menu.title": "Prague Drive",
        "menu.play": "Graj",
        "menu.garage": "Garaż",
        "menu.shop": "Sklep",
        "menu.settings": "Ustawienia",
        "menu.statistics": "Statystyki",
        "menu.credits": "Twórcy",
        "menu.exit": "Wyjście",
        "menu.back": "Wstecz",
        "settings.title": "Ustawienia",
        "settings.fullscreen": "Pełny ekran",
        "settings.resolution": "Rozdzielczość",
        "settings.music_volume": "Głośność muzyki",
        "settings.effects_volume": "Głośność efektów",
        "settings.language": "Język",
        "settings.fps": "Pokaż FPS",
        "settings.controls": "Sterowanie",
        "garage.title": "Garaż",
        "garage.select": "Wybierz",
        "garage.upgrade_engine": "Silnik",
        "garage.upgrade_brakes": "Hamulce",
        "garage.upgrade_handling": "Zwrotność",
        "garage.upgrade_tires": "Opony",
        "garage.upgrade_nitro": "Nitro",
        "garage.upgrade_paint": "Lakier",
        "shop.title": "Sklep",
        "shop.buy": "Kup",
        "shop.owned": "Posiadane",
        "shop.price": "Cena",
        "stats.title": "Statystyki",
        "stats.distance": "Dystans",
        "stats.coins": "Monety",
        "stats.top_speed": "Najwyższa prędkość",
        "stats.crashes": "Wypadki",
        "stats.near_misses": "Prawie wypadki",
        "stats.cars_owned": "Liczba pojazdów",
        "stats.time_played": "Czas gry",
        "credits.title": "Twórcy",
        "hud.coins": "Monety",
        "hud.speed": "km/h",
        "hud.gear": "Bieg",
        "hud.fps": "FPS",
        "weather.sunny": "Słonecznie",
        "weather.cloudy": "Pochmurno",
        "weather.rain": "Deszcz",
        "weather.fog": "Mgła",
        "weather.night": "Noc",
        "weather.sunset": "Zachód słońca",
    },
    "sk": {
        "menu.title": "Prague Drive",
        "menu.play": "Hrať",
        "menu.garage": "Garáž",
        "menu.shop": "Obchod",
        "menu.settings": "Nastavenia",
        "menu.statistics": "Štatistiky",
        "menu.credits": "Autori",
        "menu.exit": "Koniec",
        "menu.back": "Späť",
        "settings.title": "Nastavenia",
        "settings.fullscreen": "Celá obrazovka",
        "settings.resolution": "Rozlíšenie",
        "settings.music_volume": "Hlasitosť hudby",
        "settings.effects_volume": "Hlasitosť efektov",
        "settings.language": "Jazyk",
        "settings.fps": "Zobraziť FPS",
        "settings.controls": "Ovládanie",
        "garage.title": "Garáž",
        "garage.select": "Vybrať",
        "garage.upgrade_engine": "Motor",
        "garage.upgrade_brakes": "Brzdy",
        "garage.upgrade_handling": "Riadenie",
        "garage.upgrade_tires": "Pneumatiky",
        "garage.upgrade_nitro": "Nitro",
        "garage.upgrade_paint": "Lak",
        "shop.title": "Obchod",
        "shop.buy": "Kúpiť",
        "shop.owned": "Vlastníte",
        "shop.price": "Cena",
        "stats.title": "Štatistiky",
        "stats.distance": "Vzdialenosť",
        "stats.coins": "Mince",
        "stats.top_speed": "Najvyššia rýchlosť",
        "stats.crashes": "Nehody",
        "stats.near_misses": "Takmer nehody",
        "stats.cars_owned": "Počet vozidiel",
        "stats.time_played": "Odohraný čas",
        "credits.title": "Autori",
        "hud.coins": "Mince",
        "hud.speed": "km/h",
        "hud.gear": "Rýchlosť",
        "hud.fps": "FPS",
        "weather.sunny": "Slnečno",
        "weather.cloudy": "Zamračené",
        "weather.rain": "Dážď",
        "weather.fog": "Hmla",
        "weather.night": "Noc",
        "weather.sunset": "Súmrak",
    },
    "es": {
        "menu.title": "Prague Drive",
        "menu.play": "Jugar",
        "menu.garage": "Garaje",
        "menu.shop": "Tienda",
        "menu.settings": "Ajustes",
        "menu.statistics": "Estadísticas",
        "menu.credits": "Créditos",
        "menu.exit": "Salir",
        "menu.back": "Volver",
        "settings.title": "Ajustes",
        "settings.fullscreen": "Pantalla completa",
        "settings.resolution": "Resolución",
        "settings.music_volume": "Volumen de música",
        "settings.effects_volume": "Volumen de efectos",
        "settings.language": "Idioma",
        "settings.fps": "Mostrar FPS",
        "settings.controls": "Controles",
        "garage.title": "Garaje",
        "garage.select": "Seleccionar",
        "garage.upgrade_engine": "Motor",
        "garage.upgrade_brakes": "Frenos",
        "garage.upgrade_handling": "Manejo",
        "garage.upgrade_tires": "Neumáticos",
        "garage.upgrade_nitro": "Nitro",
        "garage.upgrade_paint": "Pintura",
        "shop.title": "Tienda",
        "shop.buy": "Comprar",
        "shop.owned": "En propiedad",
        "shop.price": "Precio",
        "stats.title": "Estadísticas",
        "stats.distance": "Distancia",
        "stats.coins": "Monedas",
        "stats.top_speed": "Velocidad máxima",
        "stats.crashes": "Choques",
        "stats.near_misses": "Casi choques",
        "stats.cars_owned": "Coches poseídos",
        "stats.time_played": "Tiempo jugado",
        "credits.title": "Créditos",
        "hud.coins": "Monedas",
        "hud.speed": "km/h",
        "hud.gear": "Marcha",
        "hud.fps": "FPS",
        "weather.sunny": "Soleado",
        "weather.cloudy": "Nublado",
        "weather.rain": "Lluvia",
        "weather.fog": "Niebla",
        "weather.night": "Noche",
        "weather.sunset": "Atardecer",
    },
    "fr": {
        "menu.title": "Prague Drive",
        "menu.play": "Jouer",
        "menu.garage": "Garage",
        "menu.shop": "Boutique",
        "menu.settings": "Paramètres",
        "menu.statistics": "Statistiques",
        "menu.credits": "Crédits",
        "menu.exit": "Quitter",
        "menu.back": "Retour",
        "settings.title": "Paramètres",
        "settings.fullscreen": "Plein écran",
        "settings.resolution": "Résolution",
        "settings.music_volume": "Volume musique",
        "settings.effects_volume": "Volume effets",
        "settings.language": "Langue",
        "settings.fps": "Afficher FPS",
        "settings.controls": "Contrôles",
        "garage.title": "Garage",
        "garage.select": "Sélectionner",
        "garage.upgrade_engine":
