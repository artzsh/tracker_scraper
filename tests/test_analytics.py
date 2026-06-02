from datetime import datetime, timezone
import unittest

from tracker_scraper.analytics import combination_records, full_stack_rows, role_records, team_appearances
from tracker_scraper.config import Config
from tracker_scraper.models import Match, Participant, Player


class AnalyticsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.config = Config(
            acts=("act-a",),
            players=(Player("Main#ONE", ("Alt#ONE",)), Player("Friend#TWO")),
        )
        self.match = Match(
            match_id="match-1",
            act_id="act-a",
            started_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            map_name="Ascent",
            winning_team="blue",
            participants=(
                Participant("alt#one", "blue", "Omen", "controller"),
                Participant("Friend#TWO", "blue", "Jett", "duelist"),
                Participant("Enemy#RED", "red", "Sage", "sentinel"),
            ),
        )

    def test_alias_is_merged_into_canonical_player(self) -> None:
        appearances = team_appearances([self.match], self.config)
        self.assertEqual(len(appearances), 1)
        self.assertEqual([player.riot_id for player, _ in appearances[0].members], ["Friend#TWO", "Main#ONE"])
        self.assertTrue(appearances[0].won)

    def test_combinations_include_subsets_and_roles(self) -> None:
        appearances = team_appearances([self.match], self.config)
        combos = combination_records(appearances)
        self.assertEqual(combos[("Friend#TWO", "Main#ONE")].games, 1)
        self.assertEqual(combos[("Main#ONE",)].wins, 1)
        self.assertEqual(role_records(appearances)[("Main#ONE", "controller")].win_rate, 1.0)

    def test_acts_are_filtered(self) -> None:
        excluded = Match(**{**self.match.__dict__, "act_id": "act-b"})
        self.assertEqual(team_appearances([excluded], self.config), [])

    def test_full_stack_requires_five_tracked_players(self) -> None:
        appearances = team_appearances([self.match], self.config)
        self.assertEqual(full_stack_rows(appearances), [])
        self.assertEqual(len(full_stack_rows(appearances, size=2)), 1)


if __name__ == "__main__":
    unittest.main()
