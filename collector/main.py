"""Collector entry point: reads logs + stats, writes to BigQuery on a loop."""

import sys
import time

from config import settings

from .bigquery_writer import (
    ensure_dataset_and_tables,
    get_client,
    write_events,
    write_item_stat_details,
    write_mob_kill_details,
    write_player_stats,
)
from .log_parser import parse_log_lines, read_log_from_offset
from .stats_reader import read_player_stats


def load_offset() -> int:
    """Load the last-read byte offset from disk."""
    if settings.log_offset_file.exists():
        return int(settings.log_offset_file.read_text().strip())
    return 0


def save_offset(offset: int) -> None:
    settings.log_offset_file.write_text(str(offset))


def collect_once() -> None:
    """Run a single collection cycle: parse new log lines + read stats, write to BQ."""
    client = get_client()
    ensure_dataset_and_tables(client)

    # Parse new log events
    offset = load_offset()
    new_lines, new_offset = read_log_from_offset(
        settings.resolved_log_file, offset
    )
    events = parse_log_lines(new_lines)
    n_events = write_events(client, events)
    save_offset(new_offset)

    # Read player stats snapshot
    stats, mob_details, item_details = read_player_stats(
        settings.resolved_stats_dir, settings.resolved_usercache_file
    )
    n_stats = write_player_stats(client, stats)
    n_mob = write_mob_kill_details(client, mob_details)
    n_items = write_item_stat_details(client, item_details)

    print(
        f"Collected {n_events} events, {n_stats} stat snapshots, "
        f"{n_mob} mob details, {n_items} item details",
        flush=True,
    )


def main() -> None:
    """Run collector in a loop."""
    print(f"Starting collector (interval={settings.collect_interval_seconds}s)")
    print(f"Server dir: {settings.server_dir}")
    print(f"Log file: {settings.resolved_log_file}")
    print(f"BigQuery: {settings.gcp_project_id}.{settings.bq_dataset}")

    while True:
        try:
            collect_once()
        except KeyboardInterrupt:
            print("\nStopping collector.")
            sys.exit(0)
        except Exception as e:
            print(f"Error during collection: {e}", file=sys.stderr)

        time.sleep(settings.collect_interval_seconds)


if __name__ == "__main__":
    main()
