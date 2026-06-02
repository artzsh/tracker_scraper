from __future__ import annotations

import json
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
