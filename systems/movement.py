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
just calls `current_movement(enemy)` every frame and the right
movement happens.

To add a new movement pattern:
  1. Write a new function here that takes one argument `e` (the
     enemy dict) and updates `e["x"]` / `e["y"]`.
  2. Reference it from a level dict in levels/.
  3. That's it — no other code changes needed.
"""

import math
import random

from core.constants import WIDTH, HEIGHT


def move_sine(e):
    """Vertical sine wave through the center.

    Bobs up and down at a steady rate. Used by Level 1 and Level 2.
    The enemy's X position doesn't change — only its Y.
    """
    e["phase"] += 0.025
    e["y"] = HEIGHT // 2 + math.sin(e["phase"]) * 200


def move_random_target(e):
    """Fly to a random spot on the right side, pause, repeat.

    Used by Mo-Boss in Level 3. The boss picks a random (X, Y)
    target on the right third of the screen, flies straight toward
    it, pauses briefly when it arrives, then picks another.

    Required keys on the enemy dict (load_level sets these up):
        target_x, target_y   — the current destination
        pause_frames         — how long to pause when reached
    """
    # If we're pausing after reaching a target, just count down.
    if e["pause_frames"] > 0:
        e["pause_frames"] -= 1
        return

    # Vector from the enemy's current position to its target.
    dx = e["target_x"] - e["x"]
    dy = e["target_y"] - e["y"]
    dist = math.hypot(dx, dy)

    if dist < 12:
        # Close enough — pause for a random short time, then pick a
        # new random target somewhere on the right side of the screen.
        e["pause_frames"] = random.randint(15, 45)
        e["target_x"] = random.randint(WIDTH - 280, WIDTH - 140)
        e["target_y"] = random.randint(100, HEIGHT - 100)
    else:
        # Move 3.5 pixels along the direction to the target.
        # Dividing dx/dist gives a unit vector; multiplying by speed
        # gives a movement vector that's always the same length
        # regardless of how far away the target is.
        speed = 3.5
        e["x"] += (dx / dist) * speed
        e["y"] += (dy / dist) * speed