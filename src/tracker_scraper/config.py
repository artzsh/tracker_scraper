from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import Player


@dataclass(frozen=True)
class Config:
    acts: tuple[str, ...]
    players: tuple[Player, ...]

    @classmethod
    def load(cls, path: Path) -> "Config":
        raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            acts=tuple(str(act) for act in raw["acts"]),
            players=tuple(
                Player(
                    riot_id=str(item["riot_id"]),
                    aliases=tuple(str(alias) for alias in item.get("aliases", [])),
                )
                for item in raw["players"]
            ),
        )
