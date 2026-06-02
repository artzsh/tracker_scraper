from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser

from .agents import role_for_agent
from .models import Participant


@dataclass
class _Row:
    team: str
    agent: str | None = None
    username: str = ""
    discriminator: str = ""


class _ScoreboardParser(HTMLParser):
    def __init__(self, teams: tuple[str, ...]) -> None:
        super().__init__(convert_charrefs=True)
        self.teams = teams
        self.participants: list[Participant] = []
        self._stack: list[tuple[set[str], bool]] = []
        self._content_teams: list[str] = []
        self._content_count = 0
        self._row: _Row | None = None
        self._text_target: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        classes = set((attributes.get("class") or "").split())
        opened_content = "st-content" in classes
        if opened_content:
            if self._content_count >= len(self.teams):
                raise ValueError("HTML contains more scoreboard sections than --teams values")
            self._content_teams.append(self.teams[self._content_count])
            self._content_count += 1
        self._stack.append((classes, opened_content))

        if "st-content__item" in classes and self._content_teams:
            self._finish_row()
            self._row = _Row(team=self._content_teams[-1])
        if self._row is None:
            return
        if tag == "img" and not self._row.agent:
            src = attributes.get("src") or ""
            if "valorant-api%2Fagents%2F" in src or "/valorant-api/agents/" in src:
                self._row.agent = attributes.get("alt") or "unknown"
        if "trn-ign__username" in classes:
            self._text_target = "username"
        elif "trn-ign__discriminator" in classes:
            self._text_target = "discriminator"

    def handle_endtag(self, tag: str) -> None:
        if not self._stack:
            return
        classes, opened_content = self._stack.pop()
        if "trn-ign__username" in classes or "trn-ign__discriminator" in classes:
            self._text_target = None
        if "st-content__item" in classes:
            self._finish_row()
        if opened_content:
            self._content_teams.pop()

    def handle_data(self, data: str) -> None:
        if self._row is None or self._text_target is None:
            return
        if self._text_target == "username":
            self._row.username += data
        else:
            self._row.discriminator += data

    def close(self) -> None:
        super().close()
        self._finish_row()

    def _finish_row(self) -> None:
        if self._row and self._row.agent and self._row.username.strip():
            riot_id = f"{self._row.username.strip()}{self._row.discriminator.strip()}"
            self.participants.append(
                Participant(
                    riot_id=riot_id,
                    team=self._row.team,
                    agent=self._row.agent,
                    role=role_for_agent(self._row.agent),
                )
            )
        self._row = None
        self._text_target = None


def parse_scoreboard_html(html: str, teams: tuple[str, ...] = ("blue", "red")) -> tuple[Participant, ...]:
    """Parse manually copied Tracker.gg scoreboard HTML without making web requests."""
    if not teams:
        raise ValueError("At least one team label is required")
    parser = _ScoreboardParser(teams)
    parser.feed(html)
    parser.close()
    if not parser.participants:
        raise ValueError("No scoreboard players found in HTML")
    riot_ids = [participant.riot_id.casefold() for participant in parser.participants]
    if len(riot_ids) != len(set(riot_ids)):
        raise ValueError("A player appears more than once; copy each scoreboard section exactly once")
    return tuple(parser.participants)
