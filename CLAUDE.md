# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python data pipeline + Streamlit dashboard + MCP server for a self-hosted vanilla Minecraft server on GCP. Reads server logs and player stats files, writes to BigQuery, serves a near-real-time competition dashboard, and enables natural language Q&A via Claude Desktop.

## Architecture

```
Minecraft Server (GCP) → Collector (Python) → BigQuery → Streamlit Dashboard
                                                   ↕
                                            MCP Server → Claude Desktop (natural language Q&A)
```

### Components

- **`collector/`** — Runs alongside the server, parses `logs/latest.log` and `world/stats/*.json`, writes structured data to BigQuery every ~2 minutes
  - `log_parser.py` — Regex-based parser for vanilla MC log format. Extracts deaths, advancements, join/leave, chat events
  - `stats_reader.py` — Reads vanilla player stats JSON files, maps UUIDs to names via `usercache.json`
  - `bigquery_writer.py` — Handles BigQuery table creation and streaming inserts
  - `main.py` — Entry point, runs collection loop with file offset tracking
- **`dashboard/app.py`** — Streamlit app querying BigQuery for leaderboards, event timelines, stat trends
- **`schemas/bigquery_schemas.py`** — BigQuery table schemas (events + player_stats + mob_kills_detail + item_stats_detail)
- **`config.py`** — Pydantic Settings model, all config via `MC_` prefixed env vars

## MCP Server

**`mcp_server/`** — MCP server for Claude Desktop that enables natural language Q&A about the Minecraft server data. Users ask questions like "What happened today?" and get engaging, story-driven answers backed by BigQuery data.

### Files

- `server.py` — FastMCP server entry point with 7 tools, 3 resources, 3 prompts
- `queries.py` — Parameterized SQL query builders (latest snapshot pattern, SAFE_DIVIDE, etc.)
- `semantic_layer.py` — Embedded data dictionary, derived metrics, unit conversions, storytelling guide
- `README.md` — User-facing setup guide for Claude Desktop

### Tools

| Tool | Description |
|------|-------------|
| `get_player_stats` | Latest stats for one or all players with derived metrics (K/D, distance, play hours) |
| `get_recent_events` | Recent events filtered by type/player/time window |
| `get_leaderboard` | Player rankings for any stat |
| `compare_players` | Head-to-head comparison of two players |
| `get_mob_report` | Most dangerous mobs / most hunted mobs |
| `get_item_breakdown` | Top items by category (mined, crafted, used, etc.) |
| `get_server_summary` | Overall server activity with cumulative + 7-day stats |

### Resources

| Resource | Description |
|----------|-------------|
| `minecraft://schema` | Full data dictionary for all 4 BigQuery tables |
| `minecraft://metrics` | Derived metrics definitions (K/D ratio, distance km, play hours, etc.) |
| `minecraft://storytelling-guide` | Instructions for narrating data as engaging stories |

### Prompts

| Prompt | Description |
|--------|-------------|
| `tell-story` | Comprehensive narrative of recent server activity |
| `player-profile` | Deep dive into one player's adventure |
| `rivalry` | Compare two players as a friendly rivalry narrative |

### Claude Desktop Setup

```json
{
  "mcpServers": {
    "minecraft": {
      "command": "/opt/anaconda3/bin/minecraft-mcp"
    }
  }
}
```

Env vars: `MC_GCP_PROJECT_ID` (default: `minecraft-free-487319`), `MC_BQ_DATASET` (default: `minecraft`), `GOOGLE_APPLICATION_CREDENTIALS`

### Semantic Layer Design

The semantic layer is embedded in Python (`semantic_layer.py`) rather than external YAML files, so it ships as a single installable package with zero config for end users. It includes:

- **Table metadata**: all 4 tables, every column with type and description
- **Derived metrics**: K/D ratio, combat efficiency, total distance (km), play hours, builder score, death rate, activity rate
- **Unit conversions**: cm→blocks (÷100), cm→km (÷100000), ticks→hours (÷72000)
- **Storytelling guide**: narrative framing, tone, structure, and example output

### Key SQL Patterns

All snapshot tables (player_stats, mob_kills_detail, item_stats_detail) need the latest-value pattern:
```sql
ROW_NUMBER() OVER (PARTITION BY player ORDER BY snapshot_time DESC) AS rn
-- then: WHERE rn = 1
```

Always use `SAFE_DIVIDE` for ratios and `COALESCE` for nullable integers.

## Commands

```bash
# Install (editable + dev deps)
pip install -e ".[dev]"

# Run tests
python -m pytest tests/ -v

# Run collector (needs GCP auth + MC_SERVER_DIR set)
MC_SERVER_DIR=/path/to/server MC_GCP_PROJECT_ID=my-project python -m collector.main

# Run dashboard
streamlit run dashboard/app.py

# Run MCP server directly
minecraft-mcp

# Run MCP server via module
python -m mcp_server.server

# Test MCP server with Inspector
mcp dev mcp_server/server.py
```

## Configuration

All settings in `config.py` via environment variables prefixed with `MC_`:
- `MC_SERVER_DIR` — Path to Minecraft server root
- `MC_GCP_PROJECT_ID` — GCP project ID (default: `minecraft-free-487319`)
- `MC_BQ_DATASET` — BigQuery dataset name (default: `minecraft`)
- `MC_COLLECT_INTERVAL_SECONDS` — Collection interval (default: `120`)

## Key Design Decisions

- **Log parsing uses byte offset tracking** (`.log_offset` file) to avoid re-processing. Handles log rotation by resetting when file shrinks.
- **Stats reader sums entire categories** (e.g., all `minecraft:mined` entries) for aggregate metrics like `blocks_mined`.
- **BigQuery streaming inserts** (`insert_rows_json`) for low-latency writes; player stats are periodic snapshots (not deltas).
- **Death message detection** matches against a keyword list since vanilla death messages always start with the player name followed by a reason phrase.
- **Semantic layer embedded in Python** (not YAML) for zero-config distribution as a single pip-installable package.
- **Parameterized queries** via `bigquery.ScalarQueryParameter` for SQL injection safety.
