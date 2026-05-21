"""
scenes/ — the screens the player sees.

Each scene is a self-contained module exporting three functions:

    init()           Set up scene state. Called once when entering the
                     scene from somewhere else.

    update(events)   Run one frame of logic. Returns one of:
                       - "title"     transition to title scene
                       - "gameplay"  transition to gameplay scene
                       - "QUIT"      exit the program
                       - None        stay in this scene

    draw(surf)       Render the scene to the given (logical) surface.

main.py's job is to dispatch update/draw to whichever scene is active
and handle the transitions that scenes request.

Scenes import FROM core/, systems/, and levels/. Nothing should ever
import FROM scenes.
"""