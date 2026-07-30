
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
        "garage.upgrade_engine": "Moteur",
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
        # Real world rendering as of block 2, via the free test camera.
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
  
