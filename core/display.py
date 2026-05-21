"""
core/display.py
================
Scale-to-fit display layer.

THE PROBLEM:
  The game was designed for a 1024x600 screen (the Pi 4B 7" touchscreen).
  But friends will play on laptops (maybe 1920x1080) or on a 65" TV
  (also 1920x1080). If we just called pygame.display.set_mode((win_w,
  win_h)) and drew with coordinates like player.x = 140, the player
  would end up in a tiny corner of a giant screen.

THE FIX:
  We always draw the game onto a fixed 1024x600 surface called the
  "logical surface". Then, at the end of every frame, we take that
  surface and stretch it up (or shrink it down) to fit the actual
  window, keeping the aspect ratio. Any leftover space becomes
  black bars (letterbox top/bottom or pillarbox left/right).

  Game code never has to know the real window size. It just draws
  on a 1024x600 canvas. ONE set of coordinates, every device.

USAGE:
    # Once, at startup:
    logical = display.init_display(fullscreen=False)

    # In the game loop, draw on `logical`, NOT on a window directly:
    logical.fill(SKY)
    pygame.draw.circle(logical, RED, (200, 300), 20)
    # ... etc.

    # At the end of each frame:
    display.present()

    # When mouse/touch happens, convert screen coords to logical:
    lx, ly = display.to_logical(event.pos[0], event.pos[1])
"""

import pygame
from core.constants import WIDTH, HEIGHT, TITLE


# ============================================================
# MODULE STATE
# ============================================================
# Underscore prefix is a Python convention meaning "internal" —
# game code shouldn't touch these directly. Use the functions below.

_window    = None    # the real OS window
_logical   = None    # the 1024x600 canvas the game draws on
_scale     = 1.0     # how much we stretch logical -> window
_offset_x  = 0       # left bar width  (pillarbox, if any)
_offset_y  = 0       # top bar height  (letterbox, if any)


def init_display(fullscreen=False):
    """Create the OS window AND the logical drawing surface.

    Returns the logical surface — the thing game code should draw on.
    """
    global _window, _logical

    pygame.display.set_caption(TITLE)

    if fullscreen:
        # (0, 0) tells pygame to match the desktop's native resolution.
        _window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else:
        # Default windowed size matches the logical resolution.
        # The window is RESIZABLE so the player can stretch it —
        # handle_resize() takes care of recomputing the scale.
        _window = pygame.display.set_mode(
            (WIDTH, HEIGHT), pygame.RESIZABLE)

    _logical = pygame.Surface((WIDTH, HEIGHT))
    _recompute_scale()
    return _logical


def handle_resize(new_size):
    """Recreate the window at the new size and recompute scaling.

    Call this from the event loop whenever pygame.VIDEORESIZE fires.
    """
    global _window
    _window = pygame.display.set_mode(new_size, pygame.RESIZABLE)
    _recompute_scale()


def _recompute_scale():
    """Work out the scale factor and the letterbox/pillarbox offsets
    for the current window size."""
    global _scale, _offset_x, _offset_y

    win_w, win_h = _window.get_size()
    # We want the WHOLE logical surface to fit inside the window,
    # so use the smaller of the two scale factors.
    scale_w = win_w / WIDTH
    scale_h = win_h / HEIGHT
    _scale = min(scale_w, scale_h)

    # Center the scaled image — whatever's left over becomes bars.
    scaled_w = WIDTH  * _scale
    scaled_h = HEIGHT * _scale
    _offset_x = (win_w - scaled_w) / 2
    _offset_y = (win_h - scaled_h) / 2


def present():
    """Scale the logical surface to fit the window, then flip the display.

    Call once per frame, AFTER all drawing is done.
    """
    # Fill the whole window black first — the bars (if any) become
    # pure black this way.
    _window.fill((0, 0, 0))

    # Stretch the logical surface up to its display size.
    scaled = pygame.transform.scale(
        _logical,
        (int(WIDTH * _scale), int(HEIGHT * _scale))
    )
    _window.blit(scaled, (_offset_x, _offset_y))
    pygame.display.flip()


def to_logical(screen_x, screen_y):
    """Convert a mouse/touch position from window coords to logical coords.

    A tap that lands on a black bar will return a value OUTSIDE the
    [0, WIDTH] x [0, HEIGHT] range. Callers should usually ignore those.
    """
    if _scale == 0:
        return (0, 0)
    lx = (screen_x - _offset_x) / _scale
    ly = (screen_y - _offset_y) / _scale
    return (lx, ly)


def get_logical_surface():
    """Return the surface game code should draw on.

    Mostly useful if a module needs it after init() time.
    """
    return _logical


def setup_browser_canvas():
    """When running in a browser via pygbag, stretch the HTML canvas
    to fill the browser window while preserving aspect ratio.

    On DESKTOP (regular Python), this is a no-op. The resizable
    pygame window handles scaling via VIDEORESIZE events, which is
    what _recompute_scale() above takes care of.

    On the BROWSER (sys.platform == "emscripten"), there is no
    pygame window to resize — the game renders into an HTML
    <canvas> element on the page. Pygbag's default template wraps
    the canvas in a parent container sized to the game's native
    1024x600, which constrains it even if we set the canvas's CSS
    directly.

    The workaround: inject a <style> element into the document
    <head> with !important rules and position:fixed on the canvas.
    position:fixed removes the canvas from normal document flow,
    so the parent container's size can't constrain it — the canvas
    is positioned relative to the viewport instead. object-fit:
    contain preserves the 1024:600 aspect inside that viewport-
    sized box (black letterbox bars on whichever sides are leftover).

    Resize handling is automatic: 100vw and 100vh are viewport-
    relative CSS units, so the canvas re-scales the moment the
    browser window changes size. No JavaScript resize listener
    needed.
    """
    import sys
    if sys.platform != "emscripten":
        return     # desktop / Pi — nothing to do

    # On WASM, the stdlib `platform` module is replaced by pygbag's
    # JS bridge. Local import so desktop never touches it.
    import platform as browser

    # Inject a <style> element into <head>. !important defeats any
    # rules pygbag's template put in place.
    style = browser.document.createElement("style")
    style.textContent = """
        html, body {
            margin: 0 !important;
            padding: 0 !important;
            width: 100% !important;
            height: 100% !important;
            overflow: hidden !important;
            background: #000 !important;
        }
        canvas {
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            width: 100vw !important;
            height: 100vh !important;
            object-fit: contain !important;
            image-rendering: pixelated;
            touch-action: none;
            background: #000;
        }
    """
    browser.document.head.appendChild(style)