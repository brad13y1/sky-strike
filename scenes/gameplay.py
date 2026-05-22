"""
scenes/gameplay.py
===================
The actual game. This file owns:

  - The player and enemy state (dicts loaded by load_level)
  - The bullet lists for both sides
  - Which level is currently active
  - Which sub-state we're in (see STATES below)

It glues together everything in core/ and systems/ and levels/ —
this is where the game actually plays.

SUB-STATES
  This scene has its own internal state machine because four screens
  share the gameplay backdrop (the level art, the player, the enemy)
  and shouldn't be separate scenes:

    "playing"         normal gameplay
    "boss_intro"      flashing "BOSS APPROACHES" overlay before a boss
    "level_complete"  defeat enemy on a non-final level
    "game_over"       player died
    "all_complete"    defeated the final level

  Each sub-state has its own update logic and its own overlay drawn
  on top of the gameplay scene.

CONTROLS
  up / down / left / right   move
  fire (held)                shoot
  pause                      -> back to title (from any sub-state)
  level_complete:  next  = next level
                   back  = restart this level
  game_over:       confirm OR back = restart this level
  all_complete:    back  = restart last level
  boss_intro:      any movement / action button = skip the intro
"""

import math
import pygame

from core.constants import (
    WIDTH, HEIGHT,
    BLACK, WHITE, GRAY, RED, DARK_RED, YELLOW, CYAN,
)
from core.paths import asset_path
from core import input as input_mod
from core import fonts
from core.haptics import vibrate

from systems import backgrounds, drawing, effects
from systems.drawing import MENU_RECT
from levels import loader
from levels import fighters as fighters_mod
from systems.weapons import WEAPONS


# ============================================================
# MODULE STATE
# ============================================================
# Initialized by init() and _start_level().

player           = None      # dict: x, y, hp, max_hp, cooldown, speed
enemy            = None      # dict: x, y, hp, max_hp, fire_rate, ...
player_bullets   = []        # each: {"x", "y", "dx"}
enemy_bullets    = []        # each: {"x", "y", "dx", "dy"}
current_level    = 0
state            = "playing"
intro_timer      = 0
current_bg       = None
current_movement = None
show_clouds      = True
player_img       = None      # reloaded each level start (fighter may change)
enemy_img        = None
current_weapon   = None      # weapon bundle from systems/weapons.WEAPONS
current_fighter  = None      # selected fighter dict (cached at level start)


# ============================================================
# LIFECYCLE
# ============================================================

def init():
    """Called when entering gameplay from the fighter select scene.

    Sprite loading happens inside _start_level() so the correct
    fighter sprite is always used, even if the player picks a
    different fighter between games.
    """
    _start_level(0)


def _start_level(idx):
    """Reset and load level `idx`. Called by init, restart, and next."""
    global player, enemy, current_level
    global current_bg, current_movement, show_clouds, enemy_img, player_img
    global player_bullets, enemy_bullets, state, intro_timer
    global current_weapon, current_fighter

    current_level = idx
    bundle = loader.load_level(idx)

    # ---- Fighter sprite and weapon ----
    current_fighter = fighters_mod.get_selected()
    player_img = pygame.image.load(
        asset_path(current_fighter["sprite"])
    ).convert_alpha()
    if current_fighter["needs_flip"]:
        player_img = pygame.transform.flip(player_img, True, False)
    player_img = pygame.transform.scale(player_img, current_fighter["size"])
    current_weapon = WEAPONS[current_fighter["weapon"]]

    player           = bundle["player"]
    enemy            = bundle["enemy"]
    current_bg       = bundle["background"]
    current_movement = bundle["movement"]
    show_clouds      = bundle["show_clouds"]
    enemy_img        = bundle["enemy_img"]

    player_bullets = []
    enemy_bullets  = []
    effects.clear()

    if bundle["has_boss_intro"]:
        state       = "boss_intro"
        intro_timer = 120
    else:
        state = "playing"


