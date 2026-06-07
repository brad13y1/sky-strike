# Sky Strike — How Your Game Works
### A Guide for the Kid Who Built It

---

> **Hey.** This is YOUR game. You drew the art, you named the bosses, and your dad helped you build the code that makes it all run. This guide is going to show you exactly how it works — so you can start changing things, adding things, and eventually building games completely on your own.
>
> You don't need to understand everything at once. Read a section, try something, break something, fix it. That's how every game developer in the world learns.

---

## Part 1 — What IS a Game, Really?

Before we look at any code, let's talk about what a game actually is when a computer runs it.

### The Game Loop

Your game runs **60 times every second**. Every single time it runs, it does the same three things in order:

```
1. CHECK — Did anything happen? (Did you move your finger? Did a bullet hit something?)
2. UPDATE — Change the game world based on what happened
3. DRAW — Paint the screen so you can see the result
```

Then it does it again. And again. 60 times a second, forever, until you close the game.

That's it. Every game you've ever played — Minecraft, Roblox, any of them — is doing this same loop. Sky Strike does it too.

Think of it like a flipbook. Each page is slightly different. Flick through them fast enough and it looks like things are moving.

---

### What is Code?

Code is just **instructions written in a language the computer understands**.

Python (the language Sky Strike is written in) is one of the friendliest languages to learn. It reads almost like English.

For example, this line:
```python
player["speed"] = 5
```
Means: "The player's speed is 5."

And this:
```python
if player["hp"] <= 0:
    state = "game_over"
```
Means: "If the player's health points reach zero or below, switch to the game over screen."

You can understand that just by reading it, right? That's why Python is great for learning.

---

## Part 2 — Meet Your Files

Sky Strike isn't one giant file. It's split into lots of smaller files, each one doing a specific job. This is how real games are built.

Think of it like a sports team. The goalkeeper has one job. The striker has one job. They work together, but they don't do each other's jobs.

Here's your team:

```
Sky_Strike/
│
├── main.py               ← THE COACH. Starts everything, runs the game loop.
│
├── core/                 ← THE FOUNDATION. Basic stuff everything else needs.
│   ├── constants.py      ← The rulebook. Screen size, colors, game title.
│   ├── input.py          ← The ears. Listens for your keyboard, touch, buttons.
│   ├── display.py        ← The TV. Makes sure the game fits your screen.
│   ├── fonts.py          ← The text styles. Small, medium, big writing.
│   ├── paths.py          ← The map. Helps find image files wherever the game runs.
│   └── haptics.py        ← The rumble. Makes the phone vibrate (if it supports it).
│
├── systems/              ← THE ENGINE PARTS. Things that make the game work.
│   ├── movement.py       ← The brain. Controls how enemies move.
│   ├── backgrounds.py    ← The painter. Draws the sky, clouds, stars.
│   ├── drawing.py        ← The artist. Draws your jet, the enemy, health bars.
│   ├── effects.py        ← The special effects. Explosions, CRIT text popups.
│   └── weapons.py        ← The armory. Controls how bullets look and move.
│
├── scenes/               ← THE SCREENS the player sees.
│   ├── title.py          ← The title screen with your start image.
│   └── gameplay.py       ← THE GAME ITSELF. The most important file.
│
├── levels/               ← THE LEVELS. One file per level.
│   ├── loader.py         ← The setup crew. Prepares everything before a level starts.
│   ├── fighters.py       ← The pilot roster. All your playable jets.
│   ├── level_01.py       ← Level 1 settings
│   ├── level_02.py       ← Level 2 settings
│   ├── level_03.py       ← Level 3 settings (boss level!)
│   ├── level_04.py       ← Level 4 settings
│   └── level_05.py       ← Level 5 settings (final boss!)
│
└── assets/               ← THE ART AND SOUNDS.
    ├── sprites/          ← PNG images for jets, enemies, bosses
    ├── backgrounds/      ← PNG images for level backgrounds
    └── sounds/           ← Sound effects and music (coming soon!)
```

### The Golden Rule

Information only flows ONE WAY — from the bottom of that list upward. 

`core` doesn't know about levels. `systems` doesn't know about scenes. This is important because it means changing a level file can never accidentally break the engine. Your art can never break your math.

---

## Part 3 — How a Level Works

Let's look at a real level file. Open `levels/level_01.py` in Thonny. You'll see something like this:

```python
from systems.backgrounds import fill_solid_sky
from systems.movement   import move_sine

LEVEL = {
    "enemy_hp":           20,
    "enemy_fire_rate":    90,
    "enemy_bullet_speed": 7,
    "enemy_damage":       1,
    "enemy_image":        "sprites/enemy1.png",
    "enemy_size":         (130, 60),
    "background":         fill_solid_sky,
    "player_hp":          5,
    "movement":           move_sine,
    "hit_body":           55,
    "hit_cockpit":        None,
    "hit_cockpit_damage": 0,
    "boss_name":          None,
    "show_clouds":        True,
}
```

