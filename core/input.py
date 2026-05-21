"""
core/input.py
==============
Unified input layer. Game code asks for named ACTIONS — like 'fire'
or 'up' — and the input system figures out whether a keyboard key,
gamepad button, gamepad hat (D-pad), gamepad axis (stick), or a
touchscreen tap triggered it.

WHY this exists:
  Sky Strike has four ways to play:
    - Keyboard
    - Gamepad (8BitDo Pro 2 in XInput mode, or any compatible pad)
    - Touchscreen on the Pi 4B 7" display
    - Touchscreen in a mobile/tablet browser

  Without this layer, every place in the game that checks input
  would have to write something like:
      if event.key == K_SPACE or button == 0 or mouse_in_fire_zone:
  ...and every time we added a new control we'd have to update all
  of those places.

  With this layer, game code says:
      if input.just_pressed('fire'):
  ...and the input system handles which source it came from.

ACTIONS  (game-level concepts, not hardware):
    'up' / 'down' / 'left' / 'right' — directional movement
    'fire'                             — shoot
    'confirm'                          — A button / SPACE / RETURN / N
    'next'                             — N key / A button (level complete)
    'back'                             — B button / R key (restart)
    'pause'                            — START button / ESC

USAGE:
    # Once at startup, after pygame.init():
    input_mod.init()

    # Every frame, BEFORE reading input:
    events = pygame.event.get()
    input_mod.update(events)

    # Then anywhere in game code:
    if input_mod.is_pressed('up'):       ...   # currently held
    if input_mod.just_pressed('fire'):   ...   # newly pressed this frame
    if input_mod.just_released('confirm'): ... # released this frame
"""

import pygame
from core import display


# ============================================================
# BINDINGS
# ============================================================
# Each ACTION maps to a list of SOURCES that can trigger it.
# A source is a tuple:  (kind, payload)
#
#   ('key',    pygame.K_SPACE)   keyboard key
#   ('button', 0)                gamepad button index
#                                  (0=A on XInput, 1=B, 7=START)
#   ('hat',    (0, 1))           gamepad D-pad direction (x, y)
#                                  (0, 1)=up, (0,-1)=down,
#                                  (-1,0)=left, (1,0)=right
#   ('axis',   (1, -1))          gamepad analog stick (idx, direction)
#                                  axis 1 = left stick vertical;
#                                  direction -1 = up, +1 = down.
#                                  Deadzone is applied automatically.
#   ('touch',  pygame.Rect(...)) tap inside this rect (LOGICAL coords)
#
# RULES:
#   - To REBIND a control, edit the list for that action.
#   - To ADD a touchscreen button, add a ('touch', rect) entry.
#     The rect is in logical coordinates (the 1024x600 game canvas),
#     NOT screen coordinates — display.to_logical() handles that.
#   - Multiple sources are OR'd together — ANY ONE triggers the action.

BINDINGS = {
    'up':      [('key', pygame.K_UP),    ('key', pygame.K_w),
                ('hat', (0,  1)), ('axis', (1, -1))],

    'down':    [('key', pygame.K_DOWN),  ('key', pygame.K_s),
                ('hat', (0, -1)), ('axis', (1,  1))],

    'left':    [('key', pygame.K_LEFT),  ('key', pygame.K_a),
                ('hat', (-1, 0)), ('axis', (0, -1))],

    'right':   [('key', pygame.K_RIGHT), ('key', pygame.K_d),
                ('hat', (1,  0)), ('axis', (0,  1))],

    'fire':    [('key', pygame.K_SPACE),
                ('button', 0)],

    'confirm': [('key', pygame.K_RETURN), ('key', pygame.K_a),
                ('button', 0)],

    'next':    [('key', pygame.K_n),
                ('button', 0)],

    'back':    [('key', pygame.K_b),         ('key', pygame.K_r),
                ('key', pygame.K_BACKSPACE),
                ('button', 1)],

    'pause':   [('key', pygame.K_ESCAPE),
                ('button', 7)],
}

AXIS_DEADZONE = 0.25  # stick must move past this before it counts


# ============================================================
# MODULE STATE
# ============================================================

_pressed      = set()  # actions held THIS frame
_pressed_last = set()  # actions held LAST frame (for edge detection)
_joystick     = None   # gamepad object, or None if no pad attached
_taps         = []     # tap positions this frame, in logical coords

# Touch hold state — separate from _taps because gameplay needs to track
# WHERE the finger currently is, not just where it tapped down. This is
# the difference between "press to fire" (a one-frame event) and "drag
# to position the jet" (continuous state). See touch_held() / touch_pos().
_touch_held    = False    # True from MOUSEBUTTONDOWN until MOUSEBUTTONUP
_touch_pos     = (0, 0)   # last known finger position in LOGICAL coords

# Swipe detection — used by the fighter select screen to cycle fighters.
# A swipe is a MOUSEBUTTONDOWN followed by MOUSEBUTTONUP where the finger
# moved more than SWIPE_THRESHOLD pixels horizontally.
# 'left' = finger moved left, 'right' = finger moved right, None = no swipe.
# Taps and swipes are mutually exclusive: if a swipe is detected, no tap
# is registered for that touch event (and vice versa).
_touch_start_x  = 0       # x position when the finger went down
_swipe          = None     # 'left', 'right', or None — valid for ONE frame
SWIPE_THRESHOLD = 50       # minimum horizontal pixels to count as a swipe


# ============================================================
# SETUP
# ============================================================

