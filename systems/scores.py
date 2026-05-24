"""
systems/scores.py
==================
High-score persistence.

  Web (pygbag / emscripten) : browser localStorage under the key "sky_strike_hs"
  Desktop (Thonny / dev)    : scores.json written next to main.py

Public API
----------
load()              -> list of up to MAX dicts  {"name": str, "score": int}
                       sorted highest-first; empty list if nothing saved yet
qualifies(score)    -> True if score earns a place in the top-MAX list
insert(name, score) -> saves entry, returns (new_board, rank_0indexed)
"""

import sys
import json

MAX  = 5
_KEY  = "sky_strike_hs"
_FILE = "scores.json"


def _is_web():
    return sys.platform == "emscripten"


def load():
    """Return the current leaderboard — list of up to MAX {"name", "score"} dicts."""
    try:
        if _is_web():
            from platform import window
            raw = window.localStorage.getItem(_KEY)
            if raw is None:
                return []
            return json.loads(raw)
        else:
            with open(_FILE) as f:
                return json.load(f)
    except Exception:
        return []


def _save(board):
    try:
        if _is_web():
            from platform import window
            window.localStorage.setItem(_KEY, json.dumps(board))
        else:
            with open(_FILE, "w") as f:
                json.dump(board, f)
    except Exception:
        pass


def qualifies(score):
    """True if this score earns a place in the top-MAX list."""
    board = load()
    if len(board) < MAX:
        return True
    return score > board[-1]["score"]


def insert(name, score):
    """Insert a new entry, trim to MAX, save.
    Returns (board, rank) where rank is 0-indexed (0 = first place).
    """
    board = load()
    entry = {"name": name.strip().upper(), "score": score}
    board.append(entry)
    board.sort(key=lambda e: e["score"], reverse=True)
    board = board[:MAX]
    _save(board)
    # Find where the new entry landed (first match by name + score)
    for i, e in enumerate(board):
        if e["name"] == entry["name"] and e["score"] == entry["score"]:
            return board, i
    return board, 0