from google.cloud.bigquery import SchemaField

EVENTS_SCHEMA = [
    SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
    SchemaField("player", "STRING", mode="REQUIRED"),
    SchemaField("event_type", "STRING", mode="REQUIRED"),
    # death, advancement, challenge, goal, join, leave, chat, killed_entity
    SchemaField("details", "STRING", mode="NULLABLE"),
    SchemaField("raw_message", "STRING", mode="NULLABLE"),
]

PLAYER_STATS_SCHEMA = [
    SchemaField("snapshot_time", "TIMESTAMP", mode="REQUIRED"),
    SchemaField("player", "STRING", mode="REQUIRED"),
    SchemaField("uuid", "STRING", mode="REQUIRED"),

    # Combat
    SchemaField("deaths", "INTEGER", mode="NULLABLE"),
    SchemaField("mob_kills", "INTEGER", mode="NULLABLE"),
    SchemaField("player_kills", "INTEGER", mode="NULLABLE"),
    SchemaField("damage_dealt", "INTEGER", mode="NULLABLE"),
    SchemaField("damage_taken", "INTEGER", mode="NULLABLE"),

    # Movement
    SchemaField("walk_cm", "INTEGER", mode="NULLABLE"),
    SchemaField("sprint_cm", "INTEGER", mode="NULLABLE"),
    SchemaField("crouch_cm", "INTEGER", mode="NULLABLE"),
    SchemaField("swim_cm", "INTEGER", mode="NULLABLE"),
    SchemaField("fly_cm", "INTEGER", mode="NULLABLE"),
    SchemaField("fall_cm", "INTEGER", mode="NULLABLE"),
    SchemaField("climb_cm", "INTEGER", mode="NULLABLE"),
    SchemaField("boat_cm", "INTEGER", mode="NULLABLE"),
    SchemaField("horse_cm", "INTEGER", mode="NULLABLE"),
    SchemaField("minecart_cm", "INTEGER", mode="NULLABLE"),
    SchemaField("elytra_cm", "INTEGER", mode="NULLABLE"),
    SchemaField("walk_on_water_cm", "INTEGER", mode="NULLABLE"),
    SchemaField("walk_under_water_cm", "INTEGER", mode="NULLABLE"),
    SchemaField("jump", "INTEGER", mode="NULLABLE"),
    SchemaField("sneak_time_ticks", "INTEGER", mode="NULLABLE"),

    # Blocks & items
    SchemaField("blocks_mined", "INTEGER", mode="NULLABLE"),
    SchemaField("blocks_placed", "INTEGER", mode="NULLABLE"),
    SchemaField("items_crafted", "INTEGER", mode="NULLABLE"),
    SchemaField("items_used", "INTEGER", mode="NULLABLE"),
    SchemaField("items_picked_up", "INTEGER", mode="NULLABLE"),
    SchemaField("items_dropped", "INTEGER", mode="NULLABLE"),
    SchemaField("items_broken", "INTEGER", mode="NULLABLE"),
    SchemaField("items_enchanted", "INTEGER", mode="NULLABLE"),

    # Interactions
    SchemaField("animals_bred", "INTEGER", mode="NULLABLE"),
    SchemaField("fish_caught", "INTEGER", mode="NULLABLE"),
    SchemaField("traded_with_villager", "INTEGER", mode="NULLABLE"),
    SchemaField("talked_to_villager", "INTEGER", mode="NULLABLE"),
    SchemaField("opened_chest", "INTEGER", mode="NULLABLE"),
    SchemaField("opened_enderchest", "INTEGER", mode="NULLABLE"),
    SchemaField("opened_shulker_box", "INTEGER", mode="NULLABLE"),
    SchemaField("sleep_in_bed", "INTEGER", mode="NULLABLE"),
    SchemaField("bell_ring", "INTEGER", mode="NULLABLE"),
    SchemaField("eat_cake_slice", "INTEGER", mode="NULLABLE"),
    SchemaField("raid_trigger", "INTEGER", mode="NULLABLE"),
    SchemaField("raid_win", "INTEGER", mode="NULLABLE"),

    # Time
    SchemaField("play_time_ticks", "INTEGER", mode="NULLABLE"),
    SchemaField("time_since_death_ticks", "INTEGER", mode="NULLABLE"),
    SchemaField("time_since_rest_ticks", "INTEGER", mode="NULLABLE"),
]

# Per-entity kill/death breakdown (minecraft:killed and minecraft:killed_by)
MOB_KILLS_DETAIL_SCHEMA = [
    SchemaField("snapshot_time", "TIMESTAMP", mode="REQUIRED"),
    SchemaField("player", "STRING", mode="REQUIRED"),
    SchemaField("uuid", "STRING", mode="REQUIRED"),
    SchemaField("direction", "STRING", mode="REQUIRED"),  # "killed" or "killed_by"
    SchemaField("entity", "STRING", mode="REQUIRED"),     # e.g. "zombie", "creeper"
    SchemaField("count", "INTEGER", mode="REQUIRED"),
]

# Per-item breakdown for mined/crafted/used/picked_up/dropped
ITEM_STATS_DETAIL_SCHEMA = [
    SchemaField("snapshot_time", "TIMESTAMP", mode="REQUIRED"),
    SchemaField("player", "STRING", mode="REQUIRED"),
    SchemaField("uuid", "STRING", mode="REQUIRED"),
    SchemaField("category", "STRING", mode="REQUIRED"),  # mined, crafted, used, picked_up, dropped, broken
    SchemaField("item", "STRING", mode="REQUIRED"),       # e.g. "birch_log", "stone"
    SchemaField("count", "INTEGER", mode="REQUIRED"),
]
