"""
Level 5 — Lazy Panda boss, drinking bubble-tea .

This level is backyard PNG as the background instead of a
procedural sky fill.

When the kid wants to swap backgrounds for future levels, this is
the template: import image_bg, point it at the PNG, set
show_clouds based on whether the art is a sky scene or something
else (jungle / lava / space / etc.).

ASSET REQUIRED:
    assets/backgrounds/yard.png

    Any image; image_bg() will scale it to 1024x600 automatically.
    Use 1024x600 source art if you can, to avoid distortion.
"""

from systems.backgrounds import image_bg
from systems.movement   import move_figure_eight


LEVEL = {
    "enemy_hp":           45,
    "enemy_fire_rate":    45,
    "enemy_bullet_speed": 9,
    "enemy_damage":       4,
    "enemy_image":        "sprites/panda.png",
    "needs_flip": 		  False,
    "enemy_size":         (180, 90),
    "background":         image_bg("backgrounds/yard.png"),
    "player_hp":          7,
    "movement":           move_figure_eight,
    "hit_body":           55,
    "hit_cockpit":        None,
    "hit_cockpit_damage": 0,
    "boss_name":          "LAZY PANDA",
    "show_clouds":        False,    
}