That big thing with curly braces `{ }` is called a **dictionary**. Think of it like a form with fields to fill in.

Each line is:
```
"field name": value,
```

The computer reads this form before the level starts and sets everything up based on what you wrote.

**You can change any of those numbers and the game changes.** That's the power of this design. You don't have to touch the engine — just fill in different numbers on the form.

---

## Part 4 — What Every Setting Does

Let's go through each setting and what it means in plain English.

### Enemy Settings

| Setting | What it means | Example |
|---|---|---|
| `enemy_hp` | How many times you have to hit the enemy before it dies | 20 = takes 20 hits |
| `enemy_fire_rate` | How many frames between each enemy shot | 90 = shoots once every 1.5 seconds. Lower = shoots FASTER |
| `enemy_bullet_speed` | How fast enemy bullets travel | 7 = medium speed. Higher = harder to dodge |
| `enemy_damage` | How much HP you lose when an enemy bullet hits you | 1 = one hit point lost |
| `enemy_image` | Which PNG file to use for the enemy sprite | `"sprites/enemy1.png"` |
| `enemy_size` | How big the enemy sprite is on screen (width, height in pixels) | `(130, 60)` |

### Player Settings

| Setting | What it means | Example |
|---|---|---|
| `player_hp` | This is here for old reasons — the real HP comes from your fighter in fighters.py | Usually ignored |

### Visual Settings

| Setting | What it means | Example |
|---|---|---|
| `background` | Which background function to use | `fill_solid_sky` = plain blue |
| `show_clouds` | Should clouds appear floating across the sky? | `True` or `False` |

### Hit Detection Settings

