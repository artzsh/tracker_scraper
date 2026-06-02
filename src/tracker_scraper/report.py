from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

from .analytics import Record, TeamAppearance, combination_records, full_stack_rows, role_records


def _percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def _write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_reports(appearances: list[TeamAppearance], output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    combos = combination_records(appearances)
    roles = role_records(appearances)
    combo_rows = [
        {"players": " | ".join(players), "size": len(players), "games": rec.games, "wins": rec.wins, "win_rate": _percent(rec.win_rate)}
        for players, rec in sorted(combos.items(), key=lambda item: (-len(item[0]), -item[1].games, item[0]))
    ]
    role_rows = [
        {"player": player, "role": role, "games": rec.games, "wins": rec.wins, "win_rate": _percent(rec.win_rate)}
        for (player, role), rec in sorted(roles.items())
    ]
    stack_rows = full_stack_rows(appearances)
    stack_players = sorted({key for row in stack_rows for key in row if key not in {"match_id", "started_at", "map", "result"}})
    _write_csv(output / "combinations.csv", ["players", "size", "games", "wins", "win_rate"], combo_rows)
    _write_csv(output / "player_roles.csv", ["player", "role", "games", "wins", "win_rate"], role_rows)
    _write_csv(output / "full_stack_role_matrix.csv", ["match_id", "started_at", "map", "result", *stack_players], stack_rows)
    _write_summary(output / "summary.md", combos, roles, len(appearances))


def _write_summary(path: Path, combos: dict[tuple[str, ...], Record], roles: dict[tuple[str, str], Record], appearances: int) -> None:
    best_combos = sorted(((players, rec) for players, rec in combos.items() if len(players) >= 2), key=lambda item: (-item[1].games, -item[1].win_rate, item[0]))[:10]
    lines = ["# Valorant team report", "", f"Tracked team appearances: **{appearances}**", "", "## Most played combinations", "", "| Players | Games | Wins | Win rate |", "| --- | ---: | ---: | ---: |"]
    lines.extend(f"| {' + '.join(players)} | {rec.games} | {rec.wins} | {_percent(rec.win_rate)} |" for players, rec in best_combos)
    lines.extend(["", "## Player roles", "", "| Player | Role | Games | Wins | Win rate |", "| --- | --- | ---: | ---: | ---: |"])
    lines.extend(f"| {player} | {role} | {rec.games} | {rec.wins} | {_percent(rec.win_rate)} |" for (player, role), rec in sorted(roles.items()))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
