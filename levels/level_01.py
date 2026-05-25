"""
Level 1 — the introduction.

A normal enemy under a plain blue sky. Easy stats so the player can
get a feel for the controls before the difficulty ramps up.
"""

from systems.backgrounds import image_bg
from systems.movement   import move_sine

LEVEL = {
    "enemy_hp":           30,
    "enemy_fire_rate":    80,
    "enemy_bullet_speed": 7,
    "enemy_damage":       1,
    "enemy_image":        "sprites/enemy1.png",
    "needs_flip": 		  False,
    "enemy_size":         (130, 60),
    "background":         image_bg("backgrounds/fuji_bg.png"),
    "player_hp":          3,
    "movement":           move_sine,
    "hit_body":           55,
    "hit_cockpit":        None,
    "hit_cockpit_damage": 0,
    "boss_name":          None,
    "music":              "s-gothic.ogg",
    "show_clouds":        False,
}