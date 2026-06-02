from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from .html_import import parse_scoreboard_html
from .io import load_matches_if_exists, write_matches
from .models import Match


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import a manually saved Tracker.gg scoreboard HTML fragment.")
    parser.add_argument("--html", type=Path, required=True, help="UTF-8 HTML fragment copied from one match scoreboard")
    parser.add_argument("--output", type=Path, default=Path("data/matches.json"))
    parser.add_argument("--match-id", required=True, help="Stable unique ID or URL slug for the match")
    parser.add_argument("--act-id", required=True, help="Act UUID also listed in team.json")
    parser.add_argument("--started-at", required=True, help="ISO timestamp, for example 2026-05-31T18:30:00Z")
    parser.add_argument("--map", dest="map_name", required=True)
    parser.add_argument("--winning-team", choices=("blue", "red"), required=True)
    parser.add_argument("--teams", nargs="+", default=("blue", "red"), help="Labels for scoreboard sections in HTML order")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    match = Match(
        match_id=args.match_id,
        act_id=args.act_id,
        started_at=datetime.fromisoformat(args.started_at.replace("Z", "+00:00")),
        map_name=args.map_name,
        winning_team=args.winning_team,
        participants=parse_scoreboard_html(args.html.read_text(encoding="utf-8"), tuple(args.teams)),
    )
    matches = load_matches_if_exists(args.output)
    matches_by_id = {existing.match_id: existing for existing in matches}
    matches_by_id[match.match_id] = match
    write_matches(args.output, matches_by_id.values())
    print(f"Imported {match.match_id}: {len(match.participants)} players. Stored {len(matches_by_id)} matches in {args.output}")


if __name__ == "__main__":
    main()
