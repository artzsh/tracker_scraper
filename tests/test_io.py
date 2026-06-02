import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tracker_scraper.io import load_matches


class LoadMatchesTest(unittest.TestCase):
    def test_deduplicates_match_ids_from_multiple_profile_exports(self) -> None:
        match = {
            "match_id": "shared-match",
            "act_id": "act-a",
            "started_at": "2026-01-01T00:00:00Z",
            "winning_team": "blue",
            "participants": [],
        }
        with TemporaryDirectory() as directory:
            path = Path(directory) / "matches.json"
            path.write_text(json.dumps({"matches": [match, match]}), encoding="utf-8")
            self.assertEqual(len(load_matches(path)), 1)


if __name__ == "__main__":
    unittest.main()
