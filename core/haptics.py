"""
core/haptics.py
================
Device vibration / haptic feedback.

All vibration calls go through vibrate() so the rest of the game
never has to think about platform differences. Desktop runs silently.
Browser (pygbag) triggers the Web Vibration API via the JS bridge.

Correct pygbag pattern (from official FAQ):
    from platform import window
    window.navigator.vibrate(ms)

NOT platform.window.navigator.vibrate() — that form doesn't work.

VIBRATION SCALE used in Sky Strike:
    30ms  — enemy destroyed (small satisfying pulse)
    80ms  — player takes a hit (sharp jolt)
    300ms — player destroyed (heavy rumble)
    400ms — boss defeated (big celebration)
    600ms — final boss defeated (maximum celebration)
"""

import sys


def vibrate(ms):
    """Trigger device vibration for `ms` milliseconds.

    Browser/mobile only. Silent on desktop — sys.platform check
    ensures we never try the JS bridge outside of pygbag/emscripten.
    The try/except catches unsupported browsers or devices gracefully.
    """
    if sys.platform != "emscripten":
        return   # desktop — no vibration API, skip silently

    try:
        from platform import window
        window.navigator.vibrate(ms)
    except Exception:
        pass     # unsupported browser or device — fail silently