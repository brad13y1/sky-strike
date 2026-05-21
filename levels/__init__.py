"""
levels/ — one file per level.

To add a new level (say, level 4):
  1. Create levels/level_04.py with a single dict named LEVEL.
  2. Import it here and add it to the LEVELS list below.

The order in LEVELS is the order the player plays them in. The
index matters: levels/loader.py looks up LEVELS[idx] to get the
config for the level that's loading.

Adding a level requires:
  - a new file in this folder
  - one import line and one list entry in __init__.py

Nothing else changes. That's the whole point of the data-driven
levels architecture.
"""

from levels.level_01 import LEVEL as level_01
from levels.level_02 import LEVEL as level_02
from levels.level_03 import LEVEL as level_03
from levels.level_04 import LEVEL as level_04
from levels.level_05 import LEVEL as level_05


LEVELS = [
    level_01,
    level_02,
    level_03,
    level_04,
    level_05,
]