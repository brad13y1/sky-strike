# Sky Strike — Advanced Quick Reference
### "Building New Stuff"

> You've mastered changing numbers. Now let's build new things from scratch — new movement patterns, new levels, and eventually new screens. This guide assumes you've read the Full Tutorial and the Beginner Reference.

---

## 🚀 Create a New Movement Pattern

Movement patterns live in `systems/movement.py`. Every pattern is a **function** — a named block of code that runs once per frame.

### The Template

Every movement pattern looks like this:

```python
def move_yourname(e, player):
    """One sentence describing what this pattern does."""
    # Your movement code goes here
    # e["x"] is the enemy's horizontal position
    # e["y"] is the enemy's vertical position
    # player["x"] and player["y"] are the player's position
```

- `e` = the enemy (you can read and change `e["x"]` and `e["y"]`)
- `player` = the player (you can READ `player["x"]` and `player["y"]` but don't change them here)

### The Screen Coordinates

The game screen is **1024 pixels wide** and **600 pixels tall**.

```
(0, 0) ────────────────────── (1024, 0)
  │                                 │
  │         YOUR SCREEN             │
  │                                 │
(0, 600) ──────────────────── (1024, 600)
```

- X increases going RIGHT
- Y increases going DOWN
- Enemy should stay roughly between x=700 and x=950
- Enemy should stay roughly between y=80 and y=520

### Example — A New Pattern: move_hover

This pattern makes the enemy hover around a fixed point:

```python
def move_hover(e, player):
    """Hover in a small circle, staying close to center."""
    e["phase"] += 0.04
    e["x"] = 820 + math.sin(e["phase"]) * 40
    e["y"] = 300 + math.cos(e["phase"]) * 80
```

`math.sin` and `math.cos` create smooth wave movements. Changing the numbers changes how big the movement is.

### How to Use Your New Pattern

**Step 1** — Write the function in `systems/movement.py` (add it at the bottom of the file)

**Step 2** — In your level file, import it:
```python
from systems.movement import move_hover
```

**Step 3** — Use it in the LEVEL dict:
```python
"movement": move_hover,
```

**Step 4** — Run the game and see what it looks like. Adjust the numbers until it feels right.

---

## 🚀 Add a New Level

Each level is one file in the `levels/` folder, plus one line in `levels/__init__.py`.

### Step 1 — Create the Level File

Create a new file called `level_06.py` in the `levels/` folder.

Copy this template and fill in your own values:

```python
"""
Level 6 — your description here.
"""

from systems.backgrounds import fill_solid_sky
from systems.movement   import move_zigzag


LEVEL = {
    "enemy_hp":           40,
    "enemy_fire_rate":    60,
    "enemy_bullet_speed": 9,
    "enemy_damage":       1,
    "enemy_image":        "sprites/enemy1.png",
    "enemy_size":         (130, 60),
    "background":         fill_solid_sky,
    "player_hp":          5,
    "movement":           move_zigzag,
    "hit_body":           55,
    "hit_cockpit":        None,
    "hit_cockpit_damage": 0,
    "boss_name":          None,
    "show_clouds":        True,
    "needs_flip":         False,
}
```

### Step 2 — Register the Level

Open `levels/__init__.py`. You'll see a list of levels. Add your new one at the end:

```python
from levels.level_06 import LEVEL as level_06

LEVELS = [
    level_01,
    level_02,
    level_03,
    level_04,
    level_05,
    level_06,    ← ADD THIS LINE
]
```

That's it. Run the game, beat Level 5, and Level 6 will appear.

### Tips for Good Level Progression

Make each level slightly harder than the last. A good formula:

| Level | enemy_hp | fire_rate | bullet_speed |
|---|---|---|---|
| Easy (1-2) | 15–25 | 80–100 | 6–8 |
| Medium (3-4) | 30–50 | 50–70 | 8–10 |
| Hard (5-6) | 50–80 | 35–55 | 9–12 |
| Boss levels | 100–150 | 25–40 | 10–14 |

---

## 🚀 Add a PNG Background to a Level

Instead of a solid color sky, you can use your own artwork as the background.

### Step 1 — Prepare Your Image

- Draw or create your background image
- Save it as a PNG file
- Put it in `assets/backgrounds/`
- Name it something like `level_06_bg.png`

Best size: **1024 × 600 pixels** (matches the game screen exactly)

### Step 2 — Update the Level File

At the top of your level file, change the import:

```python
from systems.backgrounds import image_bg
```

Then inside the LEVEL dict, change background to:

```python
"background": image_bg("backgrounds/level_06_bg.png"),
```

Also turn off clouds if your background already has them:

```python
"show_clouds": False,
```

---

## 🚀 Add a Boss to a Level

A boss level has:
- A boss name (triggers the flashing "APPROACHES" intro screen)
- Higher HP and fire rate
- A boss-appropriate movement pattern
- A boss sprite image

### Step 1 — Set the Boss Name

In your level file:
```python
"boss_name": "THUNDER-HAWK-1",
```

### Step 2 — Use a Boss Movement Pattern

Good boss patterns:
- `move_random_target` — unpredictable, classic boss feel
- `move_figure_eight` — hypnotic, looks impressive
- `move_circle` — orbiting, hard to track

### Step 3 — Set Boss Stats

```python
"enemy_hp":           120,
"enemy_fire_rate":    35,
"enemy_bullet_speed": 11,
"enemy_damage":       2,
```

### Step 4 — Use a Boss Sprite

Put your boss PNG in `assets/sprites/` and update:
```python
"enemy_image": "sprites/myboss.png",
"enemy_size":  (200, 100),
```

---

## 🚀 Add a Cockpit Weak Spot

Some enemies have a cockpit that does EXTRA damage when hit precisely. This rewards skilled shooting.

In the level file:
```python
"hit_cockpit":        25,   ← cockpit hit zone radius in pixels
"hit_cockpit_damage": 5,    ← how much damage a cockpit hit does
```

The cockpit hit zone is automatically placed slightly left of the enemy's center (where a cockpit would be on a jet facing left).

Leave both as `None` / `0` for enemies without a weak spot.

---

## 🚀 Understanding the Code — Decoding Real Lines

Here are some real lines from the game explained in plain English.

### From gameplay.py:

```python
if player["hp"] <= 0:
    state = "game_over"
```
**Plain English:** "If the player's health points are zero or less, switch to the game over screen."

---

```python
player["y"] = max(60, min(HEIGHT - 60, ty))
```
**Plain English:** "Set the player's Y position to where your finger is — but don't let it go higher than 60 pixels from the top, or lower than 60 pixels from the bottom."

`max()` picks the bigger of two numbers. `min()` picks the smaller. Together they create a clamp (a boundary the value can't escape).

---

```python
enemy["cooldown"] -= 1
if enemy["cooldown"] <= 0:
    # fire a bullet
    enemy["cooldown"] = enemy["fire_rate"]
```
**Plain English:** "Count down. When the countdown reaches zero, shoot a bullet and reset the countdown to the fire_rate value."

This is how ALL cooldowns work in the game — player shooting, enemy shooting. Count down, do the thing, reset.

---

### From movement.py:

```python
def move_sine(e, player):
    e["phase"] += 0.025
    e["y"] = HEIGHT // 2 + math.sin(e["phase"]) * 200
```
**Plain English:** "Each frame, advance the phase slightly. Set the enemy's Y position to the center of the screen plus a sine wave. The sine wave makes the value smoothly go up and down between -200 and +200 from center."

`HEIGHT // 2` = 300 (the middle of the 600px tall screen)
`math.sin()` = a wave that goes between -1 and 1
`* 200` = stretch that wave to go between -200 and 200

---

## 🚀 What to Learn Next

When you're ready to go even further, here are the next skills to explore (your dad can help set these up):

| Skill | What it unlocks |
|---|---|
| **Python lists** | Making levels with multiple enemies |
| **Python functions** | Writing your own helper tools |
| **Python classes** | Grouping data and behavior together (the next big leap) |
| **Pygame sprites** | More flexible way to handle game objects |
| **JSON files** | Saving and loading high scores |
| **GitHub** | Sharing your code and tracking changes (your dad uses this already) |

---

## 🚀 The Developer's Questions

Every time you add something new, ask yourself these questions:

1. **Does it run without errors?** — Run `main.py` and check
2. **Does it look right?** — Play the level and watch
3. **Does it feel right?** — Is it fun? Too hard? Too easy?
4. **Did it break anything else?** — Play through all levels to check

If all four are yes — ship it. You're done. Move on to the next thing.

---

*Sky Strike — Built by Kanoa*
