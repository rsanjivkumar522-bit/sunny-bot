"""
Simple JSON-backed storage for runtime keyword replies and warn counts.
Data is kept in a local file; on Render use a persistent disk or swap
this module for a database backend (e.g. Redis, SQLite) if you need
true persistence across deploys.
"""
import json
import logging
import threading
from pathlib import Path
from typing import Optional

from bot.config import DEFAULT_KEYWORDS

logger = logging.getLogger(__name__)

_STORE_PATH = Path("data/bot_data.json")
_lock = threading.Lock()


def _load() -> dict:
    """Load the JSON store from disk, initialising it if missing."""
    if not _STORE_PATH.exists():
        _STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
        default: dict = {
            "keywords": DEFAULT_KEYWORDS,
            "warns": {},       # {str(user_id): int}
            "muted": [],       # [int user_id, ...]
            "banned": [],      # [int user_id, ...]
            "stats": {
                "messages_handled": 0,
                "keyword_hits": 0,
                "welcomes_sent": 0,
            },
        }
        _STORE_PATH.write_text(json.dumps(default, indent=2))
        return default
    with _STORE_PATH.open() as f:
        return json.load(f)


def _save(data: dict) -> None:
    with _STORE_PATH.open("w") as f:
        json.dump(data, f, indent=2)


# ── Public API ────────────────────────────────────────────────────────────────

def get_keywords() -> dict[str, str]:
    with _lock:
        return _load().get("keywords", {})


def set_keyword(keyword: str, reply: str) -> None:
    with _lock:
        data = _load()
        data.setdefault("keywords", {})[keyword.lower().strip()] = reply
        _save(data)


def remove_keyword(keyword: str) -> bool:
    """Returns True if keyword existed and was removed."""
    with _lock:
        data = _load()
        kw = keyword.lower().strip()
        if kw in data.get("keywords", {}):
            del data["keywords"][kw]
            _save(data)
            return True
        return False


def get_warns(user_id: int) -> int:
    with _lock:
        return _load().get("warns", {}).get(str(user_id), 0)


def add_warn(user_id: int) -> int:
    """Increment warn count and return new total."""
    with _lock:
        data = _load()
        data.setdefault("warns", {})
        data["warns"][str(user_id)] = data["warns"].get(str(user_id), 0) + 1
        _save(data)
        return data["warns"][str(user_id)]


def reset_warns(user_id: int) -> None:
    with _lock:
        data = _load()
        data.setdefault("warns", {}).pop(str(user_id), None)
        _save(data)


def is_muted(user_id: int) -> bool:
    with _lock:
        return user_id in _load().get("muted", [])


def set_muted(user_id: int, muted: bool) -> None:
    with _lock:
        data = _load()
        data.setdefault("muted", [])
        if muted and user_id not in data["muted"]:
            data["muted"].append(user_id)
        elif not muted and user_id in data["muted"]:
            data["muted"].remove(user_id)
        _save(data)


def is_banned(user_id: int) -> bool:
    with _lock:
        return user_id in _load().get("banned", [])


def increment_stat(key: str, amount: int = 1) -> None:
    with _lock:
        data = _load()
        data.setdefault("stats", {})[key] = data["stats"].get(key, 0) + amount
        _save(data)


def get_stats() -> dict:
    with _lock:
        return _load().get("stats", {})
