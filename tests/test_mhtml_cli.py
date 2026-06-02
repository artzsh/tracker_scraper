from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from tracker_scraper.mhtml_cli import main
from tracker_scraper.mhtml_import import existing_match_ids
from test_mhtml_import import write_mhtml


class MhtmlCliTest(unittest.TestCase):
    def test_folder_import_skips_duplicate_files_and_existing_csv_matches(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            input_dir = root / "mhtml"
            input_dir.mkdir()
            write_mhtml(input_dir / "profile-a.mhtml")
            write_mhtml(input_dir / "profile-b.mhtml")
            config = root / "team.json"
            config.write_text('{"acts": [], "players": [{"riot_id": "Main#ONE", "aliases": ["Alt#ONE"]}]}', encoding="utf-8")
            output = root / "team_matches.csv"
            args = ["tracker-import-mhtml-folder", "--input", str(input_dir), "--config", str(config), "--output", str(output)]
            with patch("sys.argv", args):
                main()
            with patch("sys.argv", args):
                main()
            self.assertEqual(existing_match_ids(output), {"match-001"})
            self.assertEqual(len(output.read_text(encoding="utf-8-sig").splitlines()), 2)


if __name__ == "__main__":
    unittest.main()
