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
    BLACK, WHITE, GRAY, GREEN, RED, DARK_RED, YELLOW, CYAN,
)
from core.paths import asset_path
from core import input as input_mod
from core import fonts
from core.haptics import vibrate

from systems import backgrounds, drawing, effects
from systems import scores as scores_mod
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
score               = 0     # accumulated points — resets on new game, not between levels
lives               = 3     # remaining lives — resets on new game, not between levels
life_lost_timer     = 0     # countdown frames before restarting after a death
level_perfect       = True  # flipped False the moment the player takes any hit this level
level_hp_bonus      = 0     # HP survival bonus awarded at end of this level
level_perfect_bonus = 0     # perfect-run bonus awarded at end of this level
level_hp_regen      = 0     # HP regenerated this level (perfect +20%), for display
state            = "playing"
intro_timer      = 0
current_bg       = None
current_movement = None
show_clouds      = True
player_img       = None      # reloaded each level start (fighter may change)
enemy_img        = None
current_weapon   = None      # weapon bundle from systems/weapons.WEAPONS
current_fighter  = None      # selected fighter dict (cached at level start)

# ---- Name-entry state ----
_NE_CHARS       = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
ne_slots        = ['A', 'A', 'A']  # current letter in each slot
ne_cursor       = 0                # which slot the player is editing
ne_from_state   = 'game_over'      # which end-state triggered name entry

# ---- Leaderboard state ----
leaderboard_board   = []   # set when name entry confirms
leaderboard_new_idx = -1   # index of just-placed entry (highlighted in yellow)

