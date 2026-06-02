from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from email import policy
from email.parser import BytesParser
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

from .agents import role_for_agent
from .config import Config

CSV_FIELDS = (
    "match_id", "started_at", "mode", "map", "duration", "average_rank",
    "team", "team_score", "opponent_score", "score", "result", "player",
    "riot_id", "agent", "role", "account_level", "match_rank", "trs", "acs",
    "kills", "deaths", "assists", "kd_diff", "kd", "damage_delta", "adr",
    "headshot_pct", "kast_pct", "first_kills", "first_deaths", "multikills",
)
STAT_FIELDS = (
    "trs", "acs", "kills", "deaths", "assists", "kd_diff", "kd",
    "damage_delta", "adr", "headshot_pct", "kast_pct", "first_kills",
    "first_deaths", "multikills",
)
VOID_TAGS = {"area", "base", "br", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}


@dataclass
class _Node:
    tag: str = ""
    attrs: dict[str, str | None] | None = None
    parent: "_Node | None" = None

    def __post_init__(self) -> None:
        self.children: list[_Node] = []
        self.fragments: list[str | _Node] = []
        if self.parent:
            self.parent.children.append(self)
            self.parent.fragments.append(self)

    @property
    def classes(self) -> set[str]:
        return set(((self.attrs or {}).get("class") or "").split())

    @property
    def text(self) -> str:
        return "".join(fragment.text if isinstance(fragment, _Node) else fragment for fragment in self.fragments).strip()

    def walk(self):
        yield self
        for child in self.children:
            yield from child.walk()

    def find_all(self, class_name: str | None = None, tag: str | None = None) -> list["_Node"]:
        return [node for node in self.walk() if (class_name is None or class_name in node.classes) and (tag is None or node.tag == tag)]

    def find(self, class_name: str | None = None, tag: str | None = None) -> "_Node | None":
        return next(iter(self.find_all(class_name, tag)), None)


class _DomParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = _Node()
        self.current = self.root

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = _Node(tag=tag, attrs=dict(attrs), parent=self.current)
        if tag not in VOID_TAGS:
            self.current = node

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        _Node(tag=tag, attrs=dict(attrs), parent=self.current)

    def handle_endtag(self, tag: str) -> None:
        node = self.current
        while node.parent:
            if node.tag == tag:
                self.current = node.parent
                return
            node = node.parent

    def handle_data(self, data: str) -> None:
        self.current.fragments.append(data)


@dataclass(frozen=True)
class ParsedMatch:
    match_id: str
    rows: tuple[dict[str, str], ...]


def _clean(value: str) -> str:
    return " ".join(value.split())


def _html_part(path: Path) -> tuple[str, str]:
    message = BytesParser(policy=policy.default).parsebytes(path.read_bytes())
    for part in message.walk():
        if part.get_content_type() == "text/html":
            payload = part.get_payload(decode=True)
            if payload is None:
                break
            charset = part.get_content_charset() or "utf-8"
            return payload.decode(charset, errors="replace"), str(part.get("Content-Location") or message.get("Snapshot-Content-Location") or "")
    raise ValueError("MHTML does not contain a text/html page")


def _match_id(location: str) -> str:
    match = re.search(r"/valorant/match/([^/?#]+)", urlparse(location).path)
    if not match:
        raise ValueError("Cannot find match ID in MHTML Content-Location")
    return match.group(1)


def _image_alt(row: _Node, marker: str) -> str:
    for image in row.find_all(tag="img"):
        attrs = image.attrs or {}
        if marker in str(attrs.get("src") or ""):
            return str(attrs.get("alt") or "")
    return ""


