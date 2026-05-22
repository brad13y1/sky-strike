"""
levels/fighters.py
===================
The player fighter roster. Same data-driven pattern as the levels list.

Each fighter is a dict. FIGHTERS is the ordered list. selected_index
tracks which one the player chose on the fighter select screen.

TO ADD A NEW FIGHTER:
  1. Drop the sprite PNG in assets/sprites/.
  2. Add a new dict to FIGHTERS below.
  3. That is it — the select screen handles any number of fighters.

FIGHTER DICT KEYS:
    name             display name (shown large on select screen)
    tagline          one-line description of the playstyle
    sprite           relative path under assets/ (e.g. "sprites/jet.png")
    needs_flip       True if the sprite faces left and must be flipped
    size             (width, height) to scale the sprite to in-game size
    hp               starting hit points for this fighter
    speed            pixels per frame the player jet can move
    weapon           key into systems/weapons.WEAPONS
    fire_rate        frames between shots — lower number = shoots faster
    bullet_damage    hit points removed per body hit
    bullet_speed     pixels per frame the bullet travels
    bullet_size      outer radius of the bullet in pixels
    bullet_color_out outer circle color (R, G, B)
    bullet_color_in  inner circle color (R, G, B)
"""


FIGHTERS = [
    {
        # ---- WAR-HOG ----
        # The flying tank. Inspired by the A-10 Thunderbolt II —
        # heavy armor, punishing cannon, but you are not winning any
        # foot races. High HP means you can take hits. High bullet
        # damage means every shot hurts. Slow speed means you WILL
        # get hit. Pick this if you like to brawl.
        "name":             "WAR-HOG",
        "tagline":          "Flying tank. Slow but devastating.",
        "sprite":           "sprites/jet.png",
        "needs_flip":       True,
        "size":             (140, 70),
        "hp":               9,
        "speed":            2,
        "weapon":           "machine_gun",
        "fire_rate":        14,        # fast firing — heavy gatling feel
        "bullet_damage":    2,        # each round hits hard
        "bullet_speed":     14,
        "bullet_size":      9,        # big chunky rounds
        "bullet_color_out": (220, 100,  20),   # orange — depleted uranium feel
        "bullet_color_in":  (200,  30,  30),   # red core
    },
    {
        # ---- FALCON ----
        # The all-rounder. Balanced stats across the board — the
        # right choice if you are learning the game. Neither the
        # fastest nor the toughest, but never feels wrong.
        "name":             "FALCON",
        "tagline":          "Balanced fighter. Good all-rounder.",
        "sprite":           "sprites/jet1.png",
        "needs_flip":       True,
        "size":             (135, 65),
        "hp":               7,
        "speed":            5,
        "weapon":           "machine_gun",
        "fire_rate":        10,       # standard rate of fire
        "bullet_damage":    1,
        "bullet_speed":     9,
        "bullet_size":      6,
        "bullet_color_out": ( 60, 220, 255),   # cyan — classic shmup bullet
        "bullet_color_in":  (255, 255, 255),   # white core
    },
    {
        # ---- Angry Duck ----
        # The glass cannon. Extremely fast — dodge everything or die.
        # Very fast fire rate means a constant stream of bullets, but
        # low HP means one bad stretch ends your run. High skill ceiling.
        "name":             "Angry Duck",
        "tagline":          "Glass cannon. Fast, fragile, furious.",
        "sprite":           "sprites/duck.png",
        "needs_flip":       True,    # duck.png faces left, needs flip
        "size":             (130, 60),
        "hp":               3,
        "speed":            8,
        "weapon":           "machine_gun",
        "fire_rate":        6,        # very fast — streams bullets
        "bullet_damage":    0.75,
        "bullet_speed":     18,       # fastest bullets on screen
        "bullet_size":      4,        # small hot rounds
        "bullet_color_out": (255, 230,   0),   # yellow — superheated
        "bullet_color_in":  (255, 255, 255),   # white core
    },
]


# Which fighter is currently selected. Written by fighter_select.py,
# read by loader.py when building the player state bundle.
selected_index = 0


def get_selected():
    """Return the currently selected fighter dict."""
    return FIGHTERS[selected_index]