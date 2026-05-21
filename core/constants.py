"""
core/constants.py
==================
All the values that don't change while the game runs — screen size,
frame rate, colors, the title. Everyone else imports from here.

This file imports NOTHING else from the project. That's on purpose:
it's the bottom of the dependency stack, so it can never cause a
circular-import problem.

WHY a separate file:
  Before the refactor, these constants lived at the top of
  sky_strike.py and everything else inherited them by being in the
  same file. Now that the code is split into many files, every file
  needs a way to ask "what's the screen width?" — and they all ask
  this file.
"""

# ============================================================
# LOGICAL RESOLUTION
# ============================================================
# The game ALWAYS draws to a surface this size, no matter what
# screen it ends up on. core/display.py handles scaling this up to
# whatever the player's window or TV actually is.
#
# 1024x600 is the native size of the Pi 4B 7" touchscreen — the
# screen the game was originally designed for.

WIDTH  = 1024
HEIGHT = 600
FPS    = 60


# ============================================================
# WINDOW / VERSION
# ============================================================

TITLE   = "Sky Strike"
VERSION = "0.1.0-foundation"


# ============================================================
# COLORS
# ============================================================
# Each color is (R, G, B) — three numbers from 0 to 255.
# Same colors as the original sky_strike.py.

SKY        = (90, 170, 240)
WHITE      = (255, 255, 255)
BLACK      = (0,   0,   0)
GRAY       = (140, 140, 150)
DARK_GRAY  = (70,  70,  80)
RED        = (220, 40,  40)
DARK_RED   = (140, 20,  20)
ORANGE     = (255, 140, 0)
YELLOW     = (255, 230, 0)
CYAN       = (60,  220, 255)
GREEN      = (60,  200, 90)