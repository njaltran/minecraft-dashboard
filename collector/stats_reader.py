"""Read vanilla Minecraft player stats from world/stats/*.json files."""

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class PlayerStats:
    snapshot_time: datetime
    player: str
    uuid: str
    deaths: int
    mob_kills: int
    player_kills: int
    play_time_ticks: int
    walk_cm: int
    sprint_cm: int
    jump: int
    damage_dealt: int
    damage_taken: int
    blocks_mined: int
    blocks_placed: int
    items_crafted: int
    items_used: int
    items_picked_up: int


def load_usercache(usercache_path: Path) -> dict[str, str]:
    """Load UUID -> player name mapping from usercache.json."""
    if not usercache_path.exists():
        return {}
    with open(usercache_path) as f:
        entries = json.load(f)
    return {entry["uuid"]: entry["name"] for entry in entries}


def _sum_category(stats: dict, category: str) -> int:
    """Sum all values in a stat category (e.g. minecraft:mined)."""
    return sum(stats.get(category, {}).values())


def _get_custom(stats: dict, key: str) -> int:
    """Get a specific minecraft:custom stat."""
    return stats.get("minecraft:custom", {}).get(f"minecraft:{key}", 0)


def read_player_stats(
    stats_dir: Path, usercache_path: Path
) -> list[PlayerStats]:
    """Read all player stat files and return structured stats."""
    uuid_to_name = load_usercache(usercache_path)
    now = datetime.now(timezone.utc)
    results = []

    for stat_file in stats_dir.glob("*.json"):
        uuid = stat_file.stem
        player_name = uuid_to_name.get(uuid, uuid)

        with open(stat_file) as f:
            data = json.load(f)

        stats = data.get("stats", {})

        results.append(PlayerStats(
            snapshot_time=now,
            player=player_name,
            uuid=uuid,
            deaths=_get_custom(stats, "deaths"),
            mob_kills=_get_custom(stats, "mob_kills"),
            player_kills=_get_custom(stats, "player_kills"),
            play_time_ticks=_get_custom(stats, "play_time"),
            walk_cm=_get_custom(stats, "walk_one_cm"),
            sprint_cm=_get_custom(stats, "sprint_one_cm"),
            jump=_get_custom(stats, "jump"),
            damage_dealt=_get_custom(stats, "damage_dealt"),
            damage_taken=_get_custom(stats, "damage_taken"),
            blocks_mined=_sum_category(stats, "minecraft:mined"),
            blocks_placed=_sum_category(stats, "minecraft:used"),
            items_crafted=_sum_category(stats, "minecraft:crafted"),
            items_used=_sum_category(stats, "minecraft:used"),
            items_picked_up=_sum_category(stats, "minecraft:picked_up"),
        ))

    return results
