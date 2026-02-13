# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python data pipeline + Streamlit dashboard for a self-hosted vanilla Minecraft server on GCP. Reads server logs and player stats files, writes to BigQuery, and serves a near-real-time competition dashboard.

## Architecture

```
Minecraft Server (GCP) → Collector (Python) → BigQuery → Streamlit Dashboard
```

- **`collector/`** — Runs alongside the server, parses `logs/latest.log` and `world/stats/*.json`, writes structured data to BigQuery every ~2 minutes
  - `log_parser.py` — Regex-based parser for vanilla MC log format. Extracts deaths, advancements, join/leave, chat events
  - `stats_reader.py` — Reads vanilla player stats JSON files, maps UUIDs to names via `usercache.json`
  - `bigquery_writer.py` — Handles BigQuery table creation and streaming inserts
  - `main.py` — Entry point, runs collection loop with file offset tracking
- **`dashboard/app.py`** — Streamlit app querying BigQuery for leaderboards, event timelines, stat trends
- **`schemas/bigquery_schemas.py`** — BigQuery table schemas (events + player_stats)
- **`config.py`** — Pydantic Settings model, all config via `MC_` prefixed env vars

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
```

## Configuration

All settings in `config.py` via environment variables prefixed with `MC_`:
- `MC_SERVER_DIR` — Path to Minecraft server root
- `MC_GCP_PROJECT_ID` — GCP project ID
- `MC_BQ_DATASET` — BigQuery dataset name (default: `minecraft`)
- `MC_COLLECT_INTERVAL_SECONDS` — Collection interval (default: `120`)

## Key Design Decisions

- **Log parsing uses byte offset tracking** (`.log_offset` file) to avoid re-processing. Handles log rotation by resetting when file shrinks.
- **Stats reader sums entire categories** (e.g., all `minecraft:mined` entries) for aggregate metrics like `blocks_mined`.
- **BigQuery streaming inserts** (`insert_rows_json`) for low-latency writes; player stats are periodic snapshots (not deltas).
- **Death message detection** matches against a keyword list since vanilla death messages always start with the player name followed by a reason phrase.
