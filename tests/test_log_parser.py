"""Tests for Minecraft log parser."""

from datetime import date, datetime, time

from collector.log_parser import GameEvent, parse_log_line, parse_log_lines


LOG_DATE = date(2025, 4, 21)


def _make_dt(h: int, m: int, s: int) -> datetime:
    return datetime.combine(LOG_DATE, time(h, m, s))


class TestParseLogLine:
    def test_death_pricked(self):
        line = "[14:08:05] [Server thread/INFO]: Njackisyourdad was pricked to death"
        event = parse_log_line(line, LOG_DATE)
        assert event is not None
        assert event.player == "Njackisyourdad"
        assert event.event_type == "death"
        assert event.timestamp == _make_dt(14, 8, 5)

    def test_death_slain(self):
        line = "[20:15:30] [Server thread/INFO]: Steve was slain by Zombie"
        event = parse_log_line(line, LOG_DATE)
        assert event is not None
        assert event.player == "Steve"
        assert event.event_type == "death"
        assert "slain by" in event.details

    def test_death_fell(self):
        line = "[10:00:00] [Server thread/INFO]: Alex hit the ground too hard"
        event = parse_log_line(line, LOG_DATE)
        assert event is not None
        assert event.player == "Alex"
        assert event.event_type == "death"

    def test_advancement(self):
        line = "[14:08:29] [Server thread/INFO]: Njackisyourdad has made the advancement [Monster Hunter]"
        event = parse_log_line(line, LOG_DATE)
        assert event is not None
        assert event.player == "Njackisyourdad"
        assert event.event_type == "advancement"
        assert event.details == "Monster Hunter"

    def test_challenge(self):
        line = "[15:00:00] [Server thread/INFO]: Steve has completed the challenge [Sniper Duel]"
        event = parse_log_line(line, LOG_DATE)
        assert event is not None
        assert event.event_type == "challenge"
        assert event.details == "Sniper Duel"

    def test_join(self):
        line = "[13:56:10] [Server thread/INFO]: Njackisyourdad joined the game"
        event = parse_log_line(line, LOG_DATE)
        assert event is not None
        assert event.player == "Njackisyourdad"
        assert event.event_type == "join"

    def test_leave(self):
        line = "[14:08:54] [Server thread/INFO]: Njackisyourdad left the game"
        event = parse_log_line(line, LOG_DATE)
        assert event is not None
        assert event.player == "Njackisyourdad"
        assert event.event_type == "leave"

    def test_chat(self):
        line = "[16:00:00] [Server thread/INFO]: <Steve> hello everyone"
        event = parse_log_line(line, LOG_DATE)
        assert event is not None
        assert event.player == "Steve"
        assert event.event_type == "chat"
        assert event.details == "hello everyone"

    def test_warn_ignored(self):
        line = "[13:56:11] [Server thread/WARN]: Can't keep up! Is the server overloaded?"
        event = parse_log_line(line, LOG_DATE)
        assert event is None

    def test_server_startup_ignored(self):
        line = "[13:53:58] [Server thread/INFO]: Starting minecraft server version 1.21.5"
        event = parse_log_line(line, LOG_DATE)
        assert event is None

    def test_uuid_auth_ignored(self):
        line = "[13:56:07] [User Authenticator #1/INFO]: UUID of player Njackisyourdad is 63f167bb-ff0d-4bcb-a09b-ca34f443510b"
        event = parse_log_line(line, LOG_DATE)
        assert event is None  # Not Server thread, so ignored


class TestParseLogLines:
    def test_filters_relevant_events(self):
        lines = [
            "[13:53:58] [Server thread/INFO]: Starting minecraft server version 1.21.5\n",
            "[13:56:10] [Server thread/INFO]: Njackisyourdad joined the game\n",
            "[13:56:11] [Server thread/WARN]: Can't keep up!\n",
            "[14:08:05] [Server thread/INFO]: Njackisyourdad was pricked to death\n",
            "[14:08:29] [Server thread/INFO]: Njackisyourdad has made the advancement [Monster Hunter]\n",
            "[14:08:54] [Server thread/INFO]: Njackisyourdad left the game\n",
        ]
        events = parse_log_lines(lines, LOG_DATE)
        assert len(events) == 4
        assert [e.event_type for e in events] == ["join", "death", "advancement", "leave"]
