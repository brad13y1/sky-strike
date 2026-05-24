"""
systems/drawing.py
===================
Drawing functions for things that AREN'T time-limited effects:
the player jet, the enemy jet, the health bars, and the HUD.

Effects that fade or expire (explosions, crit popups) live in
systems/effects.py — they're rendered there because they need to
manage their own lifetime.

WHY draw_player and draw_enemy take an `img` parameter:
  In the old sky_strike.py these read from module-level `player_img`
  and `enemy_img` globals. That made it hard to tell what they
  depended on. Now the caller passes the image in explicitly —
  one less hidden dependency, and the function works for any
  sprite of any kind.

WHY draw_hud takes player / enemy / current_level:
  Same reason. Anything the function needs is right there in the
  signature, not hidden in module-level state.
"""

import pygame

from core.constants import (
    WIDTH, BLACK, GREEN, RED, GRAY, DARK_GRAY, YELLOW,
)
from core import fonts


# ---- Menu button tap zone ----
# Defined here so gameplay.py can import it for tap detection.
# Sits at the top-center of the screen, between the two HP bars.
# Small enough to be unobtrusive; large enough to tap reliably on a phone.
MENU_RECT = pygame.Rect(WIDTH // 2 - 40, 10, 80, 30)


def draw_player(surf, img, x, y):
    """Draw the player jet image centered at (x, y).

    `img` is whatever the gameplay scene loaded — usually a scaled
    version of assets/sprites/jet.png.
    """
    rect = img.get_rect(center=(x, y))
    surf.blit(img, rect)


def draw_enemy(surf, img, x, y):
    """Draw the enemy/boss jet image centered at (x, y).

    `img` changes per level — load_level() in levels/ reloads the
    right enemy image for whichever level is starting.
    """
    rect = img.get_rect(center=(x, y))
    surf.blit(img, rect)


def draw_health_bar(surf, x, y, w, h, current, maximum, color):
    """Draw a health bar at (x, y), w wide and h tall.

    Three layers, drawn back-to-front:
      1. Black border  (a slightly larger black rect underneath)
      2. Dark gray "empty" track
      3. The colored "filled" portion, sized by current / maximum
    """
    pygame.draw.rect(surf, BLACK, (x - 2, y - 2, w + 4, h + 4))
    pygame.draw.rect(surf, (50, 50, 50), (x, y, w, h))
    pct = max(0, current) / maximum
    pygame.draw.rect(surf, color, (x, y, int(w * pct), h))


def draw_hud(surf, player, enemy, current_level, score=0, lives=3):
    """Top-of-screen heads-up display.

      - [ MENU ] tap button centered at the very top
      - "LEVEL N" centered just below the button
      - Score display below the level number
      - "YOU" label + green player HP bar on the left
      - Life icons (small jets) below the player HP bar
      - "ENEMY" label + red enemy HP bar on the right
      - Boss nameplate above the enemy bar (only if the enemy has one)
    """
    # MENU button — visible tap target for mobile "back to title"
    pygame.draw.rect(surf, DARK_GRAY, MENU_RECT, border_radius=4)
    menu_lbl = fonts.small.render("MENU", True, (200, 200, 200))
    surf.blit(menu_lbl, menu_lbl.get_rect(center=MENU_RECT.center))

    # Level number (centered, shifted down to make room for the button)
    lvl = fonts.med.render(f"LEVEL {current_level + 1}", True, BLACK)
    surf.blit(lvl, (WIDTH // 2 - lvl.get_width() // 2, 46))

    # Score (centered below the level number, in yellow so it pops)
    sc = fonts.small.render(f"{score:,}", True, YELLOW)
    surf.blit(sc, sc.get_rect(center=(WIDTH // 2, 84)))

    # Player HP (left side)
    surf.blit(fonts.small.render("YOU", True, BLACK), (20, 16))
    draw_health_bar(surf, 75, 20, 220, 22,
                    player["hp"], player["max_hp"], GREEN)

    # Lives — small jet-shaped polygons below the HP bar.
    # 3 icons always drawn; lost lives are dimmed to dark gray.
    for i in range(3):
        ix = 20 + i * 28
        iy = 48
        color = GREEN if i < lives else DARK_GRAY
        # Simple arrowhead pointing right to suggest a jet
        points = [(ix, iy + 5), (ix + 18, iy + 9), (ix, iy + 13), (ix + 5, iy + 9)]
        pygame.draw.polygon(surf, color, points)

    # Enemy HP (right side)
    enemy_label = fonts.small.render("ENEMY", True, BLACK)
    surf.blit(enemy_label, (WIDTH - 320, 16))
    draw_health_bar(surf, WIDTH - 230, 20, 220, 22,
                    enemy["hp"], enemy["max_hp"], RED)

    # Boss nameplate, if this enemy has one (Level 3 Mo-Boss etc.)
    if enemy.get("boss_name"):
        name_text = fonts.small.render(enemy["boss_name"], True, RED)
        surf.blit(name_text, (WIDTH - 320, 44))