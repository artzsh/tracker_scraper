from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from itertools import combinations

from .config import Config
from .models import Match, Participant, Player


@dataclass(frozen=True)
class Record:
    games: int = 0
    wins: int = 0

    @property
    def win_rate(self) -> float:
        return self.wins / self.games if self.games else 0.0

    def add(self, won: bool) -> "Record":
        return Record(self.games + 1, self.wins + int(won))


@dataclass(frozen=True)
class TeamAppearance:
    match: Match
    members: tuple[tuple[Player, Participant], ...]
    won: bool


def team_appearances(matches: list[Match], config: Config) -> list[TeamAppearance]:
    """Split a match into tracked-player parties by in-game team."""
    result: list[TeamAppearance] = []
    allowed_acts = set(config.acts)
    for match in matches:
        if match.act_id not in allowed_acts:
            continue
        by_team: dict[str, list[tuple[Player, Participant]]] = defaultdict(list)
        for participant in match.participants:
            player = next((p for p in config.players if p.matches(participant.riot_id)), None)
            if player:
                by_team[participant.team].append((player, participant))
        for team, members in by_team.items():
            if members:
                result.append(
                    TeamAppearance(
                        match=match,
                        members=tuple(sorted(members, key=lambda item: item[0].canonical_id)),
                        won=team == match.winning_team,
                    )
                )
    return result


def combination_records(appearances: list[TeamAppearance]) -> dict[tuple[str, ...], Record]:
    """Count every observed subset of tracked teammates, not only the maximal party."""
    records: dict[tuple[str, ...], Record] = {}
    for appearance in appearances:
        names = tuple(player.riot_id for player, _ in appearance.members)
        for size in range(1, len(names) + 1):
            for combo in combinations(names, size):
                records[combo] = records.get(combo, Record()).add(appearance.won)
    return records


def role_records(appearances: list[TeamAppearance]) -> dict[tuple[str, str], Record]:
    records: dict[tuple[str, str], Record] = {}
    for appearance in appearances:
        for player, participant in appearance.members:
            key = (player.riot_id, participant.role)
            records[key] = records.get(key, Record()).add(appearance.won)
    return records


def full_stack_rows(appearances: list[TeamAppearance], size: int = 5) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for appearance in appearances:
        if len(appearance.members) != size:
            continue
        row = {
            "match_id": appearance.match.match_id,
            "started_at": appearance.match.started_at.isoformat(),
            "map": appearance.match.map_name,
            "result": "win" if appearance.won else "loss",
        }
        for player, participant in appearance.members:
            row[player.riot_id] = participant.role
        rows.append(row)
    return rows
