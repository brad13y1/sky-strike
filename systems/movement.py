"""
systems/movement.py
====================
Enemy AI movement patterns.

Each function updates an enemy dict's position ONE frame's worth.
The per-level config in levels/ picks which one to use:

    LEVEL = {
        ...
        "movement": move_sine,           # or move_random_target, etc.
    }

This is the "functions-as-data" pattern — the level dict doesn't
say WHAT TO DO, it says WHICH FUNCTION TO CALL. The gameplay scene
just calls `current_movement(enemy, player)` every frame and the
right movement happens.

The `player` dict is passed to every pattern so player-aware patterns
(move_dive, move_retreat) can read player["x"] / player["y"] without
any extra wiring. Simple patterns like move_sine accept it but ignore it.

To add a new movement pattern:
  1. Write a new function here: def move_*(e, player):
     Update e["x"] / e["y"] and any custom keys (e["phase"], etc.)
  2. Reference it from a level dict in levels/.
  3. That's it — no other code changes needed.
"""

import math
import random

from core.constants import WIDTH, HEIGHT


# ============================================================
# EXISTING PATTERNS  (updated to (e, player) signature)
# ============================================================

def move_sine(e, player):
    """Vertical sine wave through the center.

    Bobs up and down at a steady rate. Used by Level 1 and Level 2.
    The enemy's X position doesn't change — only its Y.
    The `player` argument is accepted but not used (shared signature).
    """
    e["phase"] += 0.025
    e["y"] = HEIGHT // 2 + math.sin(e["phase"]) * 200


def move_random_target(e, player):
    """Fly to a random spot on the right side, pause, repeat.

    Used by Mo-Boss in Level 3. The boss picks a random (X, Y)
    target on the right third of the screen, flies straight toward
    it, pauses briefly when it arrives, then picks another.

    Required keys on the enemy dict (load_level sets these up):
        target_x, target_y   — the current destination
        pause_frames         — how long to pause when reached

    The `player` argument is accepted but not used (shared signature).
    """
    if e["pause_frames"] > 0:
        e["pause_frames"] -= 1
        return

    dx = e["target_x"] - e["x"]
    dy = e["target_y"] - e["y"]
    dist = math.hypot(dx, dy)

    if dist < 12:
        e["pause_frames"] = random.randint(15, 45)
        e["target_x"] = random.randint(WIDTH - 280, WIDTH - 140)
        e["target_y"] = random.randint(100, HEIGHT - 100)
    else:
        speed = 3.5
        e["x"] += (dx / dist) * speed
        e["y"] += (dy / dist) * speed


# ============================================================
# NEW PATTERNS
# ============================================================

def move_dive(e, player):
    """Charge straight toward the player's current Y position.

    Aggressive and scary — the enemy locks onto where the player is
    RIGHT NOW and drives toward that Y. Works best for fast interceptor
    enemies and suicide bombers.

    Tip: pair with a high enemy bullet_speed for maximum pressure.
    """
    speed = 4
    dy = player["y"] - e["y"]
    if abs(dy) > speed:
        e["y"] += speed if dy > 0 else -speed
    else:
        e["y"] = player["y"]


def move_zigzag(e, player):
    """Sharp diagonal bounces between the top and bottom of the screen.

    Faster and more erratic than move_sine. Doesn't track the player —
    purely mechanical. The unpredictable rhythm makes it hard to predict
    where to shoot.

    Uses e["zigzag_dir"] (set in loader.py, default 1) to track the
    current bounce direction. No extra setup needed in level dicts.

    Good for: mid-game enemies, unpredictable feel.
    """
    speed = 5
    e["y"] += speed * e["zigzag_dir"]
    if e["y"] >= HEIGHT - 80:
        e["y"] = HEIGHT - 80
        e["zigzag_dir"] = -1
    elif e["y"] <= 80:
        e["y"] = 80
        e["zigzag_dir"] = 1


def move_strafe(e, player):
    """Hold Y completely still — just a wall of bullets advancing at the player.

    The enemy never moves vertically. Simple but intimidating. Best used
    for heavily-armoured slow enemies or as a contrast after fast movers.

    X is already fixed by the level config — this function does nothing,
    which is the whole point.

    Good for: armoured grunt enemies, level variety through contrast.
    """
    pass   # intentional — no movement is the mechanic


def move_figure_eight(e, player):
    """Loop in a figure-8 / infinity pattern.

    Uses two sine waves: X runs at `phase`, Y runs at `phase * 2`.
    The doubled Y frequency creates the crossover that forms the figure-8.
    Hypnotic and hard to lead a shot on.

    Centre point uses e["center_x"] / e["center_y"] (set in loader.py).
    Override these in a level dict to shift the pattern left/right/up/down.

    Good for: mid-bosses, levels 6-7 complexity.
    """
    e["phase"] += 0.03
    cx = e["center_x"]
    cy = e["center_y"]
    e["x"] = cx + math.sin(e["phase"])     * 120
    e["y"] = cy + math.sin(e["phase"] * 2) * 150


def move_circle(e, player):
    """Orbit a fixed centre point at a constant speed.

    Radius and speed are configurable per level via the enemy dict:
        e["orbit_radius"]   — default 150px (set in loader.py)
        e["center_x/y"]     — default right-side centre (set in loader.py)

    Override in a level dict to create tighter/wider or faster/slower
    orbits. Stacking two circle-pattern enemies at different phases
    creates a hypnotic cross-orbit effect.

    Good for: escort enemies, level 8+ complexity.
    """
    e["phase"] += 0.025
    e["x"] = e["center_x"] + math.cos(e["phase"]) * e["orbit_radius"]
    e["y"] = e["center_y"] + math.sin(e["phase"]) * e["orbit_radius"]


def move_retreat(e, player):
    """Back away when the player gets close. Advance when far away.

    Keeps the enemy just out of comfortable range — frustrating in a
    good way. Perfect for sniper-type enemies that spam long-range
    bullets and punish the player for not closing in.

    e["retreat_threshold"] (default 350px, set in loader.py) is the
    distance that triggers the reversal. Increase it for a more
    aggressive retreater; decrease it to let the player get closer.

    Enemy is clamped to the right side of the screen so it can't
    run off-screen or cross into the player's lane.
    """
    threshold = e["retreat_threshold"]
    dist = math.hypot(player["x"] - e["x"], player["y"] - e["y"])
    speed = 3

    if dist < threshold:
        # Too close — flee directly away from the player.
        dx = e["x"] - player["x"]
        dy = e["y"] - player["y"]
        d = math.hypot(dx, dy)
        if d > 0:
            e["x"] += (dx / d) * speed
            e["y"] += (dy / d) * speed
    else:
        # Far away — drift toward the player.
        dx = player["x"] - e["x"]
        dy = player["y"] - e["y"]
        d = math.hypot(dx, dy)
        if d > 0:
            e["x"] += (dx / d) * speed
            e["y"] += (dy / d) * speed

    # Keep the retreater on the right side of the screen.
    e["x"] = max(WIDTH - 380, min(WIDTH - 80, e["x"]))
    e["y"] = max(80, min(HEIGHT - 80, e["y"]))