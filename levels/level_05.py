"""
Level 5 — first all AI generated Art.

This level AI generated PNG as the background instead of a
procedural sky fill.

When the kid wants to swap backgrounds for future levels, this is
the template: import image_bg, point it at the PNG, set
show_clouds based on whether the art is a sky scene or something
else (jungle / lava / space / etc.).

ASSET REQUIRED:
    assets/backgrounds/level_05_bg.png

    Any image; image_bg() will scale it to 1024x600 automatically.
    Use 1024x600 source art if you can, to avoid distortion.
"""

from systems.backgrounds import image_bg
from systems.movement   import move_random_target


LEVEL = {
    "enemy_hp":           40,
    "enemy_fire_rate":    45,
    "enemy_bullet_speed": 9,
    "enemy_damage":       4,
    "enemy_image":        "sprites/enemy5.png",
    "enemy_size":         (180, 90),
    "background":         image_bg("backgrounds/level_05_bg.png"),
    "player_hp":          7,
    "movement":           move_random_target,
    "hit_body":           55,
    "hit_cockpit":        None,
    "hit_cockpit_damage": 0,
    "boss_name":          "AI-GEN-1",
    "show_clouds":        False,    
}