def init():
    """Start the joystick subsystem and grab the first gamepad found.

    Call once after pygame.init() and before the game loop starts.
    """
    global _joystick
    pygame.joystick.init()
    if pygame.joystick.get_count() > 0:
        _joystick = pygame.joystick.Joystick(0)
        _joystick.init()
        print(f"Controller connected: {_joystick.get_name()}")
    else:
        _joystick = None
        print("No controller — keyboard / touch only")


# ============================================================
# PER-FRAME UPDATE
# ============================================================

def update(events):
    """Refresh input state for this frame.

    Pass in the list returned by pygame.event.get(). The function
    pulls tap events out of it, then polls keyboard and gamepad
    state to figure out which actions are pressed.
    """
    global _pressed, _pressed_last, _taps, _touch_held, _touch_pos
    global _touch_start_x, _swipe

    # Edge-detection: remember what was pressed last frame so we can
    # detect 'just_pressed' (now pressed, wasn't before).
    _pressed_last = _pressed
    _pressed = set()
    _taps  = []
    _swipe = None     # swipe is a one-frame event, reset every frame

    # ---- Process raw input events ----
    # pygame reports finger taps on a touchscreen as MOUSEBUTTONDOWN /
    # MOUSEMOTION / MOUSEBUTTONUP events by default — the same code
    # handles a desktop mouse and a finger.
    for ev in events:
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            lx, ly = display.to_logical(ev.pos[0], ev.pos[1])
            _touch_held    = True       # finger is now down
            _touch_pos     = (lx, ly)
            _touch_start_x = lx        # remember where the swipe started

        elif ev.type == pygame.MOUSEMOTION and _touch_held:
            lx, ly = display.to_logical(ev.pos[0], ev.pos[1])
            _touch_pos = (lx, ly)       # finger dragged to a new spot

        elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
            lx, ly = display.to_logical(ev.pos[0], ev.pos[1])
            _touch_held = False
            dx = lx - _touch_start_x
            if abs(dx) >= SWIPE_THRESHOLD:
                # Large horizontal movement — treat as a swipe, not a tap.
                # 'left'  = finger moved left  (dx negative)
                # 'right' = finger moved right (dx positive)
                _swipe = 'left' if dx < 0 else 'right'
            else:
                # Small movement — treat as a tap at the original press point.
                _taps.append((_touch_start_x, _touch_pos[1]))

    # ---- Check every binding against the live input state ----
    keys = pygame.key.get_pressed()
    for action, sources in BINDINGS.items():
        for kind, payload in sources:
            if _check_source(kind, payload, keys):
                _pressed.add(action)
                break   # one source firing is enough — next action


def _check_source(kind, payload, keys):
    """Return True if this specific source is currently triggered."""

    if kind == 'key':
        return bool(keys[payload])

    if kind == 'button':
        if _joystick and payload < _joystick.get_numbuttons():
            return bool(_joystick.get_button(payload))
        return False

    if kind == 'hat':
        # D-pad. The hat returns a tuple like (1, 0) for right or
        # (0, -1) for down. We compare against the wanted direction;
        # a 0 in the wanted tuple means "don't care about this axis".
        if _joystick and _joystick.get_numhats() > 0:
            hat = _joystick.get_hat(0)
            want_x, want_y = payload
            if want_x != 0 and hat[0] != want_x:
                return False
            if want_y != 0 and hat[1] != want_y:
                return False
            return True
        return False

    if kind == 'axis':
        # Analog stick. payload is (axis_index, direction_sign).
        if _joystick:
            idx, direction = payload
            if idx < _joystick.get_numaxes():
                val = _joystick.get_axis(idx)
                if direction > 0:
                    return val > AXIS_DEADZONE
                else:
                    return val < -AXIS_DEADZONE
        return False

    if kind == 'touch':
        # payload is a pygame.Rect in LOGICAL coords. Check if any
        # of this frame's taps fell inside it.
        rect = payload
        for (tx, ty) in _taps:
            if rect.collidepoint(tx, ty):
                return True
        return False

    return False


# ============================================================
# QUERY API — what the game asks
# ============================================================

def is_pressed(action):
    """Is the action held this frame?
    Use for continuous things like 'move up while held'."""
    return action in _pressed


def just_pressed(action):
    """Was the action newly pressed THIS frame?

    Use for menu navigation, single fire, anything that should
    happen exactly once per press.
    """
    return action in _pressed and action not in _pressed_last


def just_released(action):
    """Was the action released this frame? Rarely needed but here."""
    return action in _pressed_last and action not in _pressed


def get_taps():
    """All tap positions (in logical coords) from this frame.

    Useful for ad-hoc touch zones that aren't bound to a named action
    — for example, 'tap anywhere to skip the boss intro'.
    """
    return list(_taps)


def touch_held():
    """True if a finger is currently held down on the screen.

    A 'tap' (down + up in the same frame burst) is registered through
    get_taps() and just_pressed() bindings. A 'hold' — finger pressed
    and not yet lifted — is what this function detects. Use this for
    drag-to-control gameplay.
    """
    return _touch_held


def touch_pos():
    """Last known finger position in logical coords (x, y).

    Returns the last reported position, even after the finger has been
    lifted — so callers should check touch_held() first if they only
    care about the LIVE position.
    """
    return _touch_pos


def get_swipe():
    """Return the swipe direction this frame, or None if no swipe occurred.

    Returns 'left' if the finger moved left, 'right' if it moved right.
    A swipe and a tap are mutually exclusive — if a swipe is detected,
    get_taps() will NOT include that touch event (and vice versa).

    Useful for carousel-style navigation (e.g. the fighter select screen).
    """
    return _swipe


def has_gamepad():
    """True if a gamepad was detected at init() time."""
    return _joystick is not None