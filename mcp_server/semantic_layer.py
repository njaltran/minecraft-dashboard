"""Semantic layer for Minecraft BigQuery data.

Embeds table metadata, derived metrics, unit conversions, and storytelling
context directly in Python so it ships with the MCP server package.
"""

import json

# ---------------------------------------------------------------------------
# Project / dataset defaults
# ---------------------------------------------------------------------------
DEFAULT_PROJECT = "minecraft-free-487319"
DEFAULT_DATASET = "minecraft"


def fqn(table: str, project: str = DEFAULT_PROJECT, dataset: str = DEFAULT_DATASET) -> str:
    """Return fully-qualified BigQuery table name."""
    return f"`{project}.{dataset}.{table}`"


# ---------------------------------------------------------------------------
# Unit conversion helpers
# ---------------------------------------------------------------------------

def cm_to_blocks(cm: int) -> float:
    return cm / 100


def cm_to_km(cm: int) -> float:
    return cm / 100_000


def ticks_to_seconds(ticks: int) -> float:
    return ticks / 20


def ticks_to_hours(ticks: int) -> float:
    return ticks / 72_000


def ticks_to_days(ticks: int) -> float:
    return ticks / 1_728_000


# ---------------------------------------------------------------------------
# Table metadata  (exposed as MCP resource "minecraft://schema")
# ---------------------------------------------------------------------------

TABLE_DESCRIPTIONS: dict = {
    "events": {
        "description": "Append-only log of all server events parsed from server logs.",
        "grain": "One row per event occurrence.",
        "columns": {
            "timestamp": "TIMESTAMP — when the event occurred (server time).",
            "player": "STRING — player name involved in the event.",
            "event_type": (
                "STRING — one of: death, advancement, challenge, goal, "
                "join, leave, chat, login, server_start."
            ),
            "details": "STRING (nullable) — death reason, advancement name, chat message, etc.",
            "raw_message": "STRING (nullable) — original log line.",
        },
    },
    "player_stats": {
        "description": (
            "Periodic snapshots of cumulative player statistics, taken every ~2 minutes. "
            "Values are running totals, NOT deltas. To get current stats use the latest "
            "snapshot per player (ROW_NUMBER pattern)."
        ),
        "grain": "One row per player per snapshot time.",
        "columns": {
            "snapshot_time": "TIMESTAMP — when this snapshot was taken.",
            "player": "STRING — player name.",
            "uuid": "STRING — permanent player UUID.",
            # Combat
            "deaths": "INTEGER — total times died (cumulative).",
            "mob_kills": "INTEGER — total mobs killed (cumulative).",
            "player_kills": "INTEGER — total PvP kills (cumulative).",
            "damage_dealt": "INTEGER — total damage dealt in half-hearts (cumulative).",
            "damage_taken": "INTEGER — total damage taken in half-hearts (cumulative).",
            # Movement (all in centimeters)
            "walk_cm": "INTEGER — distance walked in cm. Divide by 100 for blocks.",
            "sprint_cm": "INTEGER — distance sprinted in cm.",
            "crouch_cm": "INTEGER — distance crouched in cm.",
            "swim_cm": "INTEGER — distance swum in cm.",
            "fly_cm": "INTEGER — distance flown (creative/spectator) in cm.",
            "fall_cm": "INTEGER — distance fallen in cm.",
            "climb_cm": "INTEGER — distance climbed (ladders/vines) in cm.",
            "boat_cm": "INTEGER — distance by boat in cm.",
            "horse_cm": "INTEGER — distance on horse in cm.",
            "minecart_cm": "INTEGER — distance in minecart in cm.",
            "elytra_cm": "INTEGER — distance with elytra in cm.",
            "walk_on_water_cm": "INTEGER — distance walked on water in cm.",
            "walk_under_water_cm": "INTEGER — distance walked underwater in cm.",
            "jump": "INTEGER — number of jumps (cumulative).",
            "sneak_time_ticks": "INTEGER — time sneaking in ticks (÷20 = seconds).",
            # Blocks & items
            "blocks_mined": "INTEGER — total blocks broken (cumulative).",
            "blocks_placed": "INTEGER — total blocks placed (cumulative).",
            "items_crafted": "INTEGER — total items crafted (cumulative).",
            "items_used": "INTEGER — total items used (cumulative).",
            "items_picked_up": "INTEGER — total items picked up (cumulative).",
            "items_dropped": "INTEGER — total items dropped (cumulative).",
            "items_broken": "INTEGER — total tools/items broken from durability (cumulative).",
            "items_enchanted": "INTEGER — total items enchanted (cumulative).",
            # Interactions
            "animals_bred": "INTEGER — total animals bred (cumulative).",
            "fish_caught": "INTEGER — total fish caught (cumulative).",
            "traded_with_villager": "INTEGER — total villager trades (cumulative).",
            "talked_to_villager": "INTEGER — total times talked to villagers (cumulative).",
            "opened_chest": "INTEGER — total chests opened (cumulative).",
            "opened_enderchest": "INTEGER — total ender chests opened (cumulative).",
            "opened_shulker_box": "INTEGER — total shulker boxes opened (cumulative).",
            "sleep_in_bed": "INTEGER — total times slept in bed (cumulative).",
            "bell_ring": "INTEGER — total bells rung (cumulative).",
            "eat_cake_slice": "INTEGER — total cake slices eaten (cumulative).",
            "raid_trigger": "INTEGER — total raids triggered (cumulative).",
            "raid_win": "INTEGER — total raids won (cumulative).",
            # Time (in ticks; 20 ticks = 1 second, 72000 = 1 hour)
            "play_time_ticks": "INTEGER — total play time in ticks (÷72000 = hours).",
            "time_since_death_ticks": "INTEGER — ticks since last death (resets on death).",
            "time_since_rest_ticks": "INTEGER — ticks since last sleep (resets on sleep).",
        },
    },
    "mob_kills_detail": {
        "description": (
            "Per-entity breakdown of kills and deaths. Snapshot table (cumulative). "
            "Use latest snapshot per (player, direction, entity)."
        ),
        "grain": "One row per player × entity × direction per snapshot.",
        "columns": {
            "snapshot_time": "TIMESTAMP — when this snapshot was taken.",
            "player": "STRING — player name.",
            "uuid": "STRING — player UUID.",
            "direction": "STRING — 'killed' (player killed entity) or 'killed_by' (entity killed player).",
            "entity": "STRING — mob type without minecraft: prefix (zombie, creeper, etc.).",
            "count": "INTEGER — cumulative count.",
        },
    },
    "item_stats_detail": {
        "description": (
            "Per-item breakdown of mining, crafting, using, etc. Snapshot table (cumulative). "
            "Use latest snapshot per (player, category, item)."
        ),
        "grain": "One row per player × category × item per snapshot.",
        "columns": {
            "snapshot_time": "TIMESTAMP — when this snapshot was taken.",
            "player": "STRING — player name.",
            "uuid": "STRING — player UUID.",
            "category": "STRING — mined, crafted, used, picked_up, dropped, or broken.",
            "item": "STRING — item id without minecraft: prefix (diamond_pickaxe, oak_log, etc.).",
            "count": "INTEGER — cumulative count.",
        },
    },
}

