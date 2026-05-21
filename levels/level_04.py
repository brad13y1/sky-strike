"""
Level 4 — first all-art level.

This level uses a kid-drawn PNG as the background instead of a
procedural sky fill. The player jet and enemy are the existing
sprites; only the backdrop changes.

When the kid wants to swap backgrounds for future levels, this is
the template: import image_bg, point it at the PNG, set
show_clouds based on whether the art is a sky scene or something
else (jungle / lava / space / etc.).

ASSET REQUIRED:
    assets/backgrounds/level_04_bg.png

    Any image; image_bg() will scale it to 1024x600 automatically.
    Use 1024x600 source art if you can, to avoid distortion.
"""

from systems.backgrounds import image_bg
from systems.movement   import move_sine


LEVEL = {
    "enemy_hp":           50,
    "enemy_fire_rate":    65,
    "enemy_bullet_speed": 8,
    "enemy_damage":       2,
    "enemy_image":        "sprites/enemy1.png",
    "enemy_size":         (130, 60),
    "background":         image_bg("backgrounds/level_04_bg.png"),
    "player_hp":          7,
    "movement":           move_sine,
    "hit_body":           55,
    "hit_cockpit":        None,
    "hit_cockpit_damage": 0,
    "boss_name":          None,
    "show_clouds":        False,    # kid's BG is the whole scene — no procedural clouds
}