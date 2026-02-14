"""Minecraft MCP server for natural language Q&A via Claude Desktop.

Exposes BigQuery Minecraft data through MCP tools, resources, and prompts
so users can ask questions like "What happened today?" and get narrative answers.
"""

from __future__ import annotations

import json
import os
from datetime import datetime

from google.cloud import bigquery
from google.cloud.bigquery import QueryJobConfig
from mcp.server.fastmcp import FastMCP

from . import queries
from .semantic_layer import (
    STORYTELLING_GUIDE,
    metrics_as_text,
    schema_as_text,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ID = os.environ.get("MC_GCP_PROJECT_ID", "minecraft-free-487319")
DATASET = os.environ.get("MC_BQ_DATASET", "minecraft")

# ---------------------------------------------------------------------------
# Server init
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "Minecraft Dashboard",
    instructions=(
        "You are a Minecraft server narrator. Use the provided tools to query "
        "player stats, events, and leaderboards, then tell the story of what "
        "happened on the server. Read the minecraft://storytelling-guide resource "
        "for narrative style guidance. Always convert units (cm→blocks, ticks→hours) "
        "and use SAFE_DIVIDE for ratios."
    ),
)

# ---------------------------------------------------------------------------
# BigQuery client (lazy init)
# ---------------------------------------------------------------------------

_bq_client: bigquery.Client | None = None


def _get_client() -> bigquery.Client:
    global _bq_client
    if _bq_client is None:
        _bq_client = bigquery.Client(project=PROJECT_ID)
    return _bq_client


def _run_query(sql: str, params: list | None = None) -> list[dict]:
    """Execute a BigQuery query and return rows as dicts."""
    client = _get_client()
    job_config = QueryJobConfig()
    if params:
        job_config.query_parameters = params
    job = client.query(sql, job_config=job_config)
    rows = job.result()
    result = []
    for row in rows:
        d = dict(row)
        # Convert non-serializable types
        for k, v in d.items():
            if isinstance(v, datetime):
                d[k] = v.isoformat()
        result.append(d)
    return result


# ---------------------------------------------------------------------------
# MCP Resources
# ---------------------------------------------------------------------------

@mcp.resource("minecraft://schema")
def get_schema() -> str:
    """Complete data dictionary for all Minecraft BigQuery tables."""
    return schema_as_text()


@mcp.resource("minecraft://metrics")
def get_metrics() -> str:
    """Derived metrics and KPIs available for player stats analysis."""
    return metrics_as_text()


@mcp.resource("minecraft://storytelling-guide")
def get_storytelling_guide() -> str:
    """Guide for narrating Minecraft data as engaging stories."""
    return STORYTELLING_GUIDE


# ---------------------------------------------------------------------------
# MCP Prompts
# ---------------------------------------------------------------------------

@mcp.prompt()
def tell_story() -> str:
    """Generate a comprehensive narrative of recent server activity."""
    return (
        "Tell me the story of what happened on the Minecraft server recently. "
        "Use the get_server_summary tool for overall stats, get_recent_events for "
        "the timeline, and get_leaderboard for rankings. Weave the data into an "
        "engaging narrative following the storytelling guide. Include player names, "
        "dramatic moments (deaths, achievements), and interesting stats."
    )


@mcp.prompt()
def player_profile(player_name: str) -> str:
    """Deep dive into one player's adventure."""
    return (
        f"Tell me the story of {player_name}'s Minecraft adventure. "
        f"Use get_player_stats for their stats, get_recent_events filtered to "
        f"{player_name} for their timeline, and get_mob_report for their combat "
        f"history. Create a narrative arc with their achievements, setbacks, and "
        f"play style. Follow the storytelling guide."
    )


@mcp.prompt()
def rivalry(player1: str, player2: str) -> str:
    """Compare two players as a friendly rivalry narrative."""
    return (
        f"Create a rivalry narrative comparing {player1} and {player2}. "
        f"Use compare_players to get their stats side by side. Highlight each "
        f"player's strengths, declare category winners, and note complementary "
        f"play styles. Make it fun and competitive. Follow the storytelling guide."
    )


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def get_player_stats(player_name: str | None = None) -> str:
    """Get latest stats for a player (or all players) with derived metrics.

    Args:
        player_name: Player name to look up, or omit for all players.

    Returns:
        JSON array of player stats including K/D ratio, distance, play hours, etc.
    """
    sql, params = queries.latest_player_stats(
        player=player_name, project=PROJECT_ID, dataset=DATASET
    )
    rows = _run_query(sql, params)
    if not rows:
        return json.dumps({"message": f"No stats found for player '{player_name}'."})
    return json.dumps(rows, indent=2)


