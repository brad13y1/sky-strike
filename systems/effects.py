"""
systems/effects.py
===================
Short-lived visual effects: explosions and CRIT popups.

This module FULLY OWNS its effects:
  - the lists of active explosions / crit popups
  - the rendering of them
  - the per-frame aging (decrementing "frames" and removing dead ones)
  - a clear() function for reset_level

The gameplay scene just calls:
    effects.add_explosion(x, y, size, frames)   # when a hit lands
    effects.add_crit_popup(x, y)                # when a crit lands
    effects.draw_all(surf)                      # once per frame
    effects.update_all()                        # once per frame
    effects.clear()                             # on reset_level

WHY draw_explosion and draw_crit_popup live here instead of
systems/drawing.py: they're not generic drawing — they're internal
to the effects system. Bundling them keeps each effect's full
behavior in one place: how it's added, drawn, aged, removed.
"""

import pygame

from core.constants import RED, ORANGE, YELLOW
from core import fonts


# ============================================================
# DATA
# ============================================================
# Each explosion: {"x", "y", "size", "frames"}
# Each crit popup: {"x", "y", "frames"}
# 'frames' is how many MORE frames the effect should live for.

explosions  = []
crit_popups = []


# ============================================================
# ADD
# ============================================================

def add_explosion(x, y, size, frames):
    """Spawn an explosion at (x, y).

    size:   the outer red circle's radius in pixels
    frames: how long the explosion is visible (60 = 1 second)
    """
    explosions.append({"x": x, "y": y, "size": size, "frames": frames})


def add_crit_popup(x, y, frames=20):
    """Spawn a yellow 'CRIT!' that drifts up and fades out."""
    crit_popups.append({"x": x, "y": y, "frames": frames})


# ============================================================
# CLEAR
# ============================================================

def clear():
    """Wipe ALL effects. Called by reset_level / next_level so the
    new level doesn't inherit visuals from the previous one."""
    global explosions, crit_popups
    explosions  = []
    crit_popups = []


# ============================================================
# RENDER  (internal helpers)
# ============================================================

def _draw_explosion(surf, x, y, size):
    """Three concentric circles — red outside, orange middle, yellow core."""
    pygame.draw.circle(surf, RED,    (int(x), int(y)), int(size))
    pygame.draw.circle(surf, ORANGE, (int(x), int(y)), int(size * 0.7))
    pygame.draw.circle(surf, YELLOW, (int(x), int(y)), int(size * 0.35))


def _draw_crit_popup(surf, x, y, frames):
    """Yellow 'CRIT!' text that drifts upward and fades out as it ages.

    Drift: y position rises by 1.5 px per frame as frames count down.
    Fade:  alpha = frames * 13 (so 20 -> 255 down to 0 -> 0).
    """
    drift_y = y - (20 - frames) * 1.5
    alpha = max(0, min(255, frames * 13))
    crit_surf = fonts.med.render("CRIT!", True, YELLOW)
    crit_surf.set_alpha(alpha)
    rect = crit_surf.get_rect(center=(int(x), int(drift_y)))
    surf.blit(crit_surf, rect)


# ============================================================
# DRAW + UPDATE  (called by the gameplay scene each frame)
# ============================================================

def draw_all(surf):
    """Draw every active effect. Doesn't age them — call update_all()
    after this to age + remove dead ones."""
    for e in explosions:
        _draw_explosion(surf, e["x"], e["y"], e["size"])
    for c in crit_popups:
        _draw_crit_popup(surf, c["x"], c["y"], c["frames"])


def update_all():
    """Age every effect by one frame and remove any that have expired."""
    global explosions, crit_popups

    remaining_ex = []
    for e in explosions:
        e["frames"] -= 1
        if e["frames"] > 0:
            remaining_ex.append(e)
    explosions = remaining_ex

    remaining_cp = []
    for c in crit_popups:
        c["frames"] -= 1
        if c["frames"] > 0:
            remaining_cp.append(c)
    crit_popups = remaining_cp