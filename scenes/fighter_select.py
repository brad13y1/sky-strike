"""
scenes/fighter_select.py
=========================
Fighter selection screen. Sits between the title screen and gameplay.
The player cycles through available fighters, reads their stats, then
confirms to fly.

LAYOUT (1024x600):
  "SELECT YOUR FIGHTER"  -- big title, top center
  [ < BACK ]             -- tap zone, top left (mobile back button)
  <   JET SPRITE   >     -- large preview, center screen
  FIGHTER NAME           -- big text below jet
  tagline                -- small gray text
  5 stat bars            -- ARMOR / SPEED / DAMAGE / FIRE RATE / BULLET SPD
  dot indicators         -- one dot per fighter, filled = selected
  swipe hint             -- small gray text at very bottom

CONTROLS:
  left / right           cycle fighters (keyboard/gamepad)
  swipe right / left     cycle fighters (touch — swipe direction = card direction)
  confirm / fire         select fighter, go to gameplay
  tap jet sprite area    select fighter, go to gameplay
  tap [ < BACK ]         return to title (mobile-friendly back button)
  pause (ESC / START)    return to title

Adding fighters: only change levels/fighters.py. This screen
scales to any number of entries in FIGHTERS automatically.
"""

import pygame

from core.constants import (
    WIDTH, HEIGHT,
    BLACK, WHITE, GRAY, DARK_GRAY, YELLOW,
)
from core.paths import asset_path
from core import input as input_mod
from core import fonts
from levels import fighters as fighters_mod


# ---- Module state ----
_fighter_imgs = []   # display-size sprites, one per fighter; loaded by init()


# ---- Layout constants ----
_PREVIEW_W    = 260    # jet preview width  (2x gameplay size)
_PREVIEW_H    = 120    # jet preview height
_PREVIEW_CY   = 215    # vertical center of the jet preview

_NAME_CY      = 320    # vertical center of the fighter name text
_TAG_CY       = 365    # vertical center of the tagline text

_BAR_LABEL_X  = 415    # right edge of stat bar labels
_BAR_X        = 428    # left edge of stat bars
_BAR_W        = 270    # total bar width
_BAR_H        = 18     # bar height
_BAR_Y_START  = 400    # top of the first stat bar
_BAR_GAP      = 30     # vertical spacing between bars

_DOT_CY       = 558    # vertical center of the dot row
_HINT_CY      = 585    # vertical center of the swipe hint text

# Tap zone for the mobile back button (top-left corner)
_BACK_RECT = pygame.Rect(18, 12, 100, 36)

# Tap zone for the jet sprite itself (triggers confirm)
_JET_RECT  = pygame.Rect(
    WIDTH // 2 - _PREVIEW_W // 2,
    _PREVIEW_CY - _PREVIEW_H // 2,
    _PREVIEW_W,
    _PREVIEW_H,
)


# ============================================================
# LIFECYCLE
# ============================================================

def init():
    """Load every fighter's sprite at display size.

    Called each time we enter this scene. Safe to call more than once
    (list is rebuilt each time so sprite changes take effect).
    """
    global _fighter_imgs
    _fighter_imgs = []
    for f in fighters_mod.FIGHTERS:
        img = pygame.image.load(asset_path(f["sprite"])).convert_alpha()
        if f["needs_flip"]:
            img = pygame.transform.flip(img, True, False)
        img = pygame.transform.scale(img, (_PREVIEW_W, _PREVIEW_H))
        _fighter_imgs.append(img)


# ============================================================
# UPDATE
# ============================================================

def update(events):
    """One frame of logic. Returns a transition string or None."""

    count = len(fighters_mod.FIGHTERS)
    idx   = fighters_mod.selected_index

    # ---- Back to title ----
    if input_mod.just_pressed('pause'):
        return "title"

    # ---- BACK tap zone (mobile — visible button replaces ESC) ----
    for tx, ty in input_mod.get_taps():
        if _BACK_RECT.collidepoint(tx, ty):
            return "title"

    # ---- Cycle left (previous fighter) ----
    # Keyboard left arrow OR swipe right (finger moved right = card moves right
    # = previous card comes into view — standard carousel behaviour).
    if input_mod.just_pressed('left') or input_mod.get_swipe() == 'right':
        fighters_mod.selected_index = (idx - 1) % count
        return None

    # ---- Cycle right (next fighter) ----
    # Keyboard right arrow OR swipe left (finger moves left = next card).
    if input_mod.just_pressed('right') or input_mod.get_swipe() == 'left':
        fighters_mod.selected_index = (idx + 1) % count
        return None

    # ---- Confirm selection ----
    if input_mod.just_pressed('confirm') or input_mod.just_pressed('fire'):
        return "gameplay"

    # Tap on the jet sprite also confirms
    for tx, ty in input_mod.get_taps():
        if _JET_RECT.collidepoint(tx, ty):
            return "gameplay"

    return None


# ============================================================
# DRAW
# ============================================================

