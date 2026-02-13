"""Streamlit dashboard for Minecraft server competitions."""

import sys
from pathlib import Path

# Ensure project root is on sys.path when run via `streamlit run`
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from google.cloud import bigquery
from datetime import datetime, timedelta
import plotly.express as px
import pandas as pd

from config import settings

st.set_page_config(
    page_title="Minecraft Competition Dashboard",
    page_icon="⛏️",
    layout="wide",
)


@st.cache_resource
def get_client() -> bigquery.Client:
    """Create BigQuery client. Uses Streamlit secrets on Cloud, local ADC otherwise."""
    if "gcp_service_account" in st.secrets:
        from google.oauth2 import service_account
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"]
        )
        project = st.secrets["gcp_service_account"]["project_id"]
        return bigquery.Client(project=project, credentials=credentials)
    return bigquery.Client(project=settings.gcp_project_id)


def query_bq(sql: str) -> pd.DataFrame:
    client = get_client()
    return client.query(sql).to_dataframe()


def full_table(table: str) -> str:
    return f"`{settings.gcp_project_id}.{settings.bq_dataset}.{table}`"


# --- Sidebar: date range filter ---
st.sidebar.title("⛏️ MC Dashboard")
st.sidebar.markdown("---")

preset = st.sidebar.selectbox(
    "Time range",
    ["Last 7 days", "Last 24 hours", "Last 30 days", "Custom"],
)

if preset == "Last 24 hours":
    start_date = datetime.utcnow() - timedelta(days=1)
    end_date = datetime.utcnow()
elif preset == "Last 7 days":
    start_date = datetime.utcnow() - timedelta(days=7)
    end_date = datetime.utcnow()
elif preset == "Last 30 days":
    start_date = datetime.utcnow() - timedelta(days=30)
    end_date = datetime.utcnow()
else:
    start_date = st.sidebar.date_input("Start date", datetime.utcnow() - timedelta(days=7))
    end_date = st.sidebar.date_input("End date", datetime.utcnow())

auto_refresh = st.sidebar.checkbox("Auto-refresh (2 min)", value=True)
if auto_refresh:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=120_000, key="auto_refresh")

st.sidebar.markdown("---")
st.sidebar.caption("Data refreshes every ~2 min from server")

# --- Main content ---
st.title("⛏️ Minecraft Competition Dashboard")

# ============================================================
# LEADERBOARDS
# ============================================================
st.header("🏆 Leaderboards")

latest_stats_sql = f"""
SELECT * FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY player ORDER BY snapshot_time DESC) as rn
    FROM {full_table(settings.bq_player_stats_table)}
    WHERE snapshot_time >= '{start_date.isoformat()}'
)
WHERE rn = 1
ORDER BY deaths DESC
"""

try:
    stats_df = query_bq(latest_stats_sql)
except Exception as e:
    st.error(f"Could not query player stats: {e}")
    stats_df = pd.DataFrame()

