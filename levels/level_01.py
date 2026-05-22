"""
Level 1 — the introduction.

A normal enemy under a plain blue sky. Easy stats so the player can
get a feel for the controls before the difficulty ramps up.
"""

from systems.backgrounds import fill_solid_sky
from systems.movement   import move_sine


LEVEL = {
    "enemy_hp":           30,
    "enemy_fire_rate":    80,
    "enemy_bullet_speed": 7,
    "enemy_damage":       1,
    "enemy_image":        "sprites/enemy1.png",
    "enemy_size":         (130, 60),
    "background":         fill_solid_sky,
    "player_hp":          3,
    "movement":           move_sine,
    "hit_body":           55,
    "hit_cockpit":        None,
    "hit_cockpit_damage": 0,
    "boss_name":          None,
    "show_clouds":        True,
}