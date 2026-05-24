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

    NOTE: With the current fixed-X player this pattern is visually very plain
    (enemy just sits still and fires). Kept for when player X movement is added —
    at that point a completely still enemy becomes a genuine threat to dodge around.

    Good for: armoured grunt enemies once player can move horizontally.
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

    # NOTE: With current fixed-X player, X-axis retreat has no effect —
    # the enemy just hovers in place. Full behaviour unlocks when player
    # X movement is added. The Y-axis component still gives slight life.

# ============================================================
# ELABORATE PATTERNS  (8 new — designed for levels 6-30)
# ============================================================

def move_hunter(e, player):
    """Track the player in BOTH X and Y — closes the gap relentlessly.

    Unlike move_dive (Y only), the hunter moves toward the player's full
    position. With a fixed-X player this means it also slowly advances
    horizontally, shrinking the safe distance over the course of the fight.

    Clamped so it can't invade the player's side of the screen — it hunts
    but can't quite catch you. Speed is intentionally low so the player
    can still outmanoeuvre it, but only just.

    Good for: mid-game pressure enemy, pairs well with high fire-rate.
    """
    speed = 2.5
    dx = player["x"] - e["x"]
    dy = player["y"] - e["y"]
    dist = math.hypot(dx, dy)
    if dist > speed:
        e["x"] += (dx / dist) * speed
        e["y"] += (dy / dist) * speed
    # Never cross into the player's half of the screen
    e["x"] = max(int(WIDTH * 0.42), min(WIDTH - 60, e["x"]))
    e["y"] = max(60, min(HEIGHT - 60, e["y"]))


def move_phase_shift(e, player):
    """Alternate between an aggressive charge phase and an evasive phase.

    Phase 0 — CHARGE (150 frames / ~2.5 s):
        Aggressively tracks player Y at high speed. Feels like a dive-bomb.
    Phase 1 — EVADE (90 frames / ~1.5 s):
        Snaps away to the opposite Y of the player — forces the player to
        reposition before the next charge.

    State keys (self-initialised on first call):
        phase_mode    0 = charge, 1 = evade
        phase_timer   frames remaining in current phase

    Good for: any level where you want a boss that switches personalities.
    """
    e.setdefault("phase_mode",  0)
    e.setdefault("phase_timer", 150)

    e["phase_timer"] -= 1
    if e["phase_timer"] <= 0:
        e["phase_mode"]  = 1 - e["phase_mode"]       # toggle 0 ↔ 1
        e["phase_timer"] = 90 if e["phase_mode"] else 150

    if e["phase_mode"] == 0:
        # Charge — snap toward player Y
        speed = 7
        dy = player["y"] - e["y"]
        e["y"] += max(-speed, min(speed, dy))
    else:
        # Evade — move to opposite Y
        target_y = HEIGHT - player["y"]
        speed = 4
        dy = target_y - e["y"]
        e["y"] += max(-speed, min(speed, dy))

    e["y"] = max(60, min(HEIGHT - 60, e["y"]))


def move_pendulum(e, player):
    """Full-screen pendulum sweep with natural easing.

    Mathematically identical to sine but with a nearly full-screen amplitude
    and a faster phase — feels physically heavier and more threatening.
    The enemy spends less time near the centre (moving fast through it) and
    briefly pauses at the screen edges before reversing, like a real pendulum.

    Configurable per level (override in level dict):
        pendulum_top   — upper Y boundary (default 60)
        pendulum_bot   — lower Y boundary (default HEIGHT - 60)

    Good for: early-mid game variety; strong visual contrast to move_sine.
    """
    e["phase"] += 0.05
    top = e.get("pendulum_top", 60)
    bot = e.get("pendulum_bot", HEIGHT - 60)
    mid = (top + bot) / 2
    amp = (bot - top) / 2
    e["y"] = mid + math.sin(e["phase"]) * amp


def move_swarm(e, player):
    """Orbit on an advancing centre that slowly closes in on the player.

    The orbit centre starts on the far right of the screen and steps
    closer to the player every `swarm_advance_timer` frames — so the
    enemy circles at a safe distance early in the fight, then gradually
    invades the player's space as the battle goes on.

    Centre Y tracks the player's Y each frame (keeps it feeling alive).
    Centre X only advances on the timer — never instantly jumps.

    Stops advancing once the orbit centre is within 280px of the player
    so the enemy never completely engulfs the player's position.

    Configurable per level:
        swarm_radius         — orbit radius (default 180px)
        swarm_advance_timer  — frames between each step (default 120 = 2 s)

    Good for: escalating pressure enemy, mid-boss behaviour.
    """
    e.setdefault("swarm_center_x",      float(WIDTH - 180))
    e.setdefault("swarm_advance_timer",  120)

    e["phase"] += 0.045
    radius = e.get("swarm_radius", 180)

    # Tick down and step the orbit centre closer on each expiry
    e["swarm_advance_timer"] -= 1
    if e["swarm_advance_timer"] <= 0:
        e["swarm_advance_timer"] = 120
        min_cx = player["x"] + 280          # closest the centre is allowed
        if e["swarm_center_x"] > min_cx:
            e["swarm_center_x"] = max(min_cx, e["swarm_center_x"] - 40)

    # Orbit around the advancing centre; Y tracks player each frame
    e["x"] = e["swarm_center_x"] + math.cos(e["phase"]) * radius
    e["y"] = player["y"]         + math.sin(e["phase"]) * radius
    e["x"] = max(int(WIDTH * 0.38), min(WIDTH - 40, e["x"]))
    e["y"] = max(40, min(HEIGHT - 40, e["y"]))