# ---- Name-entry UI rects (computed once from constants) ----
_NE_CX         = [WIDTH // 2 - 110, WIDTH // 2, WIDTH // 2 + 110]
_NE_SLOT_RECTS = [pygame.Rect(cx - 40, HEIGHT // 2 - 45, 80, 90)  for cx in _NE_CX]
_NE_UP_RECTS   = [pygame.Rect(cx - 40, HEIGHT // 2 - 103, 80, 50) for cx in _NE_CX]
_NE_DOWN_RECTS = [pygame.Rect(cx - 40, HEIGHT // 2 + 53, 80, 50)  for cx in _NE_CX]
_NE_DONE_RECT  = pygame.Rect(WIDTH // 2 - 90, HEIGHT - 130, 180, 55)


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
    global player, enemy, current_level, score, lives, life_lost_timer, level_perfect, level_hp_bonus, level_perfect_bonus, level_hp_regen
    global current_bg, current_movement, show_clouds, enemy_img, player_img
    global player_bullets, enemy_bullets, state, intro_timer
    global current_weapon, current_fighter

    # Score and lives reset only for a brand-new game.
    if idx == 0:
        score = 0
        lives = 3

    # Per-level trackers reset every level.
    life_lost_timer   = 0
    level_perfect     = True
    level_hp_bonus    = 0
    level_perfect_bonus = 0
    level_hp_regen    = 0

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
        carried_hp = player["hp"]   # preserve HP earned / lost this level
        _start_level(current_level + 1)
        player["hp"] = carried_hp   # patch it back in (loader always resets to full)
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
    elif state == "life_lost":
        _update_life_lost()
    elif state == "name_entry":
        _update_name_entry()
    elif state == "leaderboard":
        if (input_mod.just_pressed('confirm')
            or input_mod.just_pressed('back')
            or input_mod.get_taps()):
            return "title"
    elif state == "level_complete":
        # Advance to next level (tap or any confirm button)
        if (input_mod.just_pressed('next')
            or input_mod.just_pressed('confirm')
            or input_mod.get_taps()):
            _next_level()
    elif state == "game_over":
        # Any positive input starts a brand-new game from level 1
        if (input_mod.just_pressed('confirm')
            or input_mod.just_pressed('back')
            or input_mod.get_taps()):
            _start_level(0)
    elif state == "all_complete":
        # Any positive input starts a brand-new game from level 1
        if (input_mod.just_pressed('confirm')
            or input_mod.just_pressed('back')
            or input_mod.get_taps()):
            _start_level(0)

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
    global state, player_bullets, score, level_hp_bonus, level_perfect_bonus, level_hp_regen

    remaining = []
    for b in player_bullets:
        b["move"](b)

        # Only check collisions while still 'playing'. Once the enemy
        # dies we transition to level_complete and stop registering hits.
        if state == "playing":
            hit, damage = False, 0
            is_crit = False

            # ---- Cockpit hit (inner zone, only if this enemy has one) ----
            # Cockpit is ~50 px left of the enemy's center because the
            # enemy faces left.
            if enemy["hit_cockpit"] is not None:
                cockpit_x = enemy["x"] - 50
                cockpit_dist = math.hypot(
                    b["x"] - cockpit_x, b["y"] - enemy["y"])
                if cockpit_dist < enemy["hit_cockpit"]:
                    hit = True
                    is_crit = True
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
                # ---- Score: award points for the hit ----
                score += 50 if is_crit else 10

                enemy["hp"] -= damage
                effects.add_explosion(b["x"], b["y"], 18, 8)
                if enemy["hp"] <= 0:
                    effects.add_explosion(enemy["x"], enemy["y"], 70, 35)
                    # ---- End-of-level survival bonuses ----
                    level_hp_bonus = int((player["hp"] / player["max_hp"]) * 500)
                    level_perfect_bonus = 1000 if level_perfect else 0
                    score += level_hp_bonus + level_perfect_bonus
                    # ---- Perfect HP regen (+20%, capped at max) ----
                    if level_perfect:
                        regen = int(player["max_hp"] * 0.2)
                        level_hp_regen = min(regen, player["max_hp"] - player["hp"])
                        player["hp"] = min(player["max_hp"], player["hp"] + regen)
                    if current_level + 1 < loader.level_count():
                        # Normal enemy or non-final boss defeated
                        if enemy["boss_name"] is not None:
                            score += 1000  # boss kill bonus
                            vibrate(400)   # boss defeated
                        else:
                            score += 500   # regular enemy kill bonus
                            vibrate(30)    # regular enemy defeated
                        state = "level_complete"
                    else:
                        score += 2500      # final boss kill bonus
                        vibrate(600)       # final boss defeated
                        if scores_mod.qualifies(score):
                            _start_name_entry("all_complete")
                        else:
                            state = "all_complete"
                continue   # bullet consumed by the hit

        # Bullet survived this frame's checks — keep it if still on screen.
        if -50 < b["x"] < WIDTH + 50:
            remaining.append(b)

    player_bullets = remaining


def _update_enemy_bullets():
    """Move every enemy bullet, check for player hits, age out the rest."""
    global state, enemy_bullets, level_perfect, lives, life_lost_timer, score

    remaining = []
    for b in enemy_bullets:
        b["x"] += b["dx"]
        b["y"] += b.get("dy", 0)

        if state == "playing":
            dist = math.hypot(b["x"] - player["x"], b["y"] - player["y"])
            if dist < 50:
                level_perfect = False   # player took a hit — no perfect bonus this level
                player["hp"] -= enemy["damage"]
                effects.add_explosion(b["x"], b["y"], 18, 8)
                if player["hp"] <= 0:
                    effects.add_explosion(player["x"], player["y"], 70, 35)
                    vibrate(300)   # player destroyed
                    score -= 1000  # death penalty
                    lives -= 1
                    if lives <= 0:
                        if scores_mod.qualifies(score):
                            _start_name_entry("game_over")
                        else:
                            state = "game_over"
                    else:
                        state = "life_lost"   # still have lives — show overlay then restart
                        life_lost_timer = 120  # ~2 seconds at 60 fps
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


def _update_life_lost():
    """Tick the life-lost countdown; scenery keeps moving. Auto-restarts when done."""
    global state, life_lost_timer
    life_lost_timer -= 1
    if life_lost_timer <= 0:
        _start_level(current_level)   # restart level with full HP and fresh enemy
        return
    if show_clouds:
        backgrounds.update_clouds()
    backgrounds.update_stars()
    effects.update_all()


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
    if state not in ("game_over", "life_lost", "name_entry", "leaderboard"):
        drawing.draw_player(surf, player_img, player["x"], player["y"])
    if state not in ("level_complete", "name_entry", "leaderboard"):
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
    drawing.draw_hud(surf, player, enemy, current_level, score, lives)

    # ---------- Per-state overlay ----------
    if state == "boss_intro":
        _draw_boss_intro_overlay(surf)
    elif state == "life_lost":
        _draw_life_lost(surf)
    elif state == "name_entry":
        _draw_name_entry(surf)
    elif state == "leaderboard":
        _draw_leaderboard_state(surf)
    elif state == "level_complete":
        _draw_level_complete(surf)
    elif state == "game_over":
        _draw_game_over(surf)
    elif state == "all_complete":
        _draw_all_complete(surf)


def _draw_life_lost(surf):
    """Brief 'LIFE LOST' overlay shown while the explosion plays out."""
    msg = fonts.big.render("LIFE LOST", True, DARK_RED)
    surf.blit(msg, msg.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40)))
    life_word = "life" if lives == 1 else "lives"
    sub = fonts.med.render(f"{lives} {life_word} remaining", True, WHITE)
    surf.blit(sub, sub.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 16)))



def _start_name_entry(from_state):
    """Transition to the name-entry screen after earning a high score."""
    global state, ne_slots, ne_cursor, ne_from_state
    state         = "name_entry"
    ne_slots      = ['A', 'A', 'A']
    ne_cursor     = 0
    ne_from_state = from_state


def _update_name_entry():
    """Handle input for the arcade letter-cycler name entry screen."""
    global ne_slots, ne_cursor, state, leaderboard_board, leaderboard_new_idx

    def _cycle(slot, delta):
        idx = (_NE_CHARS.index(ne_slots[slot]) + delta) % len(_NE_CHARS)
        ne_slots[slot] = _NE_CHARS[idx]

    def _confirm():
        global state, leaderboard_board, leaderboard_new_idx
        name = ''.join(ne_slots)
        board, rank      = scores_mod.insert(name, score)
        leaderboard_board    = board
        leaderboard_new_idx  = rank
        state = "leaderboard"

    # Keyboard / gamepad
    if input_mod.just_pressed('up'):
        _cycle(ne_cursor, +1)
    if input_mod.just_pressed('down'):
        _cycle(ne_cursor, -1)
    if input_mod.just_pressed('left') and ne_cursor > 0:
        ne_cursor -= 1
    if input_mod.just_pressed('right') and ne_cursor < 2:
        ne_cursor += 1
    if input_mod.just_pressed('confirm') or input_mod.just_pressed('fire'):
        _confirm()
        return

    # Touch — tap up/down arrows, slot to select, DONE to confirm
    for tx, ty in input_mod.get_taps():
        if _NE_DONE_RECT.collidepoint(tx, ty):
            _confirm()
            return
        for i in range(3):
            if _NE_UP_RECTS[i].collidepoint(tx, ty):
                ne_cursor = i
                _cycle(i, +1)
            elif _NE_DOWN_RECTS[i].collidepoint(tx, ty):
                ne_cursor = i
                _cycle(i, -1)
            elif _NE_SLOT_RECTS[i].collidepoint(tx, ty):
                ne_cursor = i


def _draw_name_entry(surf):
    """Arcade letter-cycler overlay — semi-transparent so the backdrop shows."""
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))
    surf.blit(overlay, (0, 0))

    # Header
    if ne_from_state == "all_complete":
        header = fonts.big.render("ALL LEVELS COMPLETE!", True, WHITE)
    else:
        header = fonts.big.render("GAME OVER", True, DARK_RED)
    surf.blit(header, header.get_rect(center=(WIDTH // 2, 70)))

    hs = fonts.big.render("NEW HIGH SCORE!", True, YELLOW)
    surf.blit(hs, hs.get_rect(center=(WIDTH // 2, 140)))

    sc = fonts.med.render(f"Score: {score:,}", True, WHITE)
    surf.blit(sc, sc.get_rect(center=(WIDTH // 2, 200)))

    prompt = fonts.med.render("Enter your name:", True, GRAY)
    surf.blit(prompt, prompt.get_rect(center=(WIDTH // 2, 240)))

    # Letter slots + arrows
    for i in range(3):
        active = (i == ne_cursor)
        slot_color  = YELLOW if active else GRAY
        letter_color = YELLOW if active else WHITE

        # Up triangle
        up_r = _NE_UP_RECTS[i]
        cx = up_r.centerx
        pygame.draw.polygon(surf, slot_color,
            [(cx, up_r.top + 6), (cx - 22, up_r.bottom - 6), (cx + 22, up_r.bottom - 6)])

        # Slot box
        s_rect = _NE_SLOT_RECTS[i]
        pygame.draw.rect(surf, slot_color, s_rect, 3, border_radius=8)
        letter = fonts.big.render(ne_slots[i], True, letter_color)
        surf.blit(letter, letter.get_rect(center=s_rect.center))

        # Down triangle
        dn_r = _NE_DOWN_RECTS[i]
        pygame.draw.polygon(surf, slot_color,
            [(cx, dn_r.bottom - 6), (cx - 22, dn_r.top + 6), (cx + 22, dn_r.top + 6)])

    # DONE button
    pygame.draw.rect(surf, YELLOW, _NE_DONE_RECT, border_radius=10)
    done_lbl = fonts.med.render("DONE", True, BLACK)
    surf.blit(done_lbl, done_lbl.get_rect(center=_NE_DONE_RECT.center))

    hint = fonts.small.render("tap ▲ ▼  to change  |  tap slot to select", True, GRAY)
    surf.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT - 30)))


def _draw_leaderboard_state(surf):
    """Full-screen leaderboard shown right after the player enters their name."""
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 210))
    surf.blit(overlay, (0, 0))

    title = fonts.big.render("HIGH SCORES", True, YELLOW)
    surf.blit(title, title.get_rect(center=(WIDTH // 2, 80)))

    for i in range(5):
        if i < len(leaderboard_board):
            e = leaderboard_board[i]
            row_txt = f"{i + 1}.  {e['name']:<3}   {e['score']:>9,}"
            color   = YELLOW if i == leaderboard_new_idx else WHITE
        else:
            row_txt = f"{i + 1}.  ---         ---"
            color   = GRAY
        row = fonts.med.render(row_txt, True, color)
        surf.blit(row, row.get_rect(center=(WIDTH // 2, 180 + i * 56)))

    hint = fonts.small.render("tap to continue", True, GRAY)
    surf.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT - 36)))


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

    skip = fonts.small.render("tap to skip", True, GRAY)
    surf.blit(skip, skip.get_rect(
        center=(WIDTH // 2, HEIGHT // 2 + 60)))


def _draw_level_complete(surf):
    msg = fonts.big.render("LEVEL COMPLETE!", True, BLACK)
    surf.blit(msg, msg.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 80)))

    # Survival bonus breakdown
    hp_line = fonts.med.render(f"Survival Bonus:  +{level_hp_bonus}", True, BLACK)
    surf.blit(hp_line, hp_line.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 36)))

    if level_perfect_bonus > 0:
        perf_line = fonts.med.render(f"PERFECT!  +{level_perfect_bonus}", True, YELLOW)
        surf.blit(perf_line, perf_line.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 4)))

    if level_hp_regen > 0:
        regen_line = fonts.med.render(f"HP Restored:  +{level_hp_regen}", True, GREEN)
        surf.blit(regen_line, regen_line.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 28)))

    sc = fonts.med.render(f"TOTAL SCORE: {score:,}", True, BLACK)
    y_sc = HEIGHT // 2 + (62 if level_hp_regen > 0 else 30)
    surf.blit(sc, sc.get_rect(center=(WIDTH // 2, y_sc)))

    hint = fonts.small.render("tap to continue", True, GRAY)
    surf.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 100)))


def _draw_game_over(surf):
    msg = fonts.big.render("GAME OVER", True, DARK_RED)
    surf.blit(msg, msg.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40)))

    sc = fonts.med.render(f"Final Score: {score:,}", True, BLACK)
    surf.blit(sc, sc.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 10)))

    hint = fonts.small.render("tap to play again", True, GRAY)
    surf.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 60)))


def _draw_all_complete(surf):
    msg1 = fonts.big.render("ALL LEVELS COMPLETE!", True, WHITE)
    surf.blit(msg1, msg1.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 110)))

    msg2 = fonts.med.render("More levels coming soon...", True, WHITE)
    surf.blit(msg2, msg2.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 68)))

    # Final level survival bonus breakdown
    hp_line = fonts.med.render(f"Survival Bonus:  +{level_hp_bonus}", True, WHITE)
    surf.blit(hp_line, hp_line.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30)))

    if level_perfect_bonus > 0:
        perf_line = fonts.med.render(f"PERFECT!  +{level_perfect_bonus}", True, YELLOW)
        surf.blit(perf_line, perf_line.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 2)))

    if level_hp_regen > 0:
        regen_line = fonts.med.render(f"HP Restored:  +{level_hp_regen}", True, GREEN)
        surf.blit(regen_line, regen_line.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 34)))

    sc = fonts.big.render(f"FINAL SCORE: {score:,}", True, YELLOW)
    surf.blit(sc, sc.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 72)))

    hint = fonts.small.render("tap to play again", True, GRAY)
    surf.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 116)))