def _restart_level():
    """Reload the current level cleanly."""
    _start_level(current_level)


def _next_level():
    """Advance to the next level — or trigger all_complete if there isn't one."""
    global state
    if current_level + 1 < loader.level_count():
        _start_level(current_level + 1)
    else:
        state = "all_complete"


# ============================================================
# UPDATE
# ============================================================

def update(events):
    """Run one frame of logic. Returns a transition string or None."""

    # ESC / START from ANY sub-state -> back to title.
    if input_mod.just_pressed('pause'):
        return "title"

    # MENU button tap (mobile) — tap-only so accidental swipes don't trigger it.
    for tx, ty in input_mod.get_taps():
        if MENU_RECT.collidepoint(tx, ty):
            return "title"

    if state == "playing":
        _update_playing()
    elif state == "boss_intro":
        _update_boss_intro()
    elif state == "level_complete":
        # Primary advance: next-level (N / A / Enter / tap)
        if (input_mod.just_pressed('next')
            or input_mod.just_pressed('confirm')
            or input_mod.get_taps()):
            _next_level()
        # Alternative: restart this level (B / R / Backspace)
        elif input_mod.just_pressed('back'):
            _restart_level()
    elif state == "game_over":
        # Any positive input retries the level
        if (input_mod.just_pressed('confirm')
            or input_mod.just_pressed('back')
            or input_mod.get_taps()):
            _restart_level()
    elif state == "all_complete":
        # Any positive input replays the final level
        if (input_mod.just_pressed('confirm')
            or input_mod.just_pressed('back')
            or input_mod.get_taps()):
            _restart_level()

    return None


def _update_playing():
    """One frame of actual gameplay: input -> AI -> bullets -> world."""

    # ---------- Player movement + fire-intent ----------
    # Touch takes priority while held: the jet snaps to the finger position
    # and auto-fires. When no finger is held, fall through to the
    # keyboard / gamepad path.
    # X movement is clamped to the player's half of the screen (80-500)
    # to keep the jet out of the enemy's territory and off the left edge.
    PLAYER_X_MIN, PLAYER_X_MAX = 80, 80

    if input_mod.touch_held():
        tx, ty = input_mod.touch_pos()
        player["x"] = max(PLAYER_X_MIN, min(PLAYER_X_MAX, tx))
        player["y"] = max(60, min(HEIGHT - 60, ty - 60))
        fire = True
    else:
        move_y = 0
        if input_mod.is_pressed('up'):
            move_y = -player["speed"]
        elif input_mod.is_pressed('down'):
            move_y = player["speed"]

        move_x = 0
        if input_mod.is_pressed('left'):
            move_x = -player["speed"]
        elif input_mod.is_pressed('right'):
            move_x = player["speed"]

        player["y"] += move_y
        player["x"] += move_x
        # Clamp inside the play area (jet is ~60px tall / ~60px wide)
        player["y"] = max(60, min(HEIGHT - 60, player["y"]))
        player["x"] = max(PLAYER_X_MIN, min(PLAYER_X_MAX, player["x"]))
        fire = input_mod.is_pressed('fire')

    # ---------- Player firing (cooldown applies to both input paths) ----------
    player["cooldown"] -= 1
    if fire and player["cooldown"] <= 0:
        player_bullets.append(current_weapon["spawn"](current_fighter, player))
        player["cooldown"] = current_fighter["fire_rate"]

    # ---------- Enemy movement (whichever pattern this level uses) ----------
    # player dict passed so patterns like move_dive / move_retreat can
    # read player["x"] / player["y"] without needing a separate parameter.
    current_movement(enemy, player)

    # ---------- Enemy firing ----------
    enemy["cooldown"] -= 1
    if enemy["cooldown"] <= 0:
        # Lead the shot slightly toward the player's current Y.
        dy = (player["y"] - enemy["y"]) / 60.0
        enemy_bullets.append({
            "x": enemy["x"] - 70,
            "y": enemy["y"],
            "dx": -enemy["bullet_speed"],
            "dy": dy,
        })
        enemy["cooldown"] = enemy["fire_rate"]

    # ---------- Bullets ----------
    _update_player_bullets()
    _update_enemy_bullets()

    # ---------- Scenery + effects ----------
    if show_clouds:
        backgrounds.update_clouds()
    backgrounds.update_stars()
    effects.update_all()


