"""
SKY STRIKE — main.py
======================
Entry point and scene router.

The game is built as a set of SCENES (see scenes/). Each scene is
a module exporting:

    init()           prepare scene state
    update(events)   one frame of logic; returns a transition name or None
    draw(surf)       render to the logical surface

This file's job is small:

    1. Initialize pygame, display, input, fonts.
    2. Start at the title scene.
    3. Run the async game loop forever:
         - Pump events; honor QUIT and window resize.
         - Update input.
         - Let the current scene run one frame.
         - If the scene asked for a transition, switch scenes.
         - Draw the scene.
         - Scale to window and flip.
         - Yield to the browser (pygbag).

DESKTOP:   cd Sky_Strike  ->  python main.py
BROWSER:   cd <parent>    ->  pygbag Sky_Strike
            (opens at http://localhost:8000)

NOTHING goes after asyncio.run(main()) — pygbag's WASM build runs
this non-blocking and would never execute code below it.
"""

import asyncio
import pygame

from core import constants, display, fonts
from systems import audio
from core import input as input_mod
from scenes import title, gameplay, fighter_select


# ---- Module state ----
current_scene = None
clock         = None
logical       = None


def _transition(name):
    """Switch to the named scene and call its init()."""
    global current_scene
    if name == "title":
        title.init()
        current_scene = title
    elif name == "fighter_select":
        fighter_select.init()
        current_scene = fighter_select
    elif name == "gameplay":
        gameplay.init()
        current_scene = gameplay


async def main():
    """The pygbag-compatible game loop."""
    global current_scene, clock, logical

    # ---------- Pygame + foundation init ----------
    pygame.init()
    logical = display.init_display(fullscreen=False)
    display.setup_browser_canvas()    # no-op on desktop; stretches canvas in browser
    input_mod.init()
    fonts.init()
    audio.init()

    # ---------- Start at the title screen ----------
    _transition("title")

    clock = pygame.time.Clock()
    running = True

    # ============================================================
    # MAIN LOOP
    # ============================================================
    while running:

        # ---------- 1. Collect events ----------
        events = pygame.event.get()
        for ev in events:
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.VIDEORESIZE:
                display.handle_resize(ev.size)

        # ---------- 2. Update input ----------
        input_mod.update(events)

        # ---------- 3. Run the active scene ----------
        result = current_scene.update(events)
        if result == "QUIT":
            running = False
        elif result is not None:
            _transition(result)

        # ---------- 4. Draw ----------
        current_scene.draw(logical)

        # ---------- 5. Present (scale + flip) ----------
        display.present()

        clock.tick(constants.FPS)

        # ---------- 6. Yield to the browser (required for pygbag) ----------
        await asyncio.sleep(0)

    pygame.quit()


# ---------- Entry point ----------
asyncio.run(main())