if not stats_df.empty:
    # Row 1: Combat stats
    cols = st.columns(4)
    with cols[0]:
        st.subheader("💀 Deaths")
        st.dataframe(
            stats_df[["player", "deaths"]].sort_values("deaths", ascending=False),
            use_container_width=True, hide_index=True,
        )
    with cols[1]:
        st.subheader("⚔️ Mob Kills")
        st.dataframe(
            stats_df[["player", "mob_kills"]].sort_values("mob_kills", ascending=False),
            use_container_width=True, hide_index=True,
        )
    with cols[2]:
        st.subheader("💥 Damage Dealt")
        st.dataframe(
            stats_df[["player", "damage_dealt"]].sort_values("damage_dealt", ascending=False),
            use_container_width=True, hide_index=True,
        )
    with cols[3]:
        st.subheader("🛡️ Damage Taken")
        st.dataframe(
            stats_df[["player", "damage_taken"]].sort_values("damage_taken", ascending=False),
            use_container_width=True, hide_index=True,
        )

    # Row 2: Building & gathering
    cols2 = st.columns(4)
    with cols2[0]:
        st.subheader("⛏️ Blocks Mined")
        st.dataframe(
            stats_df[["player", "blocks_mined"]].sort_values("blocks_mined", ascending=False),
            use_container_width=True, hide_index=True,
        )
    with cols2[1]:
        st.subheader("🧱 Blocks Placed")
        st.dataframe(
            stats_df[["player", "blocks_placed"]].sort_values("blocks_placed", ascending=False),
            use_container_width=True, hide_index=True,
        )
    with cols2[2]:
        st.subheader("🔨 Items Crafted")
        st.dataframe(
            stats_df[["player", "items_crafted"]].sort_values("items_crafted", ascending=False),
            use_container_width=True, hide_index=True,
        )
    with cols2[3]:
        st.subheader("📦 Items Picked Up")
        st.dataframe(
            stats_df[["player", "items_picked_up"]].sort_values("items_picked_up", ascending=False),
            use_container_width=True, hide_index=True,
        )

    # Row 3: Movement
    cols3 = st.columns(4)
    with cols3[0]:
        st.subheader("🏃 Distance Traveled")
        dist_df = stats_df[["player", "walk_cm", "sprint_cm", "swim_cm", "fly_cm", "boat_cm", "horse_cm"]].copy()
        dist_df["total_blocks"] = (
            dist_df["walk_cm"] + dist_df["sprint_cm"] + dist_df["swim_cm"]
            + dist_df["fly_cm"] + dist_df["boat_cm"] + dist_df["horse_cm"]
        ) / 100
        st.dataframe(
            dist_df[["player", "total_blocks"]].sort_values("total_blocks", ascending=False),
            use_container_width=True, hide_index=True,
        )
    with cols3[1]:
        st.subheader("🦘 Jumps")
        st.dataframe(
            stats_df[["player", "jump"]].sort_values("jump", ascending=False),
            use_container_width=True, hide_index=True,
        )
    with cols3[2]:
        st.subheader("🕐 Play Time (hours)")
        time_df = stats_df[["player", "play_time_ticks"]].copy()
        time_df["hours"] = (time_df["play_time_ticks"] / 20 / 3600).round(1)
        st.dataframe(
            time_df[["player", "hours"]].sort_values("hours", ascending=False),
            use_container_width=True, hide_index=True,
        )
    with cols3[3]:
        st.subheader("🐾 Animals Bred")
        st.dataframe(
            stats_df[["player", "animals_bred"]].sort_values("animals_bred", ascending=False),
            use_container_width=True, hide_index=True,
        )
else:
    st.info("No player stats data yet. Make sure the collector is running.")

# ============================================================
# MOB KILL BREAKDOWN
# ============================================================
st.header("🐲 Mob Kill Breakdown")

mob_detail_sql = f"""
SELECT * FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY player, direction, entity ORDER BY snapshot_time DESC) as rn
    FROM {full_table('mob_kills_detail')}
    WHERE snapshot_time >= '{start_date.isoformat()}'
)
WHERE rn = 1
ORDER BY count DESC
"""

try:
    mob_df = query_bq(mob_detail_sql)
except Exception as e:
    st.error(f"Could not query mob details: {e}")
    mob_df = pd.DataFrame()

if not mob_df.empty:
    mob_cols = st.columns(2)

    with mob_cols[0]:
        st.subheader("Mobs You Killed")
        killed_df = mob_df[mob_df["direction"] == "killed"][["player", "entity", "count"]]
        if not killed_df.empty:
            fig_killed = px.bar(
                killed_df, x="entity", y="count", color="player",
                barmode="group", title="Mobs Killed by Player",
            )
            st.plotly_chart(fig_killed, use_container_width=True)

    with mob_cols[1]:
        st.subheader("Mobs That Killed You")
        killed_by_df = mob_df[mob_df["direction"] == "killed_by"][["player", "entity", "count"]]
        if not killed_by_df.empty:
            fig_killed_by = px.bar(
                killed_by_df, x="entity", y="count", color="player",
                barmode="group", title="Killed By (per mob type)",
            )
            st.plotly_chart(fig_killed_by, use_container_width=True)
else:
    st.info("No mob kill data yet.")

# ============================================================
# ITEM BREAKDOWN
# ============================================================
st.header("📊 Item Breakdown")

item_category = st.selectbox(
    "Item category",
    ["mined", "crafted", "used", "picked_up", "dropped", "broken"],
)

item_detail_sql = f"""
SELECT * FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY player, category, item ORDER BY snapshot_time DESC) as rn
    FROM {full_table('item_stats_detail')}
    WHERE snapshot_time >= '{start_date.isoformat()}'
      AND category = '{item_category}'
)
WHERE rn = 1
ORDER BY count DESC
LIMIT 50
"""

try:
    item_df = query_bq(item_detail_sql)
except Exception as e:
    st.error(f"Could not query item details: {e}")
    item_df = pd.DataFrame()

