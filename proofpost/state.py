"""Small JSON state file: watermark, drafted items, kit history.

The MVP plan specifies SQLite; v1 uses a single JSON file instead — for a
single-user personal tool it keeps the same guarantees (incremental scans,
no item drafted twice, kit cadence) with zero schema/migration overhead.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_STATE_PATH = Path.home() / ".proofpost" / "state.json"


def default_state() -> dict[str, Any]:
    return {
        "watermark": None,          # ISO ts of the newest event ever scanned
        "drafted_ids": [],          # material ids already put in a kit
        "posted_ids": [],           # material ids the user confirmed posted
        "last_kit_at": None,        # ISO ts of the most recent kit
        "kits": [],                 # [{file, created_at, theme_ids}]
    }


def load_state(path: Path | str | None = None) -> dict[str, Any]:
    path = Path(path) if path else DEFAULT_STATE_PATH
    if not path.exists():
        return default_state()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default_state()
    state = default_state()
    state.update({k: data.get(k, v) for k, v in state.items()})
    return state


def save_state(state: dict[str, Any], path: Path | str | None = None) -> Path:
    path = Path(path) if path else DEFAULT_STATE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
    return path


def mark_drafted(state: dict[str, Any], theme_ids: list[str], kit_file: str) -> None:
    drafted = set(state.get("drafted_ids", []))
    drafted.update(theme_ids)
    state["drafted_ids"] = sorted(drafted)
    now = datetime.now(timezone.utc).isoformat()
    state["last_kit_at"] = now
    state.setdefault("kits", []).append(
        {"file": kit_file, "created_at": now, "theme_ids": list(theme_ids)}
    )


def mark_posted(state: dict[str, Any], theme_ids: list[str]) -> None:
    posted = set(state.get("posted_ids", []))
    posted.update(theme_ids)
    state["posted_ids"] = sorted(posted)


def days_since_last_kit(state: dict[str, Any]) -> float | None:
    last = state.get("last_kit_at")
    if not last:
        return None
    try:
        last_dt = datetime.fromisoformat(last)
    except ValueError:
        return None
    return (datetime.now(timezone.utc) - last_dt).total_seconds() / 86400.0