def _update_player_bullets():
    """Move every player bullet, check for hits, age out off-screen ones."""
    global state, player_bullets

    remaining = []
    for b in player_bullets:
        b["move"](b)

        # Only check collisions while still 'playing'. Once the enemy
        # dies we transition to level_complete and stop registering hits.
        if state == "playing":
            hit, damage = False, 0

            # ---- Cockpit hit (inner zone, only if this enemy has one) ----
            # Cockpit is ~50 px left of the enemy's center because the
            # enemy faces left.
            if enemy["hit_cockpit"] is not None:
                cockpit_x = enemy["x"] - 50
                cockpit_dist = math.hypot(
                    b["x"] - cockpit_x, b["y"] - enemy["y"])
                if cockpit_dist < enemy["hit_cockpit"]:
                    hit = True
                    damage = enemy["hit_cockpit_damage"]
                    effects.add_crit_popup(b["x"], b["y"])

            # ---- Body hit (only if cockpit didn't already register) ----
            if not hit:
                body_dist = math.hypot(
                    b["x"] - enemy["x"], b["y"] - enemy["y"])
                if body_dist < enemy["hit_body"]:
                    hit = True
                    damage = b["damage"]

            if hit:
                enemy["hp"] -= damage
                effects.add_explosion(b["x"], b["y"], 18, 8)
                if enemy["hp"] <= 0:
                    effects.add_explosion(enemy["x"], enemy["y"], 70, 35)
                    if current_level + 1 < loader.level_count():
                        # Normal enemy or non-final boss defeated
                        if enemy["boss_name"] is not None:
                            vibrate(400)   # boss defeated
                        else:
                            vibrate(30)    # regular enemy defeated
                        state = "level_complete"
                    else:
                        vibrate(600)       # final boss defeated
                        state = "all_complete"
                continue   # bullet consumed by the hit

        # Bullet survived this frame's checks — keep it if still on screen.
        if -50 < b["x"] < WIDTH + 50:
            remaining.append(b)

    player_bullets = remaining


def _update_enemy_bullets():
    """Move every enemy bullet, check for player hits, age out the rest."""
    global state, enemy_bullets

    remaining = []
    for b in enemy_bullets:
        b["x"] += b["dx"]
        b["y"] += b.get("dy", 0)

        if state == "playing":
            dist = math.hypot(b["x"] - player["x"], b["y"] - player["y"])
            if dist < 50:
                player["hp"] -= enemy["damage"]
                effects.add_explosion(b["x"], b["y"], 18, 8)
                if player["hp"] <= 0:
                    effects.add_explosion(player["x"], player["y"], 70, 35)
                    vibrate(300)   # player destroyed
                    state = "game_over"
                else:
                    vibrate(80)    # player hit
                continue   # bullet consumed

        if -50 < b["x"] < WIDTH + 50:
            remaining.append(b)

    enemy_bullets = remaining


def _update_boss_intro():
    """Tick the intro countdown; let movement / action buttons skip it."""
    global state, intro_timer

    intro_timer -= 1
    if intro_timer <= 0:
        state = "playing"
        return

    # Any meaningful input (movement, fire, confirm, etc.) skips the intro.
    # 'pause' is already handled at the top of update() to route to title.
    SKIPPERS = ('confirm', 'fire', 'next', 'back',
                'up', 'down', 'left', 'right')
    for a in SKIPPERS:
        if input_mod.just_pressed(a):
            state = "playing"
            return

    # Touchscreen: any tap also skips.
    if input_mod.get_taps():
        state = "playing"
        return

    # Keep scenery moving so the world doesn't freeze during the intro.
    if show_clouds:
        backgrounds.update_clouds()
    backgrounds.update_stars()


