"""Valorant agent-to-role mapping used by manual scoreboard imports."""

AGENT_ROLES: dict[str, str] = {
    # Controllers
    "astra": "controller",
    "brimstone": "controller",
    "clove": "controller",
    "harbor": "controller",
    "miks": "controller",
    "omen": "controller",
    "viper": "controller",
    # Duelists
    "iso": "duelist",
    "jett": "duelist",
    "neon": "duelist",
    "phoenix": "duelist",
    "raze": "duelist",
    "reyna": "duelist",
    "waylay": "duelist",
    "yoru": "duelist",
    # Initiators
    "breach": "initiator",
    "fade": "initiator",
    "gekko": "initiator",
    "kay/o": "initiator",
    "skye": "initiator",
    "sova": "initiator",
    "tejo": "initiator",
    # Sentinels
    "chamber": "sentinel",
    "cypher": "sentinel",
    "deadlock": "sentinel",
    "killjoy": "sentinel",
    "sage": "sentinel",
    "veto": "sentinel",
    "vyse": "sentinel",
}


def role_for_agent(agent: str) -> str:
    """Return a normalized role while keeping imports usable for future agents."""
    return AGENT_ROLES.get(agent.strip().casefold(), "unknown")
