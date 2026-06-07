# Sky Strike — Beginner Quick Reference
### "The Easy Control Panel"

> This is your cheat sheet. When you want to change something quickly, find it here. No long explanations — just the steps.

---

## ⚡ Change Enemy HP (How tough the enemy is)

**File:** `levels/level_0X.py` (whichever level you want to change)

**Find:**
```python
"enemy_hp": 20,
```
**Change the number.** Safe range: **5 to 200**

| Value | Difficulty |
|---|---|
| 10 | Very easy |
| 20 | Normal |
| 50 | Hard |
| 100 | Boss tough |
| 150 | Mega boss |

---

## ⚡ Change How Fast the Enemy Shoots

**File:** `levels/level_0X.py`

**Find:**
```python
"enemy_fire_rate": 90,
```
**Change the number.** Safe range: **20 to 180**
⚠️ **LOWER = FASTER shooting**

| Value | Feel |
|---|---|
| 20 | Extremely fast (very hard!) |
| 45 | Fast |
| 90 | Normal |
| 120 | Slow |
| 180 | Very slow (very easy) |

---

## ⚡ Change Enemy Bullet Speed

**File:** `levels/level_0X.py`

**Find:**
```python
"enemy_bullet_speed": 7,
```
**Change the number.** Safe range: **3 to 15**

| Value | Feel |
|---|---|
| 3 | Slow, easy to dodge |
| 7 | Normal |
| 12 | Fast, hard to dodge |
| 15 | Very fast (nearly impossible) |

---

## ⚡ Change the Enemy's Image (Sprite)

**Step 1** — Put your new PNG in `assets/sprites/`

**Step 2** — Open `levels/level_0X.py` and find:
```python
"enemy_image": "sprites/enemy1.png",
```
Change `enemy1.png` to your new filename.

**Step 3** — Also check the size fits:
```python
"enemy_size": (130, 60),
```
Change width and height to match your image roughly.

---

## ⚡ Flip an Enemy Image (If it faces the wrong way)

**File:** `levels/level_0X.py`

**Find:**
```python
"needs_flip": False,
```
Change to:
```python
"needs_flip": True,
```

---

## ⚡ Change the Background

**File:** `levels/level_0X.py`

**Find:**
```python
"background": fill_solid_sky,
```

**Options you can use right now:**

| Option | What it looks like |
|---|---|
| `fill_solid_sky` | Plain blue sky |
| `fill_sunset` | Orange/red sunset |
| `fill_night` | Dark night sky |
| `fill_storm` | Dark stormy sky |

Change `fill_solid_sky` to any option from the list.

Also make sure the import at the TOP of the file matches:
```python
from systems.backgrounds import fill_solid_sky
```
Change `fill_solid_sky` there too.

**To turn clouds on or off:**
```python
"show_clouds": True,   ← shows clouds
"show_clouds": False,  ← no clouds
```

---

## ⚡ Change the Movement Pattern

**File:** `levels/level_0X.py`

**TWO things to change — both must match:**

**Line 1** — near the top of the file:
```python
from systems.movement import move_sine
```

**Line 2** — inside the LEVEL dict:
```python
"movement": move_sine,
```

**Available patterns:**

| Pattern name | What the enemy does |
|---|---|
| `move_sine` | Smooth up-down wave |
| `move_random_target` | Random spots, pauses (use for bosses) |
| `move_dive` | Chases your height |
| `move_zigzag` | Sharp bounces top to bottom |
| `move_strafe` | Holds perfectly still |
| `move_figure_eight` | Figure-8 loop |
| `move_circle` | Orbits in a circle |
| `move_retreat` | Backs away when you get close |

---

## ⚡ Change a Fighter's Stats

**File:** `levels/fighters.py`

Find the fighter you want to change and adjust these values:

```python
{
    "name":       "WARTHOG",
    "hp":         7,       ← hit points (3 to 10)
    "speed":      4,       ← movement speed (2 to 8)
    "fire_rate":  15,      ← how fast it shoots — LOWER = FASTER (8 to 30)
},
```

---

## ⚡ Change a Fighter's Image

**File:** `levels/fighters.py`

**Step 1** — Put new PNG in `assets/sprites/`

**Step 2** — Find the fighter and change:
```python
"sprite": "sprites/warthog.png",
```
to your new filename.

**Step 3** — If the image faces the wrong way:
```python
"needs_flip": True,
```

---

## ⚡ Add a Brand New Fighter

**File:** `levels/fighters.py`

Copy one of the existing fighter blocks and paste it into the list. Change all the values to whatever you want:

```python
{
    "name":       "MY NEW JET",
    "sprite":     "sprites/mynewjet.png",
    "hp":         5,
    "speed":      5,
    "fire_rate":  12,
    "weapon":     "machine_gun",
    "size":       (130, 60),
    "needs_flip": False,
},
```

⚠️ Make sure there's a comma after the closing `}` if it's not the last fighter in the list.

---

## ⚡ Give an Enemy a Boss Name

**File:** `levels/level_0X.py`

**Find:**
```python
"boss_name": None,
```
**Change to:**
```python
"boss_name": "YOUR BOSS NAME HERE",
```

This makes the boss intro screen appear with your chosen name before the level starts.

---

## ⚡ Quick Safe Ranges Summary

| Setting | Minimum | Maximum | Lower = |
|---|---|---|---|
| `enemy_hp` | 5 | 200 | Easier |
| `enemy_fire_rate` | 20 | 180 | Faster shooting ⚠️ |
| `enemy_bullet_speed` | 3 | 15 | Slower bullets |
| `enemy_damage` | 1 | 3 | Less damage |
| Fighter `hp` | 3 | 10 | Less health |
| Fighter `speed` | 2 | 8 | Slower |
| Fighter `fire_rate` | 8 | 30 | Faster shooting ⚠️ |

---

## ⚠️ Things to Always Remember

- **Save before changing anything** — Ctrl + S
- **Don't remove quotes or commas** — Python needs them
- **Don't rename the left side** of a colon — only change the right side
- **Ctrl + Z** undoes your last change if something breaks
- **Read the error message** — it tells you which line has a problem

---

*Sky Strike — Built by Kanoa*
