"""Tests for Minecraft stats reader."""

import json
import tempfile
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
            "minecraft:jump": 500,
            "minecraft:damage_dealt": 250,
            "minecraft:damage_taken": 180,
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
    def test_reads_stats(self, tmp_path):
        # Set up usercache
        cache_file = tmp_path / "usercache.json"
        cache_file.write_text(json.dumps(SAMPLE_USERCACHE))

        # Set up stats dir
        stats_dir = tmp_path / "stats"
        stats_dir.mkdir()
        stat_file = stats_dir / "63f167bb-ff0d-4bcb-a09b-ca34f443510b.json"
        stat_file.write_text(json.dumps(SAMPLE_STATS))

        results = read_player_stats(stats_dir, cache_file)
        assert len(results) == 1

        s = results[0]
        assert s.player == "Njackisyourdad"
        assert s.uuid == "63f167bb-ff0d-4bcb-a09b-ca34f443510b"
        assert s.deaths == 3
        assert s.mob_kills == 10
        assert s.player_kills == 1
        assert s.play_time_ticks == 50000
        assert s.walk_cm == 100000
        assert s.sprint_cm == 200000
        assert s.jump == 500
        assert s.blocks_mined == 80  # 50 + 30
        assert s.items_crafted == 3  # 2 + 1
        assert s.items_picked_up == 90  # 50 + 30 + 10

    def test_empty_stats_dir(self, tmp_path):
        cache_file = tmp_path / "usercache.json"
        cache_file.write_text("[]")
        stats_dir = tmp_path / "stats"
        stats_dir.mkdir()

        results = read_player_stats(stats_dir, cache_file)
        assert results == []
