"""
core/fonts.py
==============
The three fonts the whole game uses, loaded once at startup.

WHY a separate file:
  Every drawing function and every menu screen renders text. If we
  loaded fonts inside whoever needed them, the same font would get
  loaded over and over. Loading them once here and letting everyone
  read `fonts.small`, `fonts.med`, `fonts.big` is faster and tidier.

WHY init() instead of loading at the top:
  pygame.font.SysFont() doesn't work until pygame.init() has been
  called. main.py calls pygame.init() first, then fonts.init().

LATER (before PyInstaller .exe):
  We'll switch from SysFont to a bundled TTF file in
  assets/fonts/freesansbold.ttf — pygame's default and system fonts
  don't survive PyInstaller bundling reliably.
"""

import pygame


# ---------- Module state ----------
# Public, but starts as None until init() is called.
small = None
med   = None
big   = None


def init():
    """Load the three fonts. Call once, after pygame.init()."""
    global small, med, big
    small = pygame.font.SysFont("Courier", 22, bold=True)
    med   = pygame.font.SysFont("Courier", 30, bold=True)
    big   = pygame.font.SysFont("Courier", 64, bold=True)