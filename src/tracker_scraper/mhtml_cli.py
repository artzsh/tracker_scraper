from __future__ import annotations

import argparse
from pathlib import Path

from .config import Config
from .mhtml_import import append_matches, existing_match_ids, parse_mhtml


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import a folder of manually saved Tracker.gg match MHTML pages into a team CSV file.")
    parser.add_argument("--input", type=Path, required=True, help="Folder containing .mhtml or .mht files")
    parser.add_argument("--config", type=Path, default=Path("team.json"))
    parser.add_argument("--output", type=Path, default=Path("data/team_matches.csv"))
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = Config.load(args.config)
    files = sorted(path for path in args.input.rglob("*") if path.is_file() and path.suffix.casefold() in {".mhtml", ".mht"})
    known_ids = existing_match_ids(args.output)
    imported = []
    skipped = 0
    failed = 0
    for path in files:
        try:
            match = parse_mhtml(path, config)
        except ValueError as error:
            failed += 1
            print(f"ERROR {path.name}: {error}")
            continue
        if match.match_id in known_ids:
            skipped += 1
            print(f"SKIP  {path.name}: match {match.match_id} already imported")
            continue
        known_ids.add(match.match_id)
        imported.append(match)
        print(f"ADD   {path.name}: match {match.match_id}, {len(match.rows)} team players")
    rows = append_matches(args.output, imported)
    print(f"Done: {len(imported)} matches added, {rows} player rows written, {skipped} duplicate matches skipped, {failed} files failed. CSV: {args.output}")


if __name__ == "__main__":
    main()
