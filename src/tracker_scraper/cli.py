from __future__ import annotations

import argparse
from pathlib import Path

from .analytics import team_appearances
from .config import Config
from .io import load_matches
from .report import write_reports


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Valorant team reports from an authorized normalized JSON export.")
    parser.add_argument("--config", type=Path, default=Path("team.json"))
    parser.add_argument("--matches", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("reports"))
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = Config.load(args.config)
    matches = load_matches(args.matches)
    appearances = team_appearances(matches, config)
    write_reports(appearances, args.output)
    print(f"Wrote reports for {len(appearances)} tracked team appearances to {args.output}")


if __name__ == "__main__":
    main()
