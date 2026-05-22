"""
Level 2 — the difficulty bump.

Same enemy sprite as Level 1 but under a sunset sky and with harder
stats: double the HP, faster fire rate, faster + more dangerous
bullets. The player also gets one extra HP to compensate.
"""

from systems.backgrounds import fill_sunset
from systems.movement   import move_retreat


LEVEL = {
    "enemy_hp":           40,
    "enemy_fire_rate":    70,
    "enemy_bullet_speed": 8,
    "enemy_damage":       2,
    "enemy_image":        "sprites/enemy1.png",
    "enemy_size":         (130, 60),
    "background":         fill_sunset,
    "player_hp":          6,
    "movement":           move_retreat,
    "hit_body":           55,
    "hit_cockpit":        None,
    "hit_cockpit_damage": 0,
    "boss_name":          None,
    "show_clouds":        True,
}