@mcp.tool()
def get_recent_events(
    hours: int = 24,
    event_type: str | None = None,
    player_name: str | None = None,
    limit: int = 200,
) -> str:
    """Get recent server events (deaths, advancements, joins, etc.).

    Args:
        hours: How many hours back to look (default 24).
        event_type: Filter by type: death, advancement, challenge, goal, join, leave, chat.
        player_name: Filter to a specific player.
        limit: Max events to return (default 200, max 1000).

    Returns:
        JSON array of events with timestamp, player, event_type, and details.
    """
    sql, params = queries.recent_events(
        hours=hours,
        event_type=event_type,
        player=player_name,
        limit=limit,
        project=PROJECT_ID,
        dataset=DATASET,
    )
    rows = _run_query(sql, params)
    if not rows:
        return json.dumps({"message": "No events found for the given filters."})
    return json.dumps(rows, indent=2)


@mcp.tool()
def get_leaderboard(stat: str = "deaths") -> str:
    """Get player leaderboard for any stat.

    Args:
        stat: The stat to rank by. Options: deaths, mob_kills, player_kills,
              blocks_mined, blocks_placed, items_crafted, damage_dealt,
              play_time_ticks, kd_ratio, total_distance_km, play_hours,
              builder_score, death_rate, activity_rate.

    Returns:
        JSON array of players ranked by the chosen stat.
    """
    sql, params = queries.latest_player_stats(project=PROJECT_ID, dataset=DATASET)
    rows = _run_query(sql, params)
    if not rows:
        return json.dumps({"message": "No player stats found."})

    # Sort by the requested stat
    valid_keys = set()
    if rows:
        valid_keys = set(rows[0].keys())

    if stat not in valid_keys:
        return json.dumps({
            "error": f"Unknown stat '{stat}'.",
            "available_stats": sorted(valid_keys - {"player", "snapshot_time"}),
        })

    rows.sort(key=lambda r: r.get(stat) or 0, reverse=True)
    return json.dumps(rows, indent=2)


@mcp.tool()
def compare_players(player1: str, player2: str) -> str:
    """Head-to-head comparison of two players with all stats and derived metrics.

    Args:
        player1: First player name.
        player2: Second player name.

    Returns:
        JSON array with both players' stats side by side.
    """
    sql, params = queries.player_comparison(
        player1, player2, project=PROJECT_ID, dataset=DATASET
    )
    rows = _run_query(sql, params)
    if not rows:
        return json.dumps({"message": f"No stats found for '{player1}' and/or '{player2}'."})
    return json.dumps(rows, indent=2)


@mcp.tool()
def get_mob_report(
    direction: str = "killed",
    player_name: str | None = None,
) -> str:
    """Report on mob kills or mob deaths.

    Args:
        direction: 'killed' for mobs the players killed, 'killed_by' for mobs that killed players.
        player_name: Filter to a specific player (optional).

    Returns:
        JSON array of mobs ranked by kill count.
    """
    sql, params = queries.mob_leaderboard(
        direction=direction,
        player=player_name,
        project=PROJECT_ID,
        dataset=DATASET,
    )
    rows = _run_query(sql, params)
    if not rows:
        return json.dumps({"message": "No mob kill data found."})
    return json.dumps(rows, indent=2)


@mcp.tool()
def get_item_breakdown(
    category: str = "mined",
    player_name: str | None = None,
) -> str:
    """Top items by category (mined, crafted, used, picked_up, dropped, broken).

    Args:
        category: Item action category. One of: mined, crafted, used, picked_up, dropped, broken.
        player_name: Filter to a specific player (optional).

    Returns:
        JSON array of items ranked by count.
    """
    sql, params = queries.item_breakdown(
        category=category,
        player=player_name,
        project=PROJECT_ID,
        dataset=DATASET,
    )
    rows = _run_query(sql, params)
    if not rows:
        return json.dumps({"message": f"No item data found for category '{category}'."})
    return json.dumps(rows, indent=2)


@mcp.tool()
def get_server_summary() -> str:
    """Overall server activity summary with cumulative and 7-day stats.

    Returns:
        JSON object with total players, deaths, mob kills, blocks, play hours,
        and 7-day event counts.
    """
    sql, params = queries.server_summary(project=PROJECT_ID, dataset=DATASET)
    rows = _run_query(sql, params)
    if not rows:
        return json.dumps({"message": "No server data found."})
    return json.dumps(rows[0], indent=2)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    """Run the MCP server (stdio transport)."""
    mcp.run()


if __name__ == "__main__":
    main()
