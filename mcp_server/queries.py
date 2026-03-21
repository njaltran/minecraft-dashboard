"""SQL query builders for the Minecraft MCP server.

Every function returns a (sql, params) tuple where params is a list of
bigquery.ScalarQueryParameter objects for safe parameterized execution.
"""

from __future__ import annotations

from google.cloud.bigquery import ScalarQueryParameter

from .semantic_layer import METRICS, fqn


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _param(name: str, type_: str, value) -> ScalarQueryParameter:
    return ScalarQueryParameter(name, type_, value)


def _latest_snapshot_cte(
    table: str,
    partition_cols: str = "player",
    project: str | None = None,
    dataset: str | None = None,
    time_filter: str | None = None,
) -> str:
    """Build a CTE that selects only the latest snapshot per partition key."""
    kwargs = {}
    if project:
        kwargs["project"] = project
    if dataset:
        kwargs["dataset"] = dataset
    table_ref = fqn(table, **kwargs)

    where = f"\n      WHERE {time_filter}" if time_filter else ""
    return (
        f"latest AS (\n"
        f"    SELECT *, ROW_NUMBER() OVER (\n"
        f"      PARTITION BY {partition_cols} ORDER BY snapshot_time DESC\n"
        f"    ) AS rn\n"
        f"    FROM {table_ref}{where}\n"
        f"  )"
    )


# ---------------------------------------------------------------------------
# Metric SQL snippet builder
# ---------------------------------------------------------------------------

def _metric_select(metric_keys: list[str] | None = None) -> str:
    """Return SQL select expressions for requested derived metrics."""
    keys = metric_keys or list(METRICS.keys())
    parts = []
    for k in keys:
        if k in METRICS:
            parts.append(f"  ROUND({METRICS[k]['sql_expr']}, 2) AS {k}")
    return ",\n".join(parts)


# ---------------------------------------------------------------------------
# Query builders
# ---------------------------------------------------------------------------

def latest_player_stats(
    player: str | None = None,
    project: str | None = None,
    dataset: str | None = None,
) -> tuple[str, list[ScalarQueryParameter]]:
    """Latest stats snapshot per player with derived metrics."""
    cte = _latest_snapshot_cte("player_stats", project=project, dataset=dataset)
    metrics = _metric_select()
    where = "WHERE rn = 1"
    params: list[ScalarQueryParameter] = []

    if player:
        where += " AND player = @player_name"
        params.append(_param("player_name", "STRING", player))

    sql = f"""\
WITH {cte}
SELECT
  player,
  snapshot_time,
  -- Combat
  deaths, mob_kills, player_kills, damage_dealt, damage_taken,
  -- Movement (raw)
  walk_cm, sprint_cm, swim_cm, fly_cm, elytra_cm, boat_cm, horse_cm,
  -- Blocks & items
  blocks_mined, blocks_placed, items_crafted, items_used, items_picked_up, items_broken,
  -- Interactions
  animals_bred, fish_caught, traded_with_villager, sleep_in_bed,
  -- Time
  play_time_ticks,
  -- Derived metrics
{metrics}
FROM latest
{where}
ORDER BY deaths DESC
"""
    return sql, params


def recent_events(
    hours: int = 24,
    event_type: str | None = None,
    player: str | None = None,
    limit: int = 200,
    project: str | None = None,
    dataset: str | None = None,
) -> tuple[str, list[ScalarQueryParameter]]:
    """Recent events, optionally filtered by type and/or player."""
    kwargs = {}
    if project:
        kwargs["project"] = project
    if dataset:
        kwargs["dataset"] = dataset
    table_ref = fqn("events", **kwargs)

    conditions = [f"timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {int(hours)} HOUR)"]
    params: list[ScalarQueryParameter] = []

    if event_type:
        conditions.append("event_type = @event_type")
        params.append(_param("event_type", "STRING", event_type))

    if player:
        conditions.append("player = @player_name")
        params.append(_param("player_name", "STRING", player))

    where = " AND ".join(conditions)
    safe_limit = min(int(limit), 1000)

    sql = f"""\
SELECT timestamp, player, event_type, details
FROM {table_ref}
WHERE {where}
ORDER BY timestamp DESC
LIMIT {safe_limit}
"""
    return sql, params