def _header_metadata(root: _Node) -> dict[str, str]:
    info = root.find("vm-header-info")
    score = root.find("vm-header-score")
    time = root.find("vm-header-time")
    rank = root.find("vm-header-rank")
    if not info or not score or not time:
        raise ValueError("Cannot find match header in HTML")
    info_values = [_clean(node.text) for node in info.find_all("trn-match-drawer__header-value")]
    score_blocks = [node for node in score.children if "trn-match-drawer__header-block" in node.classes]
    scores: dict[str, str] = {}
    for block in score_blocks:
        label = block.find("trn-match-drawer__header-label")
        value = block.find("trn-match-drawer__header-value")
        if label and value and _clean(label.text) in {"Team A", "Team B"}:
            scores[_clean(label.text)] = _clean(value.text)
    time_labels = time.find_all("trn-match-drawer__header-label")
    time_values = time.find_all("trn-match-drawer__header-value")
    return {
        "mode": _clean(info.find("trn-match-drawer__header-label").text),
        "map": info_values[0] if info_values else "",
        "started_at": _clean(time_labels[0].text) if time_labels else "",
        "duration": _clean(time_values[0].text) if time_values else "",
        "average_rank": _clean(rank.find("trn-match-drawer__header-value").text) if rank and rank.find("trn-match-drawer__header-value") else "",
        "Team A": scores.get("Team A", ""),
        "Team B": scores.get("Team B", ""),
    }


def _scoreboard_rows(root: _Node) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for table in [node for node in root.walk() if "st-valorant-team" in node.classes]:
        header = table.find("st-header")
        if not header:
            continue
        header_text = _clean(header.text)
        team_match = re.search(r"Team [AB]", header_text)
        if not team_match:
            continue
        team = team_match.group(0)
        content = table.find("st-content")
        if not content:
            continue
        for row in content.find_all("st-content__item"):
            username = row.find("trn-ign__username")
            discriminator = row.find("trn-ign__discriminator")
            if not username or not discriminator:
                continue
            cells = [node for node in row.children if "st-content__item-value" in node.classes]
            values = []
            for cell in cells[2:]:
                value = cell.find("value")
                values.append(_clean(value.text) if value else "")
            values += [""] * (len(STAT_FIELDS) - len(values))
            level = row.find("level-box")
            agent = _image_alt(row, "valorant-api%2Fagents%2F") or _image_alt(row, "/valorant-api/agents/")
            riot_id = f"{_clean(username.text)}{_clean(discriminator.text)}"
            item = {
                "team": team,
                "riot_id": riot_id,
                "agent": agent,
                "role": role_for_agent(agent),
                "account_level": _clean(level.text) if level else "",
                "match_rank": _image_alt(row, "tiersv2%2F"),
            }
            item.update(dict(zip(STAT_FIELDS, values, strict=False)))
            if not item["kd_diff"] and item["kills"].lstrip("+-").isdigit() and item["deaths"].lstrip("+-").isdigit():
                item["kd_diff"] = str(int(item["kills"]) - int(item["deaths"]))
            rows.append(item)
    if not rows:
        raise ValueError("Cannot find scoreboard rows in HTML")
    return rows


def parse_mhtml(path: Path, config: Config) -> ParsedMatch:
    html, location = _html_part(path)
    parser = _DomParser()
    parser.feed(html)
    metadata = _header_metadata(parser.root)
    match_id = _match_id(location)
    output: list[dict[str, str]] = []
    opponents = {"Team A": "Team B", "Team B": "Team A"}
    for row in _scoreboard_rows(parser.root):
        player = next((player for player in config.players if player.matches(row["riot_id"])), None)
        if not player:
            continue
        opponent = opponents[row["team"]]
        team_score = metadata[row["team"]]
        opponent_score = metadata[opponent]
        result = "win" if int(team_score) > int(opponent_score) else "loss"
        output.append({
            "match_id": match_id,
            **{key: metadata[key] for key in ("started_at", "mode", "map", "duration", "average_rank")},
            "team": row["team"],
            "team_score": team_score,
            "opponent_score": opponent_score,
            "score": f"{team_score}:{opponent_score}",
            "result": result,
            "player": player.riot_id,
            **row,
        })
    if not output:
        raise ValueError("Scoreboard contains no configured team players")
    return ParsedMatch(match_id=match_id, rows=tuple(output))


def existing_match_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != CSV_FIELDS:
            raise ValueError(f"Existing CSV has an unexpected header: {path}")
        return {row["match_id"] for row in reader if row.get("match_id")}


def append_matches(path: Path, matches: list[ParsedMatch]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    with path.open("a", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS, extrasaction="ignore")
        if not exists:
            writer.writeheader()
        for match in matches:
            writer.writerows(match.rows)
    return sum(len(match.rows) for match in matches)
