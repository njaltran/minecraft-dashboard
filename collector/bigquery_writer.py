"""Write Minecraft events and stats to BigQuery using batch loads (free tier compatible)."""

from dataclasses import asdict

from google.cloud import bigquery

from config import settings
from schemas.bigquery_schemas import (
    EVENTS_SCHEMA,
    ITEM_STATS_DETAIL_SCHEMA,
    MOB_KILLS_DETAIL_SCHEMA,
    PLAYER_STATS_SCHEMA,
)

from .log_parser import GameEvent
from .stats_reader import ItemStatDetail, MobKillDetail, PlayerStats

BQ_MOB_KILLS_DETAIL_TABLE = "mob_kills_detail"
BQ_ITEM_STATS_DETAIL_TABLE = "item_stats_detail"


def get_client() -> bigquery.Client:
    return bigquery.Client(project=settings.gcp_project_id)


def ensure_dataset_and_tables(client: bigquery.Client) -> None:
    """Create dataset and tables if they don't exist."""
    dataset_ref = f"{settings.gcp_project_id}.{settings.bq_dataset}"
    dataset = bigquery.Dataset(dataset_ref)
    client.create_dataset(dataset, exists_ok=True)

    tables = {
        settings.bq_events_table: EVENTS_SCHEMA,
        settings.bq_player_stats_table: PLAYER_STATS_SCHEMA,
        BQ_MOB_KILLS_DETAIL_TABLE: MOB_KILLS_DETAIL_SCHEMA,
        BQ_ITEM_STATS_DETAIL_TABLE: ITEM_STATS_DETAIL_SCHEMA,
    }
    for table_name, schema in tables.items():
        table_id = f"{dataset_ref}.{table_name}"
        table = bigquery.Table(table_id, schema=schema)
        client.create_table(table, exists_ok=True)


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


def _serialize_datetime_rows(rows: list[dict], time_field: str) -> list[dict]:
    """Convert datetime fields to ISO format strings for JSON serialization."""
    for row in rows:
        if time_field in row:
            row[time_field] = row[time_field].isoformat()
    return rows


def write_events(client: bigquery.Client, events: list[GameEvent]) -> int:
    """Insert game events into BigQuery. Returns number of rows inserted."""
    if not events:
        return 0

    table_id = f"{settings.gcp_project_id}.{settings.bq_dataset}.{settings.bq_events_table}"
    rows = _serialize_datetime_rows([asdict(e) for e in events], "timestamp")
    return _batch_load(client, table_id, rows, EVENTS_SCHEMA)


def write_player_stats(client: bigquery.Client, stats: list[PlayerStats]) -> int:
    """Insert player stat snapshots into BigQuery. Returns number of rows inserted."""
    if not stats:
        return 0

    table_id = f"{settings.gcp_project_id}.{settings.bq_dataset}.{settings.bq_player_stats_table}"
    rows = _serialize_datetime_rows([asdict(s) for s in stats], "snapshot_time")
    return _batch_load(client, table_id, rows, PLAYER_STATS_SCHEMA)


def write_mob_kill_details(client: bigquery.Client, details: list[MobKillDetail]) -> int:
    """Insert per-entity kill/killed_by breakdowns. Returns number of rows inserted."""
    if not details:
        return 0

    table_id = f"{settings.gcp_project_id}.{settings.bq_dataset}.{BQ_MOB_KILLS_DETAIL_TABLE}"
    rows = _serialize_datetime_rows([asdict(d) for d in details], "snapshot_time")
    return _batch_load(client, table_id, rows, MOB_KILLS_DETAIL_SCHEMA)


def write_item_stat_details(client: bigquery.Client, details: list[ItemStatDetail]) -> int:
    """Insert per-item breakdowns. Returns number of rows inserted."""
    if not details:
        return 0

    table_id = f"{settings.gcp_project_id}.{settings.bq_dataset}.{BQ_ITEM_STATS_DETAIL_TABLE}"
    rows = _serialize_datetime_rows([asdict(d) for d in details], "snapshot_time")
    return _batch_load(client, table_id, rows, ITEM_STATS_DETAIL_SCHEMA)
