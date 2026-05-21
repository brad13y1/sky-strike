"""
systems/ — reusable game-logic pieces.

Each system is a self-contained module the gameplay scene calls into.
They own their own data when they have any (explosion list, cloud
list, ...) and expose simple functions.

- movement.py     enemy AI movement patterns
- backgrounds.py  sky fills + clouds + stars (data + draw + update)
- drawing.py      player / enemy / HUD rendering
- effects.py      explosions + crit popups (data + draw + update)
- audio.py        (added in a later pass — sounds, music)

Systems import FROM core/, but NOT from scenes/ or levels/. The
dependency direction is one-way.
"""