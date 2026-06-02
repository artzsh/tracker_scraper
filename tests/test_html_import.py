from pathlib import Path
import unittest

from tracker_scraper.agents import AGENT_ROLES, role_for_agent
from tracker_scraper.html_import import parse_scoreboard_html


FIXTURE = Path(__file__).parent / "fixtures" / "scoreboard.html"


class HtmlImportTest(unittest.TestCase):
    def test_parses_players_agents_teams_and_roles(self) -> None:
        participants = parse_scoreboard_html(FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(
            [(item.riot_id, item.team, item.agent, item.role) for item in participants],
            [
                ("aww#dead", "blue", "Raze", "duelist"),
                ("BECHA#NRG", "blue", "Viper", "controller"),
                ("Enemy One#RED", "red", "Miks", "controller"),
                ("Enemy Two#RED", "red", "New Agent", "unknown"),
            ],
        )

    def test_rejects_accidentally_copied_duplicate_sections(self) -> None:
        html = FIXTURE.read_text(encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "more than once"):
            parse_scoreboard_html(html + html, ("blue", "red", "blue", "red"))

    def test_current_agent_mapping_has_four_roles(self) -> None:
        self.assertEqual(set(AGENT_ROLES.values()), {"controller", "duelist", "initiator", "sentinel"})
        self.assertEqual(role_for_agent("Sage"), "sentinel")
        self.assertEqual(role_for_agent("future agent"), "unknown")


if __name__ == "__main__":
    unittest.main()