# ---------------------------------------------------------------------------
# Derived metrics  (exposed as MCP resource "minecraft://metrics")
# ---------------------------------------------------------------------------

METRICS: dict = {
    "kd_ratio": {
        "name": "Kill/Death Ratio",
        "sql_expr": "SAFE_DIVIDE(mob_kills, NULLIF(deaths, 0))",
        "description": "Mob kills per death. Above 1.0 = more kills than deaths.",
        "category": "combat",
    },
    "pvp_kd_ratio": {
        "name": "PvP K/D Ratio",
        "sql_expr": "SAFE_DIVIDE(player_kills, NULLIF(deaths, 0))",
        "description": "Player kills per death.",
        "category": "combat",
    },
    "combat_efficiency": {
        "name": "Combat Efficiency",
        "sql_expr": "SAFE_DIVIDE(damage_dealt, NULLIF(damage_taken, 0))",
        "description": "Damage dealt per damage taken. Above 1.0 = net positive.",
        "category": "combat",
    },
    "total_distance_blocks": {
        "name": "Total Distance (blocks)",
        "sql_expr": (
            "(COALESCE(walk_cm,0) + COALESCE(sprint_cm,0) + COALESCE(crouch_cm,0) "
            "+ COALESCE(swim_cm,0) + COALESCE(fly_cm,0) + COALESCE(fall_cm,0) "
            "+ COALESCE(climb_cm,0) + COALESCE(boat_cm,0) + COALESCE(horse_cm,0) "
            "+ COALESCE(minecart_cm,0) + COALESCE(elytra_cm,0) "
            "+ COALESCE(walk_on_water_cm,0) + COALESCE(walk_under_water_cm,0)) / 100"
        ),
        "description": "Sum of all movement types converted to blocks.",
        "category": "movement",
    },
    "total_distance_km": {
        "name": "Total Distance (km)",
        "sql_expr": (
            "(COALESCE(walk_cm,0) + COALESCE(sprint_cm,0) + COALESCE(crouch_cm,0) "
            "+ COALESCE(swim_cm,0) + COALESCE(fly_cm,0) + COALESCE(fall_cm,0) "
            "+ COALESCE(climb_cm,0) + COALESCE(boat_cm,0) + COALESCE(horse_cm,0) "
            "+ COALESCE(minecart_cm,0) + COALESCE(elytra_cm,0) "
            "+ COALESCE(walk_on_water_cm,0) + COALESCE(walk_under_water_cm,0)) / 100000.0"
        ),
        "description": "Sum of all movement types converted to kilometers.",
        "category": "movement",
    },
    "play_hours": {
        "name": "Play Time (hours)",
        "sql_expr": "COALESCE(play_time_ticks, 0) / 72000.0",
        "description": "Total play time converted to hours.",
        "category": "time",
    },
    "builder_score": {
        "name": "Builder Score",
        "sql_expr": "COALESCE(blocks_placed, 0) + COALESCE(items_crafted, 0)",
        "description": "Blocks placed plus items crafted.",
        "category": "building",
    },
    "net_block_change": {
        "name": "Net Block Change",
        "sql_expr": "COALESCE(blocks_placed, 0) - COALESCE(blocks_mined, 0)",
        "description": "Blocks placed minus mined. Positive = net builder.",
        "category": "building",
    },
    "death_rate": {
        "name": "Deaths Per Hour",
        "sql_expr": "SAFE_DIVIDE(deaths, NULLIF(COALESCE(play_time_ticks,0) / 72000.0, 0))",
        "description": "Average deaths per hour of play time.",
        "category": "composite",
    },
    "activity_rate": {
        "name": "Actions Per Hour",
        "sql_expr": (
            "SAFE_DIVIDE("
            "COALESCE(blocks_mined,0) + COALESCE(blocks_placed,0) "
            "+ COALESCE(mob_kills,0) + COALESCE(items_crafted,0), "
            "NULLIF(COALESCE(play_time_ticks,0) / 72000.0, 0))"
        ),
        "description": "Blocks + kills + crafts per hour of play.",
        "category": "composite",
    },
}