if not item_df.empty:
    fig_items = px.bar(
        item_df, x="item", y="count", color="player",
        barmode="group", title=f"Top Items ({item_category})",
    )
    st.plotly_chart(fig_items, use_container_width=True)
    st.dataframe(item_df[["player", "item", "count"]], use_container_width=True, hide_index=True)
else:
    st.info(f"No item data for '{item_category}' yet.")

# ============================================================
# EVENT TIMELINE
# ============================================================
st.header("📅 Event Timeline")

events_sql = f"""
SELECT timestamp, player, event_type, details
FROM {full_table(settings.bq_events_table)}
WHERE timestamp >= '{start_date.isoformat()}'
  AND timestamp <= '{end_date.isoformat()}'
ORDER BY timestamp DESC
LIMIT 500
"""

try:
    events_df = query_bq(events_sql)
except Exception as e:
    st.error(f"Could not query events: {e}")
    events_df = pd.DataFrame()

if not events_df.empty:
    # Event count by type per player
    event_counts = events_df.groupby(["player", "event_type"]).size().reset_index(name="count")
    fig = px.bar(
        event_counts, x="player", y="count", color="event_type",
        barmode="group", title="Events by Player",
    )
    st.plotly_chart(fig, use_container_width=True)

    # Deaths over time
    deaths_df = events_df[events_df["event_type"] == "death"].copy()
    if not deaths_df.empty:
        deaths_df["date"] = pd.to_datetime(deaths_df["timestamp"]).dt.date
        deaths_timeline = deaths_df.groupby(["date", "player"]).size().reset_index(name="deaths")
        fig2 = px.line(
            deaths_timeline, x="date", y="deaths", color="player",
            title="Deaths Over Time", markers=True,
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Recent events log
    st.subheader("Recent Events")
    st.dataframe(events_df.head(50), use_container_width=True, hide_index=True)
else:
    st.info("No events data yet. Make sure the collector is running.")

# ============================================================
# STATS TRENDS OVER TIME
# ============================================================
st.header("📈 Stats Trends")

stats_trend_sql = f"""
SELECT snapshot_time, player,
    deaths, mob_kills, player_kills, damage_dealt, damage_taken,
    blocks_mined, blocks_placed, items_crafted, items_picked_up,
    jump, animals_bred, fish_caught,
    (walk_cm + sprint_cm + swim_cm + fly_cm) / 100 as distance_blocks,
    play_time_ticks / 20 / 3600 as play_hours
FROM {full_table(settings.bq_player_stats_table)}
WHERE snapshot_time >= '{start_date.isoformat()}'
ORDER BY snapshot_time
"""

try:
    trend_df = query_bq(stats_trend_sql)
except Exception as e:
    st.error(f"Could not query stats trends: {e}")
    trend_df = pd.DataFrame()

if not trend_df.empty:
    metric = st.selectbox(
        "Select metric",
        ["deaths", "mob_kills", "player_kills", "damage_dealt", "damage_taken",
         "blocks_mined", "blocks_placed", "items_crafted", "items_picked_up",
         "jump", "animals_bred", "fish_caught", "distance_blocks", "play_hours"],
    )
    fig3 = px.line(
        trend_df, x="snapshot_time", y=metric, color="player",
        title=f"{metric.replace('_', ' ').title()} Over Time", markers=True,
    )
    st.plotly_chart(fig3, use_container_width=True)

# ============================================================
# MOVEMENT BREAKDOWN
# ============================================================
st.header("🗺️ Movement Breakdown")

if not stats_df.empty:
    movement_cols = ["walk_cm", "sprint_cm", "crouch_cm", "swim_cm", "fly_cm",
                     "fall_cm", "climb_cm", "boat_cm", "horse_cm", "elytra_cm"]
    available_cols = [c for c in movement_cols if c in stats_df.columns]

    if available_cols:
        move_df = stats_df[["player"] + available_cols].copy()
        # Convert cm to blocks
        for col in available_cols:
            move_df[col.replace("_cm", "")] = (move_df[col] / 100).round(1)
        display_cols = [col.replace("_cm", "") for col in available_cols]
        move_melted = move_df[["player"] + display_cols].melt(
            id_vars="player", var_name="movement_type", value_name="blocks"
        )
        fig_move = px.bar(
            move_melted, x="player", y="blocks", color="movement_type",
            barmode="stack", title="Distance by Movement Type (blocks)",
        )
        st.plotly_chart(fig_move, use_container_width=True)


def main():
    """Entry point for mc-dashboard script."""
    import subprocess
    import sys
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", __file__],
        check=True,
    )
