"""
systems/audio.py
=================
All game audio -- background music and sound effects.

PLACEHOLDER MODE (no .ogg files yet):
  Every trigger point has a generated sine-wave sound.
  No external dependencies -- pure Python + pygame.

PRODUCTION MODE (with .ogg files):
  Drop .ogg files into assets/sounds/ and they load automatically.
  Music:  assets/sounds/<track_name>      e.g. level_01_bg.ogg
  SFX:    assets/sounds/<name>.ogg        e.g. player_hit.ogg

FORMAT: .ogg only (pygbag / browser requirement).

CHANNELS:
  0   reserved -- background music (looping)
  1   reserved -- shoot sound (cuts off previous, no rapid stacking)
  2+  free pool -- all other SFX
"""

import math
import os
import struct

import pygame

from core.paths import asset_path


# ============================================================
# CONSTANTS
# ============================================================

_RATE     = 44100
_MUSIC_CH = 0
_SHOOT_CH = 1

_music_vol = 0.80
_sfx_vol   = 0.65

# Per-sound volume overrides — 0.0 to 1.0.
# Applied on top of _sfx_vol. Tune these without touching the .ogg files.
# Any name not listed here uses _sfx_vol as-is.
_sfx_volumes = {
    "shoot":          0.4,
    "9mm1":           0.1,
    "12GAreload":     0.2,
    "taser":          0.6,
    "cannon1":        0.3,
    "cannon2":        0.5,
    "mg1":            0.3,
    "m16burst":       0.3,
    "hit_cockpit":    0.85,
    "hit_body":       0.65,
    "player_hit":     0.70,
    "player_die":     0.80,
    "enemy_die":      0.70,
    "boss_die":       0.85,
    "level_complete": 0.75,
    "life_lost":      0.90,
    "game_over":      0.90,
    "all_complete":   0.80,
    "new_high_score": 0.70,
}

_sfx_cache   = {}
_music_cache = {}
_music_now   = None


# ============================================================
# PUBLIC API
# ============================================================

def init():
    """Initialise mixer, build placeholder sounds, then load all real .ogg files."""
    if pygame.mixer.get_init():
        pygame.mixer.quit()
    pygame.mixer.init(_RATE, -16, 2, 1024)
    pygame.mixer.set_num_channels(16)
    pygame.mixer.set_reserved(2)
    _build_sfx()
    _build_music_placeholders()
    # Scan assets/sounds/ and load every .ogg into _sfx_cache.
    # Real files overwrite generated placeholders with matching names.
    # This runs once — no more cache vs file conflicts ever.
    _preload_real_sfx()


def play_music(track):
    """Loop background music for track filename. No-op if already playing."""
    global _music_now
    if track == _music_now:
        return
    stop_music()
    sound = _load_or_make_music(track)
    ch = pygame.mixer.Channel(_MUSIC_CH)
    ch.set_volume(_music_vol)
    ch.play(sound, loops=-1)
    _music_now = track


def stop_music():
    """Stop background music immediately."""
    global _music_now
    pygame.mixer.Channel(_MUSIC_CH).stop()
    _music_now = None


def play_sfx(name):
    """Play a one-shot SFX by name.

    Names: shoot, player_hit, player_die, enemy_hit, crit, enemy_die,
           boss_die, level_complete, game_over, victory, life_lost, high_score
    """
    vol = _sfx_volumes.get(name, _sfx_vol)
    if vol <= 0.0:
        return   # volume is zero — skip entirely, no pygame weirdness
    sound = _load_or_make_sfx(name)
    if not sound:
        return
    if name == "shoot":
        ch = pygame.mixer.Channel(_SHOOT_CH)
    else:
        ch = pygame.mixer.find_channel()
    if ch:
        ch.set_volume(vol)
        ch.play(sound)


def set_music_volume(vol):
    global _music_vol
    _music_vol = max(0.0, min(1.0, vol))
    pygame.mixer.Channel(_MUSIC_CH).set_volume(_music_vol)


def set_sfx_volume(vol):
    global _sfx_vol
    _sfx_vol = max(0.0, min(1.0, vol))


# ============================================================
# SOUND GENERATION
# ============================================================

def _pack(buf, idx, v):
    v = max(-32768, min(32767, int(v)))
    struct.pack_into("<hh", buf, idx * 4, v, v)


