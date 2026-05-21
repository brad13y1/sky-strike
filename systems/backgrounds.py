"""
systems/backgrounds.py
=======================
Sky backgrounds and scrolling scenery (clouds, stars).

This module fully owns the cloud and star data — it sets them up
when the module loads, draws them when asked, and updates their
positions when asked. The gameplay scene just calls into it.

WHAT'S HERE:
  - Cloud and star data (module-level lists, set up on import)
  - Three sky fills (function-as-data, like movement patterns):
        fill_solid_sky       — plain blue, Level 1
        fill_sunset          — purple-to-orange gradient, Level 2
        fill_night_sky       — dark gradient with stars, Level 3
  - draw_clouds / draw_stars (rendering)
  - update_clouds / update_stars (drift left, recycle off-screen)

NOTE: fill_night_sky draws the stars internally because they're
part of the night sky's look. Clouds, however, are drawn by the
gameplay scene AFTER the background fill — so all three sky types
can have clouds if we want.
"""

import random
import pygame

from core.constants import WIDTH, HEIGHT, SKY, WHITE


# ============================================================
# CLOUD AND STAR DATA
# ============================================================
# These lists are created once when this module is first imported.
# Each cloud / star is a dict — update functions mutate the dicts
# in place; draw functions read them.

# Scrolling cloud background — used by every level.
clouds = [
    {"x": random.randint(0, WIDTH),
     "y": random.randint(40, HEIGHT - 80),
     "size": random.randint(25, 55),
     "speed": random.uniform(0.5, 1.5)}
    for _ in range(10)
]

# Starfield — only drawn by fill_night_sky (Level 3 and any future
# night-themed levels).
stars = [
    {"x": random.randint(0, WIDTH),
     "y": random.randint(20, HEIGHT - 40),
     "size": random.randint(1, 3),
     "speed": random.uniform(0.2, 0.6),
     "brightness": random.randint(160, 255)}
    for _ in range(80)
]


# ============================================================
# GRADIENT CACHES
# ============================================================
# fill_sunset and fill_night_sky used to redraw 600 horizontal
# lines every frame — expensive on slow hardware (Android tablets).
# Instead we render each gradient once into a Surface and cache it.
# Every frame is then a single blit instead of 600 draw calls.

_sunset_cache    = None   # built on first call to fill_sunset
_night_sky_cache = None   # built on first call to fill_night_sky


# ============================================================
# SKY FILLS  (function-as-data — each level picks one)
# ============================================================

def fill_solid_sky(surf):
    """Plain blue sky. Level 1."""
    surf.fill(SKY)


def fill_sunset(surf):
    """Vertical gradient: purple at the top, orange near the horizon.
    Level 2.

    The gradient is pre-rendered into _sunset_cache on the first call.
    Every subsequent call is a single blit — no per-frame line drawing.
    """
    global _sunset_cache
    if _sunset_cache is None:
        _sunset_cache = pygame.Surface((WIDTH, HEIGHT))
        top_color    = (90,  50, 130)
        bottom_color = (250, 130, 60)
        for y in range(HEIGHT):
            t = y / HEIGHT
            r = int(top_color[0] * (1 - t) + bottom_color[0] * t)
            g = int(top_color[1] * (1 - t) + bottom_color[1] * t)
            b = int(top_color[2] * (1 - t) + bottom_color[2] * t)
            pygame.draw.line(_sunset_cache, (r, g, b), (0, y), (WIDTH, y))
    surf.blit(_sunset_cache, (0, 0))


def fill_night_sky(surf):
    """Dark vertical gradient with stars overlaid. Level 3.

    The gradient is pre-rendered into _night_sky_cache on the first call.
    Stars are drawn on top each frame because they move — only the static
    gradient part is cached.
    """
    global _night_sky_cache
    if _night_sky_cache is None:
        _night_sky_cache = pygame.Surface((WIDTH, HEIGHT))
        top_color    = (5,  5,  20)   # near-black at the top
        bottom_color = (25, 35, 70)   # deep blue near the horizon
        for y in range(HEIGHT):
            t = y / HEIGHT
            r = int(top_color[0] * (1 - t) + bottom_color[0] * t)
            g = int(top_color[1] * (1 - t) + bottom_color[1] * t)
            b = int(top_color[2] * (1 - t) + bottom_color[2] * t)
            pygame.draw.line(_night_sky_cache, (r, g, b), (0, y), (WIDTH, y))
    surf.blit(_night_sky_cache, (0, 0))
    # Stars go ON TOP of the cached gradient — they move each frame
    # so they can't be baked into the cache.
    draw_stars(surf)


# ============================================================
# IMAGE BACKGROUNDS  (kid's PNG art as level backdrops)
# ============================================================

# Cache so we only load each background PNG once, no matter how
# many times the player replays the level.
_image_bg_cache = {}


def image_bg(relative_path):
    """Build a level-compatible background function from a PNG file.

    Used in a level dict the same way as fill_solid_sky / fill_sunset:

        from systems.backgrounds import image_bg

        LEVEL = {
            ...
            "background": image_bg("backgrounds/jungle.png"),
            ...
        }

    The PNG is loaded and scaled to fit (WIDTH x HEIGHT) the first
    time it's needed, then cached. Subsequent levels using the same
    image reuse the cached surface.

    The returned function has the same signature as the procedural
    fills above — takes a surface, blits the background onto it.
    """
    def _fill(surf):
        if relative_path not in _image_bg_cache:
            from core.paths import asset_path
            img = pygame.image.load(asset_path(relative_path)).convert()
            img = pygame.transform.scale(img, (WIDTH, HEIGHT))
            _image_bg_cache[relative_path] = img
        surf.blit(_image_bg_cache[relative_path], (0, 0))
    return _fill


# ============================================================
# DRAW
# ============================================================

def draw_clouds(surf):
    """Draw all clouds. Each cloud is 4 overlapping white circles."""
    for c in clouds:
        cx, cy, s = int(c["x"]), int(c["y"]), c["size"]
        pygame.draw.circle(surf, WHITE, (cx, cy), s)
        pygame.draw.circle(surf, WHITE, (cx + s // 2, cy - 8), int(s * 0.85))
        pygame.draw.circle(surf, WHITE, (cx - s // 2, cy - 4), int(s * 0.75))
        pygame.draw.circle(surf, WHITE, (cx + s,     cy + 4), int(s * 0.70))


def draw_stars(surf):
    """Draw all stars. Each is a small gray-scale circle whose
    brightness is stored in the star dict."""
    for s in stars:
        b = s["brightness"]
        pygame.draw.circle(
            surf, (b, b, b),
            (int(s["x"]), int(s["y"])), s["size"])


# ============================================================
# UPDATE  (call once per frame)
# ============================================================

def update_clouds():
    """Drift every cloud left. Once a cloud passes the left edge,
    wrap it back to the right with fresh random Y / size / speed."""
    for c in clouds:
        c["x"] -= c["speed"]
        if c["x"] < -100:
            c["x"]     = WIDTH + 50
            c["y"]     = random.randint(40, HEIGHT - 80)
            c["size"]  = random.randint(25, 55)
            c["speed"] = random.uniform(0.5, 1.5)


def update_stars():
    """Same idea as update_clouds but slower (deeper-feeling parallax)."""
    for s in stars:
        s["x"] -= s["speed"]
        if s["x"] < -10:
            s["x"]          = WIDTH + 10
            s["y"]          = random.randint(20, HEIGHT - 40)
            s["size"]       = random.randint(1, 3)
            s["brightness"] = random.randint(160, 255)