# ============================================================
# DRAW
# ============================================================

def draw(surf):
    """Render this frame to the logical surface."""

    # ---------- Backdrop ----------
    current_bg(surf)
    if show_clouds:
        backgrounds.draw_clouds(surf)

    # ---------- Sprites ----------
    # Hide the player if they died this frame; hide the enemy if the
    # level is complete (so the victory message has a clean backdrop).
    if state != "game_over":
        drawing.draw_player(surf, player_img, player["x"], player["y"])
    if state != "level_complete":
        drawing.draw_enemy(surf, enemy_img, enemy["x"], enemy["y"])

    # ---------- Bullets ----------
    for b in player_bullets:
        b["draw"](surf, b)
    for b in enemy_bullets:
        pygame.draw.circle(surf, RED,    (int(b["x"]), int(b["y"])), 6)
        pygame.draw.circle(surf, YELLOW, (int(b["x"]), int(b["y"])), 3)

    # ---------- Effects (explosions, CRIT popups) ----------
    effects.draw_all(surf)

    # ---------- HUD ----------
    drawing.draw_hud(surf, player, enemy, current_level)

    # ---------- Per-state overlay ----------
    if state == "boss_intro":
        _draw_boss_intro_overlay(surf)
    elif state == "level_complete":
        _draw_level_complete(surf)
    elif state == "game_over":
        _draw_game_over(surf)
    elif state == "all_complete":
        _draw_all_complete(surf)


def _draw_boss_intro_overlay(surf):
    """Flashing 'BOSS APPROACHES' over the (motionless) battlefield."""
    flash_on = (intro_timer // 10) % 2 == 0
    title_color = YELLOW if flash_on else RED

    title = fonts.big.render(
        f"{enemy['boss_name']} APPROACHES!", True, title_color)
    surf.blit(title, title.get_rect(
        center=(WIDTH // 2, HEIGHT // 2 - 60)))

    sub = fonts.med.render("Get ready...", True, WHITE)
    surf.blit(sub, sub.get_rect(
        center=(WIDTH // 2, HEIGHT // 2 + 10)))

    skip = fonts.small.render("(any button to skip)", True, GRAY)
    surf.blit(skip, skip.get_rect(
        center=(WIDTH // 2, HEIGHT // 2 + 60)))


def _draw_level_complete(surf):
    msg = fonts.big.render("LEVEL COMPLETE!", True, BLACK)
    surf.blit(msg, msg.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 80)))

    opt1 = fonts.med.render("A / N  -  Next Level", True, BLACK)
    surf.blit(opt1, opt1.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 10)))

    opt2 = fonts.med.render("B / R  -  Restart Level", True, BLACK)
    surf.blit(opt2, opt2.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30)))

    opt3 = fonts.med.render("START / ESC  -  Title Screen", True, BLACK)
    surf.blit(opt3, opt3.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 70)))


def _draw_game_over(surf):
    msg = fonts.big.render("GAME OVER", True, DARK_RED)
    surf.blit(msg, msg.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 60)))

    opt1 = fonts.med.render("A / R  -  Try Again", True, BLACK)
    surf.blit(opt1, opt1.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 10)))

    opt2 = fonts.med.render("START / ESC  -  Title Screen", True, BLACK)
    surf.blit(opt2, opt2.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50)))


def _draw_all_complete(surf):
    msg1 = fonts.big.render("ALL LEVELS COMPLETE!", True, WHITE)
    surf.blit(msg1, msg1.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100)))

    msg2 = fonts.med.render("More levels coming soon...", True, WHITE)
    surf.blit(msg2, msg2.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40)))

    opt1 = fonts.med.render("B / R  -  Replay Last Level", True, WHITE)
    surf.blit(opt1, opt1.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30)))

    opt2 = fonts.med.render("START / ESC  -  Title Screen", True, WHITE)
    surf.blit(opt2, opt2.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 70)))