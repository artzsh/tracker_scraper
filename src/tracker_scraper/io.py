from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

from .models import Match


def load_matches(path: Path) -> list[Match]:
    """Load and deduplicate normalized authorized exports by match ID."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    matches = raw["matches"] if isinstance(raw, dict) else raw
    unique: dict[str, Match] = {}
    for item in matches:
        match = Match.from_dict(item)
        unique[match.match_id] = match
    return sorted(unique.values(), key=lambda match: (match.started_at, match.match_id))


def load_matches_if_exists(path: Path) -> list[Match]:
    return load_matches(path) if path.exists() else []


def write_matches(path: Path, matches: Iterable[Match]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(matches, key=lambda match: (match.started_at, match.match_id))
    payload = {"matches": [match.to_dict() for match in ordered]}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
