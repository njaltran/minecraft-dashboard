"""Tests for Minecraft stats reader."""

import json
from pathlib import Path

from collector.stats_reader import load_usercache, read_player_stats


SAMPLE_USERCACHE = [
    {"name": "Njackisyourdad", "uuid": "63f167bb-ff0d-4bcb-a09b-ca34f443510b", "expiresOn": "2025-05-21 13:56:09 +0200"}
]

SAMPLE_STATS = {
    "stats": {
        "minecraft:custom": {
            "minecraft:deaths": 3,
            "minecraft:mob_kills": 10,
            "minecraft:player_kills": 1,
            "minecraft:play_time": 50000,
            "minecraft:walk_one_cm": 100000,
            "minecraft:sprint_one_cm": 200000,
            "minecraft:crouch_one_cm": 5000,
            "minecraft:swim_one_cm": 3000,
            "minecraft:fly_one_cm": 8000,
            "minecraft:fall_one_cm": 2000,
            "minecraft:jump": 500,
            "minecraft:sneak_time": 300,
            "minecraft:damage_dealt": 250,
            "minecraft:damage_taken": 180,
            "minecraft:animals_bred": 5,
            "minecraft:fish_caught": 12,
            "minecraft:enchant_item": 3,
            "minecraft:open_chest": 20,
            "minecraft:sleep_in_bed": 7,
            "minecraft:time_since_death": 1000,
            "minecraft:time_since_rest": 500,
        },
        "minecraft:mined": {
            "minecraft:stone": 50,
            "minecraft:dirt": 30,
        },
        "minecraft:used": {
            "minecraft:cobblestone": 20,
            "minecraft:dirt": 15,
        },
        "minecraft:crafted": {
            "minecraft:crafting_table": 2,
            "minecraft:wooden_pickaxe": 1,
        },
        "minecraft:picked_up": {
            "minecraft:cobblestone": 50,
            "minecraft:dirt": 30,
            "minecraft:stick": 10,
        },
        "minecraft:dropped": {
            "minecraft:dirt": 5,
        },
        "minecraft:broken": {
            "minecraft:wooden_pickaxe": 1,
        },
        "minecraft:killed": {
            "minecraft:zombie": 4,
            "minecraft:skeleton": 3,
        },
        "minecraft:killed_by": {
            "minecraft:creeper": 2,
        },
    }
}


class TestLoadUsercache:
    def test_loads_mapping(self, tmp_path):
        cache_file = tmp_path / "usercache.json"
        cache_file.write_text(json.dumps(SAMPLE_USERCACHE))
        mapping = load_usercache(cache_file)
        assert mapping["63f167bb-ff0d-4bcb-a09b-ca34f443510b"] == "Njackisyourdad"

    def test_missing_file_returns_empty(self, tmp_path):
        mapping = load_usercache(tmp_path / "nonexistent.json")
        assert mapping == {}


class TestReadPlayerStats:
    def _setup_files(self, tmp_path):
        cache_file = tmp_path / "usercache.json"
        cache_file.write_text(json.dumps(SAMPLE_USERCACHE))
        stats_dir = tmp_path / "stats"
        stats_dir.mkdir()
        stat_file = stats_dir / "63f167bb-ff0d-4bcb-a09b-ca34f443510b.json"
        stat_file.write_text(json.dumps(SAMPLE_STATS))
        return stats_dir, cache_file

    def test_reads_aggregate_stats(self, tmp_path):
        stats_dir, cache_file = self._setup_files(tmp_path)
        player_stats, mob_details, item_details = read_player_stats(stats_dir, cache_file)
        assert len(player_stats) == 1

        s = player_stats[0]
        assert s.player == "Njackisyourdad"
        assert s.uuid == "63f167bb-ff0d-4bcb-a09b-ca34f443510b"
        # Combat
        assert s.deaths == 3
        assert s.mob_kills == 10
        assert s.player_kills == 1
        assert s.damage_dealt == 250
        assert s.damage_taken == 180
        # Movement
        assert s.walk_cm == 100000
        assert s.sprint_cm == 200000
        assert s.crouch_cm == 5000
        assert s.swim_cm == 3000
        assert s.fly_cm == 8000
        assert s.fall_cm == 2000
        assert s.jump == 500
        assert s.sneak_time_ticks == 300
        # Blocks & items
        assert s.blocks_mined == 80  # 50 + 30
        assert s.items_crafted == 3  # 2 + 1
        assert s.items_picked_up == 90  # 50 + 30 + 10
        assert s.items_dropped == 5
        assert s.items_broken == 1
        assert s.items_enchanted == 3
        # Interactions
        assert s.animals_bred == 5
        assert s.fish_caught == 12
        assert s.opened_chest == 20
        assert s.sleep_in_bed == 7
        # Time
        assert s.play_time_ticks == 50000
        assert s.time_since_death_ticks == 1000
        assert s.time_since_rest_ticks == 500

    def test_mob_kill_details(self, tmp_path):
        stats_dir, cache_file = self._setup_files(tmp_path)
        _, mob_details, _ = read_player_stats(stats_dir, cache_file)

        killed = [d for d in mob_details if d.direction == "killed"]
        killed_by = [d for d in mob_details if d.direction == "killed_by"]

        assert len(killed) == 2  # zombie, skeleton
        assert len(killed_by) == 1  # creeper

        zombie = next(d for d in killed if d.entity == "zombie")
        assert zombie.count == 4
        assert zombie.player == "Njackisyourdad"

        creeper = killed_by[0]
        assert creeper.entity == "creeper"
        assert creeper.count == 2

    def test_item_stat_details(self, tmp_path):
        stats_dir, cache_file = self._setup_files(tmp_path)
        _, _, item_details = read_player_stats(stats_dir, cache_file)

        mined = [d for d in item_details if d.category == "mined"]
        crafted = [d for d in item_details if d.category == "crafted"]
        dropped = [d for d in item_details if d.category == "dropped"]

        assert len(mined) == 2  # stone, dirt
        assert len(crafted) == 2  # crafting_table, wooden_pickaxe
        assert len(dropped) == 1  # dirt

        stone = next(d for d in mined if d.item == "stone")
        assert stone.count == 50

    def test_empty_stats_dir(self, tmp_path):
        cache_file = tmp_path / "usercache.json"
        cache_file.write_text("[]")
        stats_dir = tmp_path / "stats"
        stats_dir.mkdir()

        player_stats, mob_details, item_details = read_player_stats(stats_dir, cache_file)
        assert player_stats == []
        assert mob_details == []
        assert item_details == []
