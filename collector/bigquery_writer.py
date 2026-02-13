"""Write Minecraft events and stats to BigQuery using batch loads (free tier compatible)."""

from dataclasses import asdict

from google.cloud import bigquery

from config import settings
from schemas.bigquery_schemas import EVENTS_SCHEMA, PLAYER_STATS_SCHEMA

from .log_parser import GameEvent
from .stats_reader import PlayerStats


def get_client() -> bigquery.Client:
    return bigquery.Client(project=settings.gcp_project_id)


def ensure_dataset_and_tables(client: bigquery.Client) -> None:
    """Create dataset and tables if they don't exist."""
    dataset_ref = f"{settings.gcp_project_id}.{settings.bq_dataset}"
    dataset = bigquery.Dataset(dataset_ref)
    client.create_dataset(dataset, exists_ok=True)

    events_ref = f"{dataset_ref}.{settings.bq_events_table}"
    events_table = bigquery.Table(events_ref, schema=EVENTS_SCHEMA)
    client.create_table(events_table, exists_ok=True)

    stats_ref = f"{dataset_ref}.{settings.bq_player_stats_table}"
    stats_table = bigquery.Table(stats_ref, schema=PLAYER_STATS_SCHEMA)
    client.create_table(stats_table, exists_ok=True)


def _batch_load(client: bigquery.Client, table_id: str, rows: list[dict], schema: list) -> int:
    """Load rows into BigQuery using a batch load job (free tier compatible)."""
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
    )
    job = client.load_table_from_json(rows, table_id, job_config=job_config)
    job.result()  # wait for completion
    return len(rows)


def write_events(client: bigquery.Client, events: list[GameEvent]) -> int:
    """Insert game events into BigQuery. Returns number of rows inserted."""
    if not events:
        return 0

    table_id = f"{settings.gcp_project_id}.{settings.bq_dataset}.{settings.bq_events_table}"
    rows = []
    for e in events:
        row = asdict(e)
        row["timestamp"] = e.timestamp.isoformat()
        rows.append(row)

    return _batch_load(client, table_id, rows, EVENTS_SCHEMA)


def write_player_stats(
    client: bigquery.Client, stats: list[PlayerStats]
) -> int:
    """Insert player stat snapshots into BigQuery. Returns number of rows inserted."""
    if not stats:
        return 0

    table_id = f"{settings.gcp_project_id}.{settings.bq_dataset}.{settings.bq_player_stats_table}"
    rows = []
    for s in stats:
        row = asdict(s)
        row["snapshot_time"] = s.snapshot_time.isoformat()
        rows.append(row)

    return _batch_load(client, table_id, rows, PLAYER_STATS_SCHEMA)
