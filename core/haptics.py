"""
core/haptics.py
================
Device vibration / haptic feedback.

All vibration calls go through vibrate() so the rest of the game
never has to think about platform differences. Desktop runs silently.
Browser (pygbag) triggers the Web Vibration API via the JS bridge.

USAGE:
    from core.haptics import vibrate
    vibrate(80)    # 80ms jolt

VIBRATION SCALE used in Sky Strike:
    30ms  — enemy destroyed (small satisfying pulse)
    80ms  — player takes a hit (sharp jolt)
    300ms — player destroyed (heavy rumble)
    400ms — boss defeated (big celebration)
    600ms — final boss defeated (maximum celebration)

Adding gamepad rumble (future):
    The joystick object lives in core/input.py as _joystick.
    pygame joystick supports: joystick.rumble(low_freq, high_freq, duration_ms)
    Add a rumble call here alongside the vibrate() call when ready.
"""


def vibrate(ms):
    """Trigger device vibration for `ms` milliseconds.

    Browser/mobile only — uses pygbag's JavaScript bridge to call
    navigator.vibrate(). Silent on desktop or unsupported devices.
    The try/except means this never crashes the game regardless of
    platform or browser support.
    """
    try:
        import platform
        platform.window.navigator.vibrate(ms)
    except Exception:
        pass   # desktop, unsupported browser, or no vibration API — fail silently