from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Minecraft server paths
    server_dir: Path = Path("/opt/minecraft")
    log_file: Path | None = None  # defaults to server_dir/logs/latest.log
    stats_dir: Path | None = None  # defaults to server_dir/world/stats
    usercache_file: Path | None = None  # defaults to server_dir/usercache.json

    # BigQuery
    gcp_project_id: str = "my-minecraft-project"
    bq_dataset: str = "minecraft"
    bq_events_table: str = "events"
    bq_player_stats_table: str = "player_stats"

    # Collector
    collect_interval_seconds: int = 120  # 2 minutes
    log_offset_file: Path = Path(".log_offset")

    model_config = {"env_prefix": "MC_"}

    @property
    def resolved_log_file(self) -> Path:
        return self.log_file or self.server_dir / "logs" / "latest.log"

    @property
    def resolved_stats_dir(self) -> Path:
        return self.stats_dir or self.server_dir / "world" / "stats"

    @property
    def resolved_usercache_file(self) -> Path:
        return self.usercache_file or self.server_dir / "usercache.json"


settings = Settings()
