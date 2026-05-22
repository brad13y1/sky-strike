"""
levels/loader.py
=================
Reads a level config from LEVELS and produces a fresh state bundle.

WHY THIS EXISTS:
  The gameplay scene doesn't want to know the format of a level dict —
  it just wants to say "load level 2" and get back the player, the
  enemy, the background function, the movement function, and the
  enemy image, all set up and ready to use.

WHY load_level RETURNS A DICT INSTEAD OF MUTATING GLOBALS:
  The old sky_strike.py used `global enemy_img, current_bg, ...`
  to poke values back into the main file. That works but it's
  hidden — looking at load_level() you couldn't tell what it
  affected.

  The new design RETURNS everything in a single bundle. The caller
  (gameplay scene) decides what to do with it. No hidden globals,
  no surprises.
"""

import pygame

from core.constants import WIDTH, HEIGHT
from core.paths import asset_path
from levels import LEVELS
from levels.fighters import get_selected


def load_level(idx):
    """Build and return a complete bundle for level `idx`.

    Returns a dict with these keys:
        player          fresh player dict with this level's HP / position
        enemy           fresh enemy dict with this level's stats
        background      function(surf) that fills the sky
        movement        function(enemy, player) that updates the enemy each frame
        enemy_img       loaded + scaled pygame.Surface for the enemy
        has_boss_intro  True if this level should show the boss intro
        show_clouds     True if procedural clouds should be drawn
    """
    cfg     = LEVELS[idx]
    fighter = get_selected()

    # ---- Player state ----
    # HP and speed come from the selected fighter, not the level config.
    # (Level dicts still have a "player_hp" key but it is no longer used —
    # left in place so nothing breaks if old level files are kept as-is.)
    player = {
        "x":        140,
        "y":        HEIGHT // 2,
        "hp":       fighter["hp"],
        "max_hp":   fighter["hp"],
        "cooldown": 0,
        "speed":    fighter["speed"],
    }

    # ---- Enemy state ----
    enemy = {
        "x":                  WIDTH - 200,
        "y":                  HEIGHT // 2,
        "hp":                 cfg["enemy_hp"],
        "max_hp":             cfg["enemy_hp"],
        "cooldown":           80,          # delay before the enemy's first shot
        "phase":              0.0,         # used by move_sine / move_figure_eight / move_circle
        "fire_rate":          cfg["enemy_fire_rate"],
        "bullet_speed":       cfg["enemy_bullet_speed"],
        "damage":             cfg["enemy_damage"],
        "hit_body":           cfg["hit_body"],
        "hit_cockpit":        cfg["hit_cockpit"],
        "hit_cockpit_damage": cfg["hit_cockpit_damage"],
        "boss_name":          cfg["boss_name"],
        # Used by move_random_target. Harmless if the level uses a different pattern.
        "target_x":           WIDTH - 200,
        "target_y":           HEIGHT // 2,
        "pause_frames":       0,
        # Used by new movement patterns. Harmless if not used by this level.
        "zigzag_dir":         1,           # move_zigzag  — bounce direction (+1 or -1)
        "center_x":           WIDTH - 200, # move_circle / move_figure_eight — orbit centre
        "center_y":           HEIGHT // 2, # move_circle / move_figure_eight — orbit centre
        "orbit_radius":       150,         # move_circle  — orbit radius in px
        "retreat_threshold":  350,         # move_retreat — distance that triggers flee/advance
    }

    # ---- Enemy sprite ----
    # asset_path() handles dev mode, PyInstaller, and pygbag automatically.
    img = pygame.image.load(asset_path(cfg["enemy_image"])).convert_alpha()
    img = pygame.transform.scale(img, cfg["enemy_size"])

    return {
        "player":         player,
        "enemy":          enemy,
        "background":     cfg["background"],
        "movement":       cfg["movement"],
        "enemy_img":      img,
        "has_boss_intro": cfg["boss_name"] is not None,
        # Default to True if missing so older levels keep working.
        "show_clouds":    cfg.get("show_clouds", True),
    }


def level_count():
    """How many levels exist. Used by 'is there a next level?' checks."""
    return len(LEVELS)