def schema_as_text() -> str:
    """Return the full data dictionary as human-readable text."""
    lines = ["# Minecraft BigQuery Data Dictionary\n"]
    for table_name, info in TABLE_DESCRIPTIONS.items():
        lines.append(f"## Table: {table_name}")
        lines.append(f"{info['description']}")
        lines.append(f"Grain: {info['grain']}\n")
        lines.append("| Column | Description |")
        lines.append("|--------|-------------|")
        for col, desc in info["columns"].items():
            lines.append(f"| {col} | {desc} |")
        lines.append("")
    return "\n".join(lines)


def metrics_as_text() -> str:
    """Return derived metrics as human-readable text."""
    lines = ["# Derived Metrics\n"]
    lines.append("These metrics are calculated from raw columns in player_stats.\n")
    for key, m in METRICS.items():
        lines.append(f"- **{m['name']}** ({m['category']}): {m['description']}")
        lines.append(f"  SQL: `{m['sql_expr']}`")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Storytelling guide  (exposed as MCP resource "minecraft://storytelling-guide")
# ---------------------------------------------------------------------------

STORYTELLING_GUIDE = """\
# Minecraft Storytelling Guide

When narrating Minecraft server data, follow these principles:

## Tone
- Treat players as characters in an adventure, not rows in a database.
- Use vivid, active language: "plummeted", "conquered", "struggled", "soared".
- Be warm and celebratory — highlight achievements, frame deaths as dramatic setbacks.

## Structure
- **Opening hook**: Lead with the most interesting or dramatic fact.
- **Characters**: Name every player mentioned; they're the protagonists.
- **Conflict**: Deaths, mob encounters, competition between players.
- **Resolution**: Achievements unlocked, builds completed, survival streaks.
- **Closing**: Current state or a teaser for what's next.

## Data presentation
- Convert units: show distances in blocks or km, time in hours, not raw cm or ticks.
- Use comparisons: "nearly twice as many", "just shy of 100", "leagues ahead".
- Relate to real world: "walked the equivalent of a half-marathon".
- Round numbers for readability: "about 12,000 blocks" not "11,847 blocks".

## Rankings & competition
- Frame leaderboards as friendly rivalry, not judgement.
- Highlight each player's unique strengths.
- Use superlatives: "the server's most fearless explorer", "the undisputed builder".

## Example narrative
> The day began when Alex logged in at 9:43 AM and immediately headed underground.
> Over the next three hours, they mined an impressive 2,400 blocks — mostly stone and
> iron ore — before a fateful encounter with a creeper ended their 4-hour survival
> streak. Undeterred, Alex respawned and turned to building, placing 800 blocks on
> what appears to be a growing castle project. Meanwhile, Steve dominated the combat
> leaderboards with 47 mob kills and zero deaths, pushing his K/D ratio to an
> enviable 12.3.

## Important reminders
- All player_stats values are CUMULATIVE totals, not session deltas.
- Always use the latest snapshot per player (ROW_NUMBER pattern).
- Use SAFE_DIVIDE to avoid division by zero.
- Distance columns are in centimeters; time columns are in ticks.
"""