| Setting | What it means | Example |
|---|---|---|
| `hit_body` | How close a bullet must get to the enemy CENTER to count as a hit (pixels) | 55 = 55 pixels |
| `hit_cockpit` | Size of the cockpit weak spot (or `None` if there isn't one) | `None` or a number |
| `hit_cockpit_damage` | How much damage a cockpit hit does | 0 = normal damage |

### Boss Settings

| Setting | What it means | Example |
|---|---|---|
| `boss_name` | The boss's name shown on screen. `None` means no boss intro. | `"MO-FORCE-1"` or `None` |
| `movement` | Which movement pattern the enemy uses | `move_sine`, `move_zigzag`, etc. |

---

## Part 5 — Safe Numbers to Use

Here are safe ranges for every number you might want to change. Stay within these ranges and the game will always work correctly.

### Enemy HP
- **Minimum:** 5 (dies too fast, not fun)
- **Maximum:** 200 (really tough boss)
- **Sweet spot for normal enemies:** 15–40
- **Sweet spot for bosses:** 80–150

### Enemy Fire Rate
- **Minimum:** 20 (fires very fast — extremely hard!)
- **Maximum:** 180 (fires very slow — very easy)
- **Sweet spot for normal:** 60–100
- **Sweet spot for boss:** 30–60
- ⚠️ **Remember:** LOWER numbers = FASTER shooting

### Enemy Bullet Speed
- **Minimum:** 3 (very slow, easy to dodge)
- **Maximum:** 15 (very fast, nearly impossible)
- **Sweet spot:** 5–10

### Enemy Damage
- **Minimum:** 1
- **Maximum:** 3 (you only have 5 HP, so 3 damage = 2 hits to kill you)
- **Sweet spot:** 1–2

### Enemy Size
- Format is `(width, height)` in pixels
- **Normal enemy:** `(130, 60)` to `(160, 80)`
- **Big boss:** `(180, 90)` to `(240, 120)`
- ⚠️ Keep the proportions roughly the same as the original image

---

## Part 6 — The Movement Patterns

The `movement` setting controls HOW the enemy moves. You pick one of these:

| Pattern | What the enemy does | Good for |
|---|---|---|
| `move_sine` | Smooth up-and-down wave | Level 1, easy enemies |
| `move_random_target` | Flies to random spots, pauses, repeats | Bosses |
| `move_dive` | Tracks where YOU are and charges at your height | Fast interceptors |
| `move_zigzag` | Sharp bounces top-to-bottom | Mid-game challenge |
| `move_strafe` | Stays completely still — just shoots | Tank enemies |
| `move_figure_eight` | Loops in a figure-8 shape | Mid-bosses |
| `move_circle` | Orbits in a circle | Advanced enemies |
| `move_retreat` | Backs away when you get close | Sniper enemies |

**To use one**, you need TWO changes in a level file:

**Line 1** — at the top of the file, change the import:
```python
from systems.movement import move_zigzag
```

**Line 2** — inside the LEVEL dict:
```python
"movement": move_zigzag,
```

Both lines must use the SAME pattern name.

---

## Part 7 — Your Fighters

Open `levels/fighters.py`. This is where all your playable jets live. Each one looks like this:

```python
{
    "name":       "WARTHOG",
    "sprite":     "sprites/warthog.png",
    "hp":         7,
    "speed":      4,
    "fire_rate":  15,
    "weapon":     "machine_gun",
    "size":       (130, 60),
    "needs_flip": True,
},
```

### Fighter Settings

| Setting | What it means |
|---|---|
| `name` | The name shown on the fighter select screen |
| `sprite` | Which PNG file to use |
| `hp` | How many hit points this fighter starts with |
| `speed` | How fast it moves (higher = faster) |
| `fire_rate` | How fast it shoots (LOWER = faster) |
| `weapon` | Which weapon it uses (`"machine_gun"` is the main one) |
| `size` | How big the sprite appears (width, height) |
| `needs_flip` | Does the PNG need to be flipped horizontally? `True` or `False` |

### Safe Ranges for Fighters

| Setting | Min | Max | Notes |
|---|---|---|---|
| `hp` | 3 | 10 | 5 is standard |
| `speed` | 2 | 8 | 4–5 feels good |
| `fire_rate` | 8 | 30 | Lower = faster shooting |

---

## Part 8 — Swapping Sprites (Images)

Want to use a new image for an enemy or jet? There are only two steps:

**Step 1** — Put your new PNG file in the right folder:
- Jet sprites → `assets/sprites/`
- Enemy sprites → `assets/sprites/`
- Level backgrounds → `assets/backgrounds/`

**Step 2** — Update the filename in the right file:
- For a jet: open `levels/fighters.py` and change the `"sprite"` line
- For an enemy: open the level file (e.g. `level_03.py`) and change `"enemy_image"`
- For a background: check how `level_04.py` or later levels set up their background

That's it! No other code needs to change.

### Image Tips
- PNG files work best (they support transparency)
- Try to keep images roughly the same size as what they're replacing
- If the image faces the wrong way, set `"needs_flip": True`

---

## Part 9 — Your First Change (Try This Now!)

Let's make a real change right now. This will prove to you that you understand how it works.

**Goal:** Make Level 1 much harder.

**Step 1** — Open `levels/level_01.py` in Thonny.

**Step 2** — Find these three lines:
```python
"enemy_hp":           20,
"enemy_fire_rate":    90,
"enemy_bullet_speed": 7,
```

**Step 3** — Change them to:
```python
"enemy_hp":           50,
"enemy_fire_rate":    40,
"enemy_bullet_speed": 12,
```

**Step 4** — Save the file (Ctrl + S).

**Step 5** — Run `main.py` and play Level 1.

The enemy should now be much tougher — more HP, shoots faster, bullets move quicker. 

When you're done testing, you can change the numbers back or keep them if you like the new difficulty.

**You just changed your game's difficulty without touching the engine.** That's exactly how real game designers work.

---

## Part 10 — How NOT to Break Things

Here are the most common ways people accidentally break their game — and how to avoid them.

### Always Save Before You Change Something
Use **Ctrl + S** before and after every change. That way you can always remember what you had before.

### Don't Delete the Quotes or Commas
Python is fussy about punctuation. Every text value needs quotes around it:
```python
"enemy_image": "sprites/enemy1.png",   ← CORRECT (has quotes AND comma)
enemy_image: sprites/enemy1.png        ← BROKEN (missing quotes and comma)
```

### Don't Change the Key Names
The LEFT side of each colon is the key name. **Don't change these.** The right side is the value — that's what you change.
```python
"enemy_hp": 20,
#  ↑              ↑
# DON'T touch    CHANGE THIS
```

### If You Break Something
1. Don't panic
2. Look at the error message — it usually tells you EXACTLY which line the problem is on
3. Compare your changed line to what it looked like before
4. Fix the punctuation or value and try again

### The Undo Button
In Thonny, **Ctrl + Z** undoes your last change. You can press it many times to go back further.

---

## Part 11 — What Happens When You Run the Game

When you click Run in Thonny, here's exactly what happens in order:

1. **`main.py` starts** — the coach blows the whistle
2. **The display is set up** — the game window appears
3. **Fonts are loaded** — so text can be drawn
4. **Input is set up** — the game starts listening for key presses and taps
5. **The title scene loads** — you see the title screen
6. **You press Start** — the game loads Level 1 using `levels/loader.py`
7. **The game loop begins** — check → update → draw, 60 times per second
8. **Each frame**, `gameplay.py` handles everything: your movement, enemy movement, bullets, collisions, drawing

Every time you interact with the game — move, shoot, take a hit — `gameplay.py` is the file handling it.

---

## Part 12 — You're a Game Developer

You have built a real game that:
- Runs on computers AND phones
- Has multiple levels with different difficulties
- Has different playable characters with different abilities
- Has bosses with names and special intros
- Is playable by your friends right now via a link

Most people never build anything like this. You did it before age 12.

The next steps are yours to decide:
- New levels with your own art?
- New movement patterns for enemies?
- Sound effects?
- New fighters?

All of those things are within reach now. You know how the files fit together. You know which numbers to change. You know how to test your changes.

**Go build something.**

---

*Sky Strike — Built by Kanoa*
