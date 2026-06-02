import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from tracker_scraper.import_cli import main


FIXTURE = Path(__file__).parent / "fixtures" / "scoreboard.html"


class ImportCliTest(unittest.TestCase):
    def test_imports_and_replaces_match_by_id(self) -> None:
        with TemporaryDirectory() as directory:
            output = Path(directory) / "matches.json"
            args = [
                "tracker-import-html", "--html", str(FIXTURE), "--output", str(output),
                "--match-id", "match-1", "--act-id", "act-a", "--started-at", "2026-05-31T18:30:00Z",
                "--map", "Ascent", "--winning-team", "blue",
            ]
            with patch("sys.argv", args):
                main()
            with patch("sys.argv", [*args[:-1], "red"]):
                main()
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(len(payload["matches"]), 1)
            self.assertEqual(payload["matches"][0]["winning_team"], "red")
            self.assertEqual(payload["matches"][0]["participants"][0]["role"], "duelist")


if __name__ == "__main__":
    unittest.main()
