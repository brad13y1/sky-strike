"""
core/paths.py
==============
Asset path resolver. The same code has to find files in THREE
different worlds, and each world keeps the files in a different place:

  1. DEV MODE
     You run `python main.py` from the Sky_Strike folder.
     Assets live at:  Sky_Strike/assets/...

  2. PYINSTALLER (.exe)
     When packaged into a Windows .exe, PyInstaller unpacks everything
     into a random temporary folder at runtime. The path to that
     folder is stored in sys._MEIPASS.

  3. PYGBAG (browser)
     The game runs as WebAssembly inside the browser. The "current
     folder" is the project folder — same as dev mode.

This file gives us ONE function — asset_path() — that returns the
correct full path no matter which world we're in. Game code never
has to think about it.

USAGE:
    from core.paths import asset_path

    jet_img = pygame.image.load(asset_path("sprites/jet.png"))
    boom   = pygame.mixer.Sound(asset_path("sounds/explosion.ogg"))

ALWAYS use forward slashes inside the relative path. pygbag/browser
is strict about it; Windows is forgiving but the rule keeps us
portable.
"""

import os
import sys


def _project_root():
    """Return the folder that contains main.py and the assets/ folder."""

    # Case 1: running inside a PyInstaller-built .exe.
    # PyInstaller adds sys._MEIPASS when it extracts the bundle to
    # a temp directory. If we see it, that's our root.
    if hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS

    # Case 2 & 3 (dev mode and pygbag/browser):
    # This file lives at <project_root>/core/paths.py. Go up two
    # levels from the file's own location:
    #   __file__       -> .../Sky_Strike/core/paths.py
    #   dirname        -> .../Sky_Strike/core
    #   dirname again  -> .../Sky_Strike
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def asset_path(relative):
    """Build the full path to a file inside the assets/ folder.

    Examples:
        asset_path("sprites/jet.png")
        asset_path("sounds/explosion.ogg")
        asset_path("fonts/freesansbold.ttf")
    """
    return os.path.join(_project_root(), "assets", relative)


def project_path(relative):
    """Like asset_path() but for files in the project root.

    Rarely needed. Most things should go through asset_path().
    """
    return os.path.join(_project_root(), relative)