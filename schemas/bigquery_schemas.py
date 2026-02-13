from google.cloud.bigquery import SchemaField

EVENTS_SCHEMA = [
    SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
    SchemaField("player", "STRING", mode="REQUIRED"),
    SchemaField("event_type", "STRING", mode="REQUIRED"),  # death, advancement, join, leave, chat
    SchemaField("details", "STRING", mode="NULLABLE"),
    SchemaField("raw_message", "STRING", mode="NULLABLE"),
]

PLAYER_STATS_SCHEMA = [
    SchemaField("snapshot_time", "TIMESTAMP", mode="REQUIRED"),
    SchemaField("player", "STRING", mode="REQUIRED"),
    SchemaField("uuid", "STRING", mode="REQUIRED"),
    SchemaField("deaths", "INTEGER", mode="NULLABLE"),
    SchemaField("mob_kills", "INTEGER", mode="NULLABLE"),
    SchemaField("player_kills", "INTEGER", mode="NULLABLE"),
    SchemaField("play_time_ticks", "INTEGER", mode="NULLABLE"),
    SchemaField("walk_cm", "INTEGER", mode="NULLABLE"),
    SchemaField("sprint_cm", "INTEGER", mode="NULLABLE"),
    SchemaField("jump", "INTEGER", mode="NULLABLE"),
    SchemaField("damage_dealt", "INTEGER", mode="NULLABLE"),
    SchemaField("damage_taken", "INTEGER", mode="NULLABLE"),
    SchemaField("blocks_mined", "INTEGER", mode="NULLABLE"),
    SchemaField("blocks_placed", "INTEGER", mode="NULLABLE"),
    SchemaField("items_crafted", "INTEGER", mode="NULLABLE"),
    SchemaField("items_used", "INTEGER", mode="NULLABLE"),
    SchemaField("items_picked_up", "INTEGER", mode="NULLABLE"),
]
