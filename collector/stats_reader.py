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

    # Combat
    deaths: int = 0
    mob_kills: int = 0
    player_kills: int = 0
    damage_dealt: int = 0
    damage_taken: int = 0

    # Movement
    walk_cm: int = 0
    sprint_cm: int = 0
    crouch_cm: int = 0
    swim_cm: int = 0
    fly_cm: int = 0
    fall_cm: int = 0
    climb_cm: int = 0
    boat_cm: int = 0
    horse_cm: int = 0
    minecart_cm: int = 0
    elytra_cm: int = 0
    walk_on_water_cm: int = 0
    walk_under_water_cm: int = 0
    jump: int = 0
    sneak_time_ticks: int = 0

    # Blocks & items (aggregates)
    blocks_mined: int = 0
    blocks_placed: int = 0
    items_crafted: int = 0
    items_used: int = 0
    items_picked_up: int = 0
    items_dropped: int = 0
    items_broken: int = 0
    items_enchanted: int = 0

    # Interactions
    animals_bred: int = 0
    fish_caught: int = 0
    traded_with_villager: int = 0
    talked_to_villager: int = 0
    opened_chest: int = 0
    opened_enderchest: int = 0
    opened_shulker_box: int = 0
    sleep_in_bed: int = 0
    bell_ring: int = 0
    eat_cake_slice: int = 0
    raid_trigger: int = 0
    raid_win: int = 0

    # Time
    play_time_ticks: int = 0
    time_since_death_ticks: int = 0
    time_since_rest_ticks: int = 0


@dataclass
class MobKillDetail:
    snapshot_time: datetime
    player: str
    uuid: str
    direction: str  # "killed" or "killed_by"
    entity: str     # e.g. "zombie"
    count: int = 0


@dataclass
class ItemStatDetail:
    snapshot_time: datetime
    player: str
    uuid: str
    category: str  # mined, crafted, used, picked_up, dropped, broken
    item: str
    count: int = 0


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


def _strip_namespace(key: str) -> str:
    """Remove 'minecraft:' prefix from a key."""
    return key.removeprefix("minecraft:")


def read_player_stats(
    stats_dir: Path, usercache_path: Path
) -> tuple[list[PlayerStats], list[MobKillDetail], list[ItemStatDetail]]:
    """Read all player stat files and return structured stats.

    Returns:
        (player_stats, mob_kill_details, item_stat_details)
    """
    uuid_to_name = load_usercache(usercache_path)
    now = datetime.now(timezone.utc)
    all_stats = []
    all_mob_details = []
    all_item_details = []

    for stat_file in stats_dir.glob("*.json"):
        uuid = stat_file.stem
        player_name = uuid_to_name.get(uuid, uuid)

        with open(stat_file) as f:
            data = json.load(f)

        stats = data.get("stats", {})

        # --- Aggregate player stats ---
        all_stats.append(PlayerStats(
            snapshot_time=now,
            player=player_name,
            uuid=uuid,

            # Combat
            deaths=_get_custom(stats, "deaths"),
            mob_kills=_get_custom(stats, "mob_kills"),
            player_kills=_get_custom(stats, "player_kills"),
            damage_dealt=_get_custom(stats, "damage_dealt"),
            damage_taken=_get_custom(stats, "damage_taken"),

            # Movement
            walk_cm=_get_custom(stats, "walk_one_cm"),
            sprint_cm=_get_custom(stats, "sprint_one_cm"),
            crouch_cm=_get_custom(stats, "crouch_one_cm"),
            swim_cm=_get_custom(stats, "swim_one_cm"),
            fly_cm=_get_custom(stats, "fly_one_cm"),
            fall_cm=_get_custom(stats, "fall_one_cm"),
            climb_cm=_get_custom(stats, "climb_one_cm"),
            boat_cm=_get_custom(stats, "boat_one_cm"),
            horse_cm=_get_custom(stats, "horse_one_cm"),
            minecart_cm=_get_custom(stats, "minecart_one_cm"),
            elytra_cm=_get_custom(stats, "aviate_one_cm"),
            walk_on_water_cm=_get_custom(stats, "walk_on_water_one_cm"),
            walk_under_water_cm=_get_custom(stats, "walk_under_water_one_cm"),
            jump=_get_custom(stats, "jump"),
            sneak_time_ticks=_get_custom(stats, "sneak_time"),

            # Blocks & items (aggregates)
            blocks_mined=_sum_category(stats, "minecraft:mined"),
            blocks_placed=_sum_category(stats, "minecraft:used"),
            items_crafted=_sum_category(stats, "minecraft:crafted"),
            items_used=_sum_category(stats, "minecraft:used"),
            items_picked_up=_sum_category(stats, "minecraft:picked_up"),
            items_dropped=_sum_category(stats, "minecraft:dropped"),
            items_broken=_sum_category(stats, "minecraft:broken"),
            items_enchanted=_get_custom(stats, "enchant_item"),

            # Interactions
            animals_bred=_get_custom(stats, "animals_bred"),
            fish_caught=_get_custom(stats, "fish_caught"),
            traded_with_villager=_get_custom(stats, "traded_with_villager"),
            talked_to_villager=_get_custom(stats, "talked_to_villager"),
            opened_chest=_get_custom(stats, "open_chest"),
            opened_enderchest=_get_custom(stats, "open_enderchest"),
            opened_shulker_box=_get_custom(stats, "open_shulker_box"),
            sleep_in_bed=_get_custom(stats, "sleep_in_bed"),
            bell_ring=_get_custom(stats, "bell_ring"),
            eat_cake_slice=_get_custom(stats, "eat_cake_slice"),
            raid_trigger=_get_custom(stats, "raid_trigger"),
            raid_win=_get_custom(stats, "raid_win"),

            # Time
            play_time_ticks=_get_custom(stats, "play_time"),
            time_since_death_ticks=_get_custom(stats, "time_since_death"),
            time_since_rest_ticks=_get_custom(stats, "time_since_rest"),
        ))

        # --- Per-entity kill/killed_by breakdowns ---
        for entity_key, count in stats.get("minecraft:killed", {}).items():
            all_mob_details.append(MobKillDetail(
                snapshot_time=now, player=player_name, uuid=uuid,
                direction="killed", entity=_strip_namespace(entity_key), count=count,
            ))
        for entity_key, count in stats.get("minecraft:killed_by", {}).items():
            all_mob_details.append(MobKillDetail(
                snapshot_time=now, player=player_name, uuid=uuid,
                direction="killed_by", entity=_strip_namespace(entity_key), count=count,
            ))

        # --- Per-item breakdowns ---
        category_map = {
            "minecraft:mined": "mined",
            "minecraft:crafted": "crafted",
            "minecraft:used": "used",
            "minecraft:picked_up": "picked_up",
            "minecraft:dropped": "dropped",
            "minecraft:broken": "broken",
        }
        for mc_cat, detail_name in category_map.items():
            for item_key, count in stats.get(mc_cat, {}).items():
                all_item_details.append(ItemStatDetail(
                    snapshot_time=now, player=player_name, uuid=uuid,
                    category=detail_name, item=_strip_namespace(item_key), count=count,
                ))

    return all_stats, all_mob_details, all_item_details