def _tone(freq, ms, vol=1.0, attack_ms=15, decay_ms=80):
    n   = _RATE * ms // 1000
    att = max(1, _RATE * attack_ms // 1000)
    dec = max(1, _RATE * decay_ms  // 1000)
    buf = bytearray(n * 4)
    for i in range(n):
        if   i < att:       env = i / att
        elif i > n - dec:   env = max(0.0, (n - i) / dec)
        else:               env = 1.0
        _pack(buf, i, math.sin(2 * math.pi * freq * i / _RATE) * 32767 * vol * env)
    return pygame.mixer.Sound(buffer=bytes(buf))


def _sweep(f0, f1, ms, vol=0.8):
    n     = _RATE * ms // 1000
    buf   = bytearray(n * 4)
    phase = 0.0
    for i in range(n):
        freq   = f0 + (f1 - f0) * i / n
        phase += 2 * math.pi * freq / _RATE
        _pack(buf, i, math.sin(phase) * 32767 * vol * (1 - i / n))
    return pygame.mixer.Sound(buffer=bytes(buf))


def _chord(freqs, ms, vol=0.5):
    n   = _RATE * ms // 1000
    buf = bytearray(n * 4)
    for i in range(n):
        val = sum(math.sin(2 * math.pi * f * i / _RATE) for f in freqs)
        _pack(buf, i, val / len(freqs) * 32767 * vol * (1 - i / n))
    return pygame.mixer.Sound(buffer=bytes(buf))


def _arpeggio(freqs, note_ms, vol=0.5):
    n_per = _RATE * note_ms // 1000
    buf   = bytearray(n_per * len(freqs) * 4)
    for j, freq in enumerate(freqs):
        for i in range(n_per):
            _pack(buf, j * n_per + i,
                  math.sin(2 * math.pi * freq * i / _RATE) * 32767 * vol * (1 - i / n_per))
    return pygame.mixer.Sound(buffer=bytes(buf))


def _ambient(freqs, seconds, vol=0.15):
    n    = _RATE * seconds
    fade = _RATE * 50 // 1000
    buf  = bytearray(n * 4)
    for i in range(n):
        if   i < fade:      env = i / fade
        elif i > n - fade:  env = (n - i) / fade
        else:               env = 1.0
        val = sum(math.sin(2 * math.pi * f * i / _RATE) for f in freqs)
        _pack(buf, i, val / len(freqs) * 32767 * vol * env)
    return pygame.mixer.Sound(buffer=bytes(buf))


def _build_sfx():
    _sfx_cache.update({
        "shoot":          _tone(880,  70,  vol=0.30, attack_ms=3,  decay_ms=55),
        "enemy_hit":      _tone(350,  80,  vol=0.50, attack_ms=5,  decay_ms=60),
        "crit":           _tone(1200, 100, vol=0.55, attack_ms=5,  decay_ms=70),
        "player_hit":     _chord([180, 220], 180, vol=0.60),
        "enemy_die":      _chord([120, 160], 420, vol=0.65),
        "boss_die":       _chord([80, 100, 160], 900, vol=0.75),
        "player_die":     _sweep(420, 80,  900,  vol=0.70),
        "life_lost":      _sweep(380, 200, 700,  vol=0.60),
        "game_over":      _sweep(360, 80,  1200, vol=0.65),
        "level_complete": _arpeggio([523, 659, 784, 1047], 130, vol=0.55),
        "victory":        _arpeggio([523, 659, 784, 880, 1047, 1047], 140, vol=0.60),
        "high_score":     _arpeggio([659, 784, 1047, 1319], 110, vol=0.55),
    })


def _build_music_placeholders():
    # A minor chord -- calm but slightly tense. All 5 current levels share this
    # placeholder until real .ogg tracks are dropped in.
    _music_cache["_default"] = _ambient([220, 261, 330], 4, vol=0.14)


def _preload_real_sfx():
    """Load every .ogg in assets/sounds/ into _sfx_cache at startup.

    Overwrites any generated placeholder with the same name so real files
    always win. Also loads fighter shoot sounds (mg1, cannon1 etc.) that
    have no generated placeholder. Music files are ignored here — they are
    handled on demand by _load_or_make_music.
    """
    sounds_dir = asset_path("sounds")
    if not os.path.isdir(sounds_dir):
        return
    for fname in os.listdir(sounds_dir):
        if not fname.lower().endswith(".ogg"):
            continue
        name = fname[:-4]   # strip .ogg extension
        path = os.path.join(sounds_dir, fname)
        try:
            _sfx_cache[name] = pygame.mixer.Sound(path)
        except Exception:
            pass


def _load_or_make_sfx(name):
    # Cache is fully populated at init (placeholders + real files).
    # Just return whatever is in there.
    return _sfx_cache.get(name)


def _load_or_make_music(track):
    if track in _music_cache:
        return _music_cache[track]
    path = asset_path(f"sounds/{track}")
    if os.path.exists(path):
        try:
            sound = pygame.mixer.Sound(path)
            _music_cache[track] = sound
            return sound
        except Exception:
            pass
    return _music_cache.get("_default", list(_music_cache.values())[0])