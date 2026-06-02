import csv
from email.message import EmailMessage
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tracker_scraper.config import Config
from tracker_scraper.mhtml_import import append_matches, existing_match_ids, parse_mhtml
from tracker_scraper.models import Player


HTML = """
<div class="trn-match-drawer__header vm-header">
  <div class="vm-header-info"><div class="trn-match-drawer__header-label">Competitive</div><div class="trn-match-drawer__header-value">Split</div></div>
  <div class="vm-header-score">
    <div class="trn-match-drawer__header-block"><div class="trn-match-drawer__header-label">Team A</div><div class="trn-match-drawer__header-value">6</div></div>
    <div class="trn-match-drawer__header-block"><div class="trn-match-drawer__header-label">Team B</div><div class="trn-match-drawer__header-value">13</div></div>
  </div>
  <div class="vm-header-time"><div class="trn-match-drawer__header-label">30.05.2026, 23:38</div><div class="trn-match-drawer__header-value">29m 28s</div></div>
  <div class="vm-header-rank"><div class="trn-match-drawer__header-value">Platinum III</div></div>
</div>
<div class="st st-valorant-team st-valorant-team-Red">
  <div class="st-header">Team A</div><div class="st-content"><div class="st-content__item">
    <div class="st-content__item-value"><img src="https://titles.trackercdn.com/valorant-api/agents/a/displayicon.png" alt="Raze"><div class="level-box">131</div><span class="trn-ign__username">Alt</span><span class="trn-ign__discriminator"> #ONE</span><img src="tiersv2%2F16.png" alt="Platinum 2"></div>
    <div class="st-content__item-value"></div>
    <div class="st-content__item-value"><div class="value">624</div></div><div class="st-content__item-value"><div class="value">279</div></div><div class="st-content__item-value"><div class="value">17</div></div><div class="st-content__item-value"><div class="value">19</div></div><div class="st-content__item-value"><div class="value">3</div></div><div class="st-content__item-value"><div class="value">-2</div></div><div class="st-content__item-value"><div class="value">0.9</div></div><div class="st-content__item-value"><div class="value">+10</div></div><div class="st-content__item-value"><div class="value">180.6</div></div><div class="st-content__item-value"><div class="value">13%</div></div><div class="st-content__item-value"><div class="value">74%</div></div><div class="st-content__item-value"><div class="value">3</div></div><div class="st-content__item-value"><div class="value">1</div></div><div class="st-content__item-value"><div class="value">2</div></div>
  </div></div>
</div>
<div class="st st-valorant-team st-valorant-team-Blue">
  <div class="st-header">Team B</div><div class="st-content"><div class="st-content__item">
    <div class="st-content__item-value"><img src="https://titles.trackercdn.com/valorant-api/agents/b/displayicon.png" alt="Viper"><span class="trn-ign__username">Enemy</span><span class="trn-ign__discriminator"> #RED</span></div>
  </div></div>
</div>
"""


def write_mhtml(path: Path, match_id: str = "match-001") -> None:
    message = EmailMessage()
    message["Snapshot-Content-Location"] = f"https://tracker.gg/valorant/match/{match_id}"
    message.set_content(HTML, subtype="html", charset="utf-8")
    path.write_bytes(message.as_bytes())


class MhtmlImportTest(unittest.TestCase):
    def setUp(self) -> None:
        self.config = Config(acts=(), players=(Player("Main#ONE", ("Alt#ONE",)),))

    def test_parses_match_metadata_scoreboard_stats_and_alias(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "match.mhtml"
            write_mhtml(path)
            match = parse_mhtml(path, self.config)
        self.assertEqual(match.match_id, "match-001")
        self.assertEqual(len(match.rows), 1)
        row = match.rows[0]
        self.assertEqual(row["map"], "Split")
        self.assertEqual(row["score"], "6:13")
        self.assertEqual(row["result"], "loss")
        self.assertEqual(row["player"], "Main#ONE")
        self.assertEqual(row["riot_id"], "Alt#ONE")
        self.assertEqual(row["agent"], "Raze")
        self.assertEqual(row["role"], "duelist")
        self.assertEqual(row["acs"], "279")
        self.assertEqual(row["kills"], "17")
        self.assertEqual(row["deaths"], "19")
        self.assertEqual(row["assists"], "3")
        self.assertEqual(row["adr"], "180.6")

    def test_appends_csv_header_and_detects_existing_match(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            mhtml = root / "match.mhtml"
            output = root / "team_matches.csv"
            write_mhtml(mhtml)
            match = parse_mhtml(mhtml, self.config)
            self.assertEqual(append_matches(output, [match]), 1)
            self.assertEqual(existing_match_ids(output), {"match-001"})
            with output.open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["match_id"], "match-001")


if __name__ == "__main__":
    unittest.main()
