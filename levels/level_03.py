"""
Level 3 — MO-FORCE-1, the first boss.

A bigger sprite, unpredictable movement (random target points), much
faster firing, and a cockpit weak spot worth 2 damage per hit. The
boss intro plays when this level loads because boss_name is set.

This is the level that introduces:
  - Random-target movement (vs. predictable sine wave)
  - Cockpit / body hitbox split (CRIT zone)
  - Boss intro overlay
  - Persistent boss nameplate in the HUD
"""

from systems.backgrounds import fill_night_sky
from systems.movement   import move_random_target


LEVEL = {
    "enemy_hp":           40,
    "enemy_fire_rate":    45,
    "enemy_bullet_speed": 9,
    "enemy_damage":       4,
    "enemy_image":        "sprites/boss1.png",
    "enemy_size":         (180, 90),
    "background":         fill_night_sky,
    "player_hp":          7,
    "movement":           move_random_target,
    "hit_body":           60,
    "hit_cockpit":        20,
    "hit_cockpit_damage": 2,
    "boss_name":          "MO-FORCE-1",
    "show_clouds":        True,
}