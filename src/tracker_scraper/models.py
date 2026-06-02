from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

ROLES = ("controller", "duelist", "initiator", "sentinel", "unknown")


@dataclass(frozen=True)
class Player:
    riot_id: str
    aliases: tuple[str, ...] = ()

    @property
    def canonical_id(self) -> str:
        return normalize_riot_id(self.riot_id)

    def matches(self, riot_id: str) -> bool:
        normalized = normalize_riot_id(riot_id)
        return normalized == self.canonical_id or normalized in {
            normalize_riot_id(alias) for alias in self.aliases
        }


@dataclass(frozen=True)
class Participant:
    riot_id: str
    team: str
    agent: str
    role: str


@dataclass(frozen=True)
class Match:
    match_id: str
    act_id: str
    started_at: datetime
    map_name: str
    winning_team: str
    participants: tuple[Participant, ...]

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Match":
        participants = tuple(
            Participant(
                riot_id=item["riot_id"],
                team=item["team"],
                agent=item.get("agent", "unknown"),
                role=normalize_role(item.get("role", "unknown")),
            )
            for item in raw["participants"]
        )
        return cls(
            match_id=str(raw["match_id"]),
            act_id=str(raw["act_id"]),
            started_at=datetime.fromisoformat(str(raw["started_at"]).replace("Z", "+00:00")),
            map_name=str(raw.get("map", "unknown")),
            winning_team=str(raw["winning_team"]),
            participants=participants,
        )


def normalize_riot_id(value: str) -> str:
    return value.strip().casefold()


def normalize_role(value: str) -> str:
    role = value.strip().casefold()
    return role if role in ROLES else "unknown"