def move_ambush(e, player):
    """Hold completely still for N frames, then dash toward the player.

    The stillness is the threat — the player watches the enemy doing nothing
    while bullets still rain in, then suddenly it MOVES in both X and Y,
    closing the gap fast. The delay makes the dash psychologically scarier
    than if it just started moving immediately.

    After the hold the enemy dashes toward the player's full position
    (both axes) and keeps closing until clamped — it doesn't reset or
    pause again, so it becomes a relentless chaser after the trigger.

    State keys (self-initialised on first call):
        ambush_timer   frames to hold still (default 120 = 2 s at 60 fps)

    Good for: first appearance of a new enemy type, boss openers.
    """
    e.setdefault("ambush_timer", 120)

    if e["ambush_timer"] > 0:
        e["ambush_timer"] -= 1
        return   # stone still

    # Ambush triggered — dash toward player in both X and Y
    speed = 8
    dx = player["x"] - e["x"]
    dy = player["y"] - e["y"]
    dist = math.hypot(dx, dy)
    if dist > speed:
        e["x"] += (dx / dist) * speed
        e["y"] += (dy / dist) * speed
    # Don't cross fully into the player's side
    e["x"] = max(int(WIDTH * 0.42), min(WIDTH - 60, e["x"]))
    e["y"] = max(60, min(HEIGHT - 60, e["y"]))


def move_coil(e, player):
    """Circular orbit with a pulsing radius — creates a spiralling coil effect.

    Like move_circle but the radius expands and contracts on a slower
    secondary cycle, so the path traces an inward-outward coil rather than
    a clean ring. Very hard to lead a shot on because the enemy's distance
    from the centre constantly shifts.

    Uses center_x / center_y from the enemy dict (same defaults as
    move_circle). Override coil_radius in a level dict for tighter/wider coils.

    Configurable: coil_radius (default 120px base, pulses ±70px)

    Good for: mid-boss, level 10+ where the player needs a new challenge.
    """
    e["phase"] += 0.035
    base_r = e.get("coil_radius", 120)
    radius = base_r + math.sin(e["phase"] * 0.4) * 70
    e["x"] = e["center_x"] + math.cos(e["phase"]) * radius
    e["y"] = e["center_y"] + math.sin(e["phase"]) * radius
    e["x"] = max(int(WIDTH * 0.38), min(WIDTH - 40, e["x"]))
    e["y"] = max(40, min(HEIGHT - 40, e["y"]))


def move_mirror(e, player):
    """Always position at the Y-axis mirror of the player.

    Player moves up → enemy moves down. Player moves down → enemy moves up.
    Forces the player to deliberately mis-position themselves to line up a
    shot — you can't just track the enemy, you have to think in reverse.

    Smooth drift rather than instant snap so the player has a brief window
    to shoot during the transition.

    Good for: tactical mid-game enemy, very different feel to anything else.
    """
    mirror_y = HEIGHT - player["y"]
    speed = 5
    dy = mirror_y - e["y"]
    e["y"] += max(-speed, min(speed, dy))
    e["y"] = max(60, min(HEIGHT - 60, e["y"]))


def move_erratic(e, player):
    """Sine base with random velocity kicks — like a damaged or panicking enemy.

    Most of the time the enemy follows a gentle sine path, but every 25–60
    frames it gets a random velocity impulse that knocks it off course. The
    impulse damps back to zero so it gradually returns to the sine path before
    the next kick hits.

    The result feels alive — the enemy is unpredictable without being pure
    noise. Good for late-game enemies that should feel desperate or frantic.

    State keys (self-initialised on first call):
        erratic_timer   frames until next random kick
        erratic_dy      current random velocity offset (damps toward 0)

    Good for: damaged boss second-phase, swarm-style enemies, level 15+.
    """
    e.setdefault("erratic_timer", random.randint(25, 60))
    e.setdefault("erratic_dy",    0.0)

    e["erratic_timer"] -= 1
    if e["erratic_timer"] <= 0:
        e["erratic_dy"]    = random.uniform(-7, 7)
        e["erratic_timer"] = random.randint(25, 60)

    e["erratic_dy"] *= 0.93   # dampen toward zero between kicks

    base_y = HEIGHT // 2 + math.sin(e["phase"]) * 150
    e["phase"] += 0.03
    e["y"] += (base_y - e["y"]) * 0.06 + e["erratic_dy"]
    e["y"] = max(60, min(HEIGHT - 60, e["y"]))