def draw(surf):
    """Render the fighter select screen."""
    surf.fill(BLACK)

    idx     = fighters_mod.selected_index
    fighter = fighters_mod.FIGHTERS[idx]
    img     = _fighter_imgs[idx]
    count   = len(fighters_mod.FIGHTERS)

    # ---- Title ----
    title = fonts.big.render("SELECT YOUR FIGHTER", True, WHITE)
    surf.blit(title, title.get_rect(center=(WIDTH // 2, 48)))

    # ---- Mobile back button ----
    pygame.draw.rect(surf, GRAY, _BACK_RECT, border_radius=4)
    back_lbl = fonts.small.render("< BACK", True, BLACK)
    surf.blit(back_lbl, back_lbl.get_rect(center=_BACK_RECT.center))

    # ---- Left / right cycle arrows ----
    if count > 1:
        left_arrow  = fonts.big.render("<", True, DARK_GRAY)
        right_arrow = fonts.big.render(">", True, DARK_GRAY)
        surf.blit(left_arrow,  left_arrow.get_rect(center=(46, HEIGHT // 2)))
        surf.blit(right_arrow, right_arrow.get_rect(center=(WIDTH - 46, HEIGHT // 2)))

    # ---- Fighter jet preview ----
    jet_rect = img.get_rect(center=(WIDTH // 2, _PREVIEW_CY))
    surf.blit(img, jet_rect)

    # ---- Fighter name ----
    name_surf = fonts.big.render(fighter["name"], True, YELLOW)
    surf.blit(name_surf, name_surf.get_rect(center=(WIDTH // 2, _NAME_CY)))

    # ---- Tagline ----
    tag_surf = fonts.small.render(fighter["tagline"], True, GRAY)
    surf.blit(tag_surf, tag_surf.get_rect(center=(WIDTH // 2, _TAG_CY)))

    # ---- Stat bars ----
    _draw_stat_bars(surf, fighter)

    # ---- Dot indicators ----
    _draw_dots(surf, idx, count)

    # ---- Swipe / tap hint (bottom of screen) ----
    hint = fonts.small.render(
        "< > or swipe to browse    tap jet or SPACE to select",
        True, DARK_GRAY)
    surf.blit(hint, hint.get_rect(center=(WIDTH // 2, _HINT_CY)))


# ============================================================
# HELPERS
# ============================================================

def _draw_stat_bars(surf, fighter):
    """Draw five labeled stat bars derived from the fighter's stats.

    All bar fills are computed from the raw stat values — no separate
    'display stat' fields needed. Ranges are chosen so each fighter
    shows clear visual differentiation.

    Bar fill formula   (clamped 0.0 – 1.0):
      ARMOR      hp / 10
      SPEED      speed / 10
      DAMAGE     bullet_damage / 3
      FIRE RATE  (20 - fire_rate) / 14   (lower fire_rate = faster = taller bar)
      BULLET SPD bullet_speed / 20
    """
    stats = [
        ("ARMOR",      min(1.0, fighter["hp"]            / 10.0)),
        ("SPEED",      min(1.0, fighter["speed"]         / 10.0)),
        ("DAMAGE",     min(1.0, fighter["bullet_damage"] /  3.0)),
        ("FIRE RATE",  min(1.0, (20 - fighter["fire_rate"]) / 14.0)),
        ("BULLET SPD", min(1.0, fighter["bullet_speed"]  / 20.0)),
    ]

    for i, (label, pct) in enumerate(stats):
        y = _BAR_Y_START + i * _BAR_GAP

        # Label — right-aligned to _BAR_LABEL_X
        lbl = fonts.small.render(label, True, WHITE)
        surf.blit(lbl, lbl.get_rect(midright=(_BAR_LABEL_X, y + _BAR_H // 2)))

        # Background track
        pygame.draw.rect(surf, DARK_GRAY, (_BAR_X, y, _BAR_W, _BAR_H))

        # Colored fill
        fill_w = int(_BAR_W * pct)
        if fill_w > 0:
            pygame.draw.rect(surf, _stat_bar_color(pct),
                             (_BAR_X, y, fill_w, _BAR_H))

        # Thin border
        pygame.draw.rect(surf, GRAY, (_BAR_X, y, _BAR_W, _BAR_H), 1)


def _stat_bar_color(pct):
    """Red at 0 → yellow at 0.5 → green at 1.0.

    Gives an intuitive low-medium-high reading at a glance.
    """
    if pct < 0.5:
        t = pct / 0.5
        return (220, int(220 * t), 0)
    else:
        t = (pct - 0.5) / 0.5
        return (int(220 * (1.0 - t)), 220, 0)


def _draw_dots(surf, selected, count):
    """Row of dot indicators — one per fighter, filled for the selected one."""
    spacing = 22
    total_w = (count - 1) * spacing
    start_x = WIDTH // 2 - total_w // 2
    for i in range(count):
        x      = start_x + i * spacing
        filled = (i == selected)
        color  = WHITE if filled else DARK_GRAY
        radius = 6    if filled else 4
        pygame.draw.circle(surf, color, (x, _DOT_CY), radius)