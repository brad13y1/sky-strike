"""
scenes/title.py
================
The title screen — what the player sees when the game launches.

LAYOUT:
  - Black background
  - Kid's start.png drawing centered on screen
  - "SKY STRIKE" big text at the top
  - "Press A or SPACE to Start" near the bottom
  - Small gray quit hint under that

CONTROLS:
  - 'confirm' (A button / RETURN) or 'fire' (A button / SPACE)
        -> transition to gameplay
  - 'pause' (ESC / START)
        -> quit the entire program

This is the ONLY scene that can quit the program. Every other scene
routes 'pause' back to title — title is the hub. This means the player
can always get out by hitting ESC twice (once to title, once to quit).
"""

import pygame

from core.constants import WIDTH, HEIGHT, BLACK, WHITE, GRAY, YELLOW
from core.paths import asset_path
from core import input as input_mod
from core import fonts
from systems import scores as scores_mod
from systems import audio


# ---- Module state ----
start_img = None    # the kid's drawing, loaded on first init()


def init():
    audio.play_music("title")
    """Load the title image. Safe to call repeatedly — the image is
    cached after the first load."""
    global start_img
    if start_img is None:
        start_img = pygame.image.load(
            asset_path("sprites/start.png")
        ).convert_alpha()
        # Scale to a reasonable on-screen size (matches the original game).
        # If the kid replaces start.png with a bigger drawing later, it
        # still ends up at this size — never huge, never tiny.
        start_img = pygame.transform.scale(start_img, (450, 300))


def update(events):
    """Returns a transition request or None to stay on title."""
    if input_mod.just_pressed('pause'):
        return "QUIT"
    if (input_mod.just_pressed('confirm')
        or input_mod.just_pressed('fire')
        or input_mod.get_taps()):
        return "fighter_select"
    return None


def draw(surf):
    surf.fill(BLACK)

    # Kid's drawing, centered
    rect = start_img.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    surf.blit(start_img, rect)

    # Game title, top of screen
    title = fonts.big.render("SKY STRIKE", True, WHITE)
    surf.blit(title, title.get_rect(center=(WIDTH // 2, 70)))

    # Start prompt, near bottom
    prompt = fonts.med.render("tap to start", True, WHITE)
    surf.blit(prompt, prompt.get_rect(center=(WIDTH // 2, HEIGHT - 50)))

    # High-score panel on the right side of the screen
    _draw_leaderboard(surf)


def _draw_leaderboard(surf):
    """Compact top-5 leaderboard shown on the right of the title screen."""
    board  = scores_mod.load()
    # Panel center-x sits in the gap between the image edge and the screen edge.
    # Image is 450px wide centered at 512 → right edge at 737.
    # Right gap: 737..1024 (287px) → panel center at ~880.
    panel_cx = 880
    y        = 155

    header = fonts.small.render("HIGH SCORES", True, YELLOW)
    surf.blit(header, header.get_rect(center=(panel_cx, y)))

    for i in range(5):
        if i < len(board):
            txt   = f"{i + 1}. {board[i]['name']:<3}  {board[i]['score']:>9,}"
            color = WHITE
        else:
            txt   = f"{i + 1}. ---"
            color = GRAY
        row = fonts.small.render(txt, True, color)
        surf.blit(row, row.get_rect(center=(panel_cx, y + 28 + i * 26)))