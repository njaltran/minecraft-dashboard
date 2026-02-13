"""Parse Minecraft server latest.log for game events."""

import re
from dataclasses import dataclass
from datetime import date, datetime, time
from pathlib import Path

# Matches: [HH:MM:SS] [Thread/LEVEL]: message
LOG_LINE_RE = re.compile(
    r"\[(\d{2}:\d{2}:\d{2})\] \[([^/]+)/(\w+)\]: (.+)"
)

# Death messages contain the player name followed by a death reason.
# Vanilla death messages always start with the player name.
# Full list: https://minecraft.wiki/w/Death_messages
DEATH_KEYWORDS = [
    "was shot by", "was pummeled by", "was pricked to death",
    "walked into a cactus", "drowned", "experienced kinetic energy",
    "blew up", "was blown up by", "was killed by", "hit the ground too hard",
    "fell from a high place", "fell off", "fell while", "was squashed by",
    "was fireballed by", "was killed trying to hurt",
    "walked into fire", "went up in flames", "burned to death",
    "was burnt to a crisp", "tried to swim in lava",
    "suffocated in a wall", "was squished",
    "starved to death", "was poked to death by",
    "was impaled on a stalagmite", "was skewered by",
    "withered away", "was stung to death",
    "was slain by", "was killed by",
    "died", "was doomed to fall",
]

ADVANCEMENT_RE = re.compile(r"^(\w+) has made the advancement \[(.+)\]$")
CHALLENGE_RE = re.compile(r"^(\w+) has completed the challenge \[(.+)\]$")
GOAL_RE = re.compile(r"^(\w+) has reached the goal \[(.+)\]$")
JOIN_RE = re.compile(r"^(\w+) joined the game$")
LEAVE_RE = re.compile(r"^(\w+) left the game$")
CHAT_RE = re.compile(r"^<(\w+)> (.+)$")


@dataclass
class GameEvent:
    timestamp: datetime
    player: str
    event_type: str  # death, advancement, challenge, goal, join, leave, chat
    details: str
    raw_message: str


def parse_death(message: str) -> tuple[str, str] | None:
    """Extract player and death reason from a death message."""
    for keyword in DEATH_KEYWORDS:
        if keyword in message:
            # Player name is everything before the keyword
            idx = message.index(keyword)
            player = message[:idx].strip()
            if player and " " not in player:  # valid MC username has no spaces
                return player, message
    return None


def parse_log_line(line: str, log_date: date | None = None) -> GameEvent | None:
    """Parse a single log line into a GameEvent, or None if not relevant."""
    match = LOG_LINE_RE.match(line.strip())
    if not match:
        return None

    time_str, _thread, level, message = match.groups()

    if level != "INFO":
        return None

    log_time = time.fromisoformat(time_str)
    dt = datetime.combine(log_date or date.today(), log_time)

    # Check each event type
    if m := ADVANCEMENT_RE.match(message):
        return GameEvent(dt, m.group(1), "advancement", m.group(2), message)

    if m := CHALLENGE_RE.match(message):
        return GameEvent(dt, m.group(1), "challenge", m.group(2), message)

    if m := GOAL_RE.match(message):
        return GameEvent(dt, m.group(1), "goal", m.group(2), message)

    if m := JOIN_RE.match(message):
        return GameEvent(dt, m.group(1), "join", "", message)

    if m := LEAVE_RE.match(message):
        return GameEvent(dt, m.group(1), "leave", "", message)

    if m := CHAT_RE.match(message):
        return GameEvent(dt, m.group(1), "chat", m.group(2), message)

    if death := parse_death(message):
        player, reason = death
        return GameEvent(dt, player, "death", reason, message)

    return None


def parse_log_lines(
    lines: list[str], log_date: date | None = None
) -> list[GameEvent]:
    """Parse multiple log lines, returning only recognized game events."""
    events = []
    for line in lines:
        event = parse_log_line(line, log_date)
        if event:
            events.append(event)
    return events


def read_log_from_offset(
    log_path: Path, offset: int = 0
) -> tuple[list[str], int]:
    """Read new lines from log file starting at byte offset.

    Returns (new_lines, new_offset).
    If file is smaller than offset (log rotated), reads from beginning.
    """
    if not log_path.exists():
        return [], offset

    file_size = log_path.stat().st_size
    if file_size < offset:
        # Log was rotated, start from beginning
        offset = 0

    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
        f.seek(offset)
        new_lines = f.readlines()
        new_offset = f.tell()

    return new_lines, new_offset
