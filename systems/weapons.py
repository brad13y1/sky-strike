"""
systems/weapons.py
===================
Expandable weapon registry.

Each weapon type is a bundle of three functions stored in the WEAPONS dict:

    "spawn"  -- creates and returns a fresh bullet dict when the player fires
    "move"   -- updates a bullet dict's position by one frame
    "draw"   -- renders a bullet onto a surface

WHY functions-as-data:
  This is the same pattern used by movement.py (enemy AI) and backgrounds.py
  (sky fills). A fighter dict says "weapon": "machine_gun". The gameplay
  scene looks that up in WEAPONS and gets three functions. It never needs
  to know which weapon type it is dealing with — it just calls the functions.

HOW TO ADD A NEW WEAPON (e.g. missiles):
  1. Write _spawn_*, _move_*, _draw_* functions in the section below.
  2. Add one entry to the WEAPONS dict at the bottom of this file.
  3. Set "weapon": "missile" in a fighter dict in levels/fighters.py.
  That is the ENTIRE change required. gameplay.py is never touched.

BULLET DICT KEYS (created by spawn, read by move and draw):
    x, y         -- current position in logical coords
    dx, dy       -- velocity in pixels per frame
    damage       -- hit points removed on a body hit
    size         -- outer radius in pixels (used for draw)
    color_out    -- outer circle color (R, G, B)
    color_in     -- inner circle color (R, G, B)
    move         -- reference to this weapon's move function (baked in at spawn)
    draw         -- reference to this weapon's draw function (baked in at spawn)
"""

import pygame


# ============================================================
# MACHINE GUN
# ============================================================

def _spawn_machine_gun(fighter, player):
    """Spawn one fast round from the nose of the player's jet.

    All bullet properties come from the fighter dict — no hardcoded values.
    """
    return {
        "x":         player["x"] + 70,
        "y":         player["y"],
        "dx":        fighter["bullet_speed"],
        "dy":        0,
        "damage":    fighter["bullet_damage"],
        "size":      fighter["bullet_size"],
        "color_out": fighter["bullet_color_out"],
        "color_in":  fighter["bullet_color_in"],
        "move":      _move_straight,
        "draw":      _draw_round_bullet,
    }


def _move_straight(b):
    """Move a bullet straight right at its dx speed. No vertical drift."""
    b["x"] += b["dx"]


def _draw_round_bullet(surf, b):
    """Two concentric circles: outer color ring, smaller inner color core."""
    pygame.draw.circle(surf, b["color_out"],
                       (int(b["x"]), int(b["y"])), b["size"])
    pygame.draw.circle(surf, b["color_in"],
                       (int(b["x"]), int(b["y"])), max(1, b["size"] // 2))


# ============================================================
# MISSILE  (stub — implement in a later pass)
# ============================================================
# To add missiles:
#
#   def _spawn_missile(fighter, player):
#       return {
#           "x": player["x"] + 70, "y": player["y"],
#           "dx": fighter["bullet_speed"],   # slower than machine gun
#           "dy": 0,
#           "damage":    fighter["bullet_damage"],
#           "size":      fighter["bullet_size"],
#           "color_out": fighter["bullet_color_out"],
#           "color_in":  fighter["bullet_color_in"],
#           "target_y":  player["y"],        # updated each frame to home in
#           "move":      _move_missile,
#           "draw":      _draw_missile,
#       }
#
#   def _move_missile(b):
#       # Gradually steer toward target_y — gentle homing
#       steer = 0.15
#       if b["y"] < b["target_y"]:
#           b["dy"] = min(b["dy"] + steer, 3.0)
#       elif b["y"] > b["target_y"]:
#           b["dy"] = max(b["dy"] - steer, -3.0)
#       b["x"] += b["dx"]
#       b["y"] += b["dy"]
#
#   def _draw_missile(surf, b):
#       # Elongated orange rectangle with a yellow tip
#       rect = pygame.Rect(int(b["x"]) - b["size"], int(b["y"]) - b["size"] // 2,
#                          b["size"] * 2, b["size"])
#       pygame.draw.rect(surf, b["color_out"], rect, border_radius=3)
#       pygame.draw.rect(surf, b["color_in"],
#                        (int(b["x"]), int(b["y"]) - b["size"] // 4,
#                         b["size"], b["size"] // 2))
#
# Then add to WEAPONS:
#   "missile": {
#       "spawn": _spawn_missile,
#       "move":  _move_missile,
#       "draw":  _draw_missile,
#   },


# ============================================================
# LASER  (stub — implement in a later pass)
# ============================================================
# To add a laser:
#
#   def _spawn_laser(fighter, player):
#       return {
#           "x": player["x"] + 70, "y": player["y"],
#           "dx": fighter["bullet_speed"],   # very fast
#           "dy": 0,
#           "damage":    fighter["bullet_damage"],
#           "size":      fighter["bullet_size"],   # thin
#           "color_out": fighter["bullet_color_out"],
#           "color_in":  fighter["bullet_color_in"],
#           "move":      _move_straight,     # same movement as machine gun
#           "draw":      _draw_laser_bolt,
#       }
#
#   def _draw_laser_bolt(surf, b):
#       # Thin horizontal rectangle — a beam rather than a round bullet
#       length = b["size"] * 4
#       rect = pygame.Rect(int(b["x"]) - length // 2, int(b["y"]) - 2,
#                          length, 4)
#       pygame.draw.rect(surf, b["color_out"], rect)
#       inner = pygame.Rect(int(b["x"]) - length // 2, int(b["y"]) - 1,
#                           length, 2)
#       pygame.draw.rect(surf, b["color_in"], inner)
#
# Then add to WEAPONS:
#   "laser": {
#       "spawn": _spawn_laser,
#       "move":  _move_straight,
#       "draw":  _draw_laser_bolt,
#   },


# ============================================================
# REGISTRY
# ============================================================
# Game code does: WEAPONS["machine_gun"]["spawn"](fighter, player)
# Adding a weapon = add a section above + one entry here.

WEAPONS = {
    "machine_gun": {
        "spawn": _spawn_machine_gun,
        "move":  _move_straight,
        "draw":  _draw_round_bullet,
    },
    # "missile": { ... },   # uncomment when implemented above
    # "laser":   { ... },   # uncomment when implemented above
}