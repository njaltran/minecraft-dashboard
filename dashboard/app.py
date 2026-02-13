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
st.sidebar.caption("Data refreshes every 1-5 min from server")

# --- Main content ---
st.title("Minecraft Competition Dashboard")

# --- Leaderboards from latest stats snapshot ---
st.header("Leaderboards")

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
    cols = st.columns(4)

    with cols[0]:
        st.subheader("💀 Deaths")
        death_df = stats_df[["player", "deaths"]].sort_values("deaths", ascending=False)
        st.dataframe(death_df, use_container_width=True, hide_index=True)

    with cols[1]:
        st.subheader("⚔️ Mob Kills")
        kills_df = stats_df[["player", "mob_kills"]].sort_values("mob_kills", ascending=False)
        st.dataframe(kills_df, use_container_width=True, hide_index=True)

    with cols[2]:
        st.subheader("🧱 Blocks Mined")
        mined_df = stats_df[["player", "blocks_mined"]].sort_values("blocks_mined", ascending=False)
        st.dataframe(mined_df, use_container_width=True, hide_index=True)

    with cols[3]:
        st.subheader("🏃 Distance (blocks)")
        dist_df = stats_df[["player", "walk_cm", "sprint_cm"]].copy()
        dist_df["total_blocks"] = (dist_df["walk_cm"] + dist_df["sprint_cm"]) / 100
        dist_df = dist_df[["player", "total_blocks"]].sort_values("total_blocks", ascending=False)
        st.dataframe(dist_df, use_container_width=True, hide_index=True)
else:
    st.info("No player stats data yet. Make sure the collector is running.")

# --- Event timeline ---
st.header("Event Timeline")

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
        event_counts,
        x="player",
        y="count",
        color="event_type",
        barmode="group",
        title="Events by Player",
    )
    st.plotly_chart(fig, use_container_width=True)

    # Deaths over time
    deaths_df = events_df[events_df["event_type"] == "death"].copy()
    if not deaths_df.empty:
        deaths_df["date"] = pd.to_datetime(deaths_df["timestamp"]).dt.date
        deaths_timeline = deaths_df.groupby(["date", "player"]).size().reset_index(name="deaths")
        fig2 = px.line(
            deaths_timeline,
            x="date",
            y="deaths",
            color="player",
            title="Deaths Over Time",
            markers=True,
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Recent events log
    st.subheader("Recent Events")
    st.dataframe(
        events_df.head(50),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No events data yet. Make sure the collector is running.")

# --- Player stats over time ---
st.header("Stats Trends")

stats_trend_sql = f"""
SELECT snapshot_time, player, deaths, mob_kills, blocks_mined, blocks_placed,
       (walk_cm + sprint_cm) / 100 as distance_blocks
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
        ["deaths", "mob_kills", "blocks_mined", "blocks_placed", "distance_blocks"],
    )
    fig3 = px.line(
        trend_df,
        x="snapshot_time",
        y=metric,
        color="player",
        title=f"{metric.replace('_', ' ').title()} Over Time",
        markers=True,
    )
    st.plotly_chart(fig3, use_container_width=True)


def main():
    """Entry point for mc-dashboard script."""
    import subprocess
    import sys
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", __file__],
        check=True,
    )