def mob_leaderboard(
    direction: str = "killed",
    player: str | None = None,
    limit: int = 15,
    project: str | None = None,
    dataset: str | None = None,
) -> tuple[str, list[ScalarQueryParameter]]:
    """Top mobs by kill count. direction='killed' or 'killed_by'."""
    safe_direction = "killed" if direction != "killed_by" else "killed_by"
    cte = _latest_snapshot_cte(
        "mob_kills_detail",
        partition_cols="player, direction, entity",
        project=project,
        dataset=dataset,
    )
    params: list[ScalarQueryParameter] = []

    player_filter = ""
    if player:
        player_filter = "AND player = @player_name"
        params.append(_param("player_name", "STRING", player))

    safe_limit = min(int(limit), 100)

    sql = f"""\
WITH {cte}
SELECT
  entity,
  SUM(count) AS total,
  COUNT(DISTINCT player) AS players_involved
FROM latest
WHERE rn = 1 AND direction = '{safe_direction}' {player_filter}
GROUP BY entity
ORDER BY total DESC
LIMIT {safe_limit}
"""
    return sql, params


def item_breakdown(
    category: str = "mined",
    player: str | None = None,
    limit: int = 25,
    project: str | None = None,
    dataset: str | None = None,
) -> tuple[str, list[ScalarQueryParameter]]:
    """Top items for a given category (mined, crafted, used, etc.)."""
    valid_categories = {"mined", "crafted", "used", "picked_up", "dropped", "broken"}
    safe_category = category if category in valid_categories else "mined"

    cte = _latest_snapshot_cte(
        "item_stats_detail",
        partition_cols="player, category, item",
        project=project,
        dataset=dataset,
    )
    params: list[ScalarQueryParameter] = []

    player_filter = ""
    if player:
        player_filter = "AND player = @player_name"
        params.append(_param("player_name", "STRING", player))

    safe_limit = min(int(limit), 100)

    sql = f"""\
WITH {cte}
SELECT
  item,
  SUM(count) AS total,
  COUNT(DISTINCT player) AS players
FROM latest
WHERE rn = 1 AND category = '{safe_category}' {player_filter}
GROUP BY item
ORDER BY total DESC
LIMIT {safe_limit}
"""
    return sql, params


def player_comparison(
    player1: str,
    player2: str,
    project: str | None = None,
    dataset: str | None = None,
) -> tuple[str, list[ScalarQueryParameter]]:
    """Side-by-side comparison of two players."""
    cte = _latest_snapshot_cte("player_stats", project=project, dataset=dataset)
    metrics = _metric_select()
    params = [
        _param("player1", "STRING", player1),
        _param("player2", "STRING", player2),
    ]

    sql = f"""\
WITH {cte}
SELECT
  player,
  snapshot_time,
  deaths, mob_kills, player_kills, damage_dealt, damage_taken,
  blocks_mined, blocks_placed, items_crafted,
  play_time_ticks,
{metrics}
FROM latest
WHERE rn = 1 AND player IN (@player1, @player2)
ORDER BY player
"""
    return sql, params


def server_summary(
    project: str | None = None,
    dataset: str | None = None,
) -> tuple[str, list[ScalarQueryParameter]]:
    """Aggregate server-wide statistics."""
    cte = _latest_snapshot_cte("player_stats", project=project, dataset=dataset)
    kwargs = {}
    if project:
        kwargs["project"] = project
    if dataset:
        kwargs["dataset"] = dataset
    events_ref = fqn("events", **kwargs)

    sql = f"""\
WITH {cte},
recent_events AS (
  SELECT
    COUNT(*) AS total_events_7d,
    COUNT(DISTINCT player) AS active_players_7d,
    COUNTIF(event_type = 'death') AS deaths_7d,
    COUNTIF(event_type IN ('advancement', 'challenge', 'goal')) AS achievements_7d,
    COUNTIF(event_type = 'join') AS joins_7d
  FROM {events_ref}
  WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
)
SELECT
  (SELECT COUNT(DISTINCT player) FROM latest WHERE rn = 1) AS total_players,
  (SELECT SUM(deaths) FROM latest WHERE rn = 1) AS total_deaths,
  (SELECT SUM(mob_kills) FROM latest WHERE rn = 1) AS total_mob_kills,
  (SELECT SUM(blocks_mined) FROM latest WHERE rn = 1) AS total_blocks_mined,
  (SELECT SUM(blocks_placed) FROM latest WHERE rn = 1) AS total_blocks_placed,
  (SELECT ROUND(SUM(play_time_ticks) / 72000.0, 1) FROM latest WHERE rn = 1) AS total_play_hours,
  r.*
FROM recent_events r
"""
    return sql, []
