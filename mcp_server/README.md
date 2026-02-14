# Minecraft MCP Server

Ask natural language questions about your Minecraft server in Claude Desktop and get engaging, story-driven answers.

**Example questions you can ask:**
- "What happened on the server today?"
- "Who died the most?"
- "Tell me about Steve's adventure"
- "What are the most dangerous mobs?"
- "Compare Alex and Steve"
- "Who's the best builder?"

## Setup

### Docker (recommended for easy sharing)

If you have Docker installed, see [DOCKER.md](DOCKER.md) for a setup that requires no Python installation — just Docker + a credentials file + a config snippet.

### Python Installation

#### Prerequisites

- **Python 3.11+** — [Download](https://www.python.org/downloads/)
- **Google Cloud credentials** with BigQuery read access to the shared dataset

### Step 1: Install

```bash
pip install minecraft-dashboard
```

Or for local development:

```bash
git clone <repo-url>
cd minecraft_project
pip install -e .
```

### Step 2: Set up Google Cloud credentials

You need a service account JSON key with BigQuery read access:

```bash
# Option A: set the environment variable
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"

# Option B: use gcloud CLI
gcloud auth application-default login
```

### Step 3: Configure Claude Desktop

Open your Claude Desktop config file:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Add the Minecraft MCP server:

```json
{
  "mcpServers": {
    "minecraft": {
      "command": "minecraft-mcp",
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "/path/to/your/service-account-key.json"
      }
    }
  }
}
```

If you installed from source instead of pip:

```json
{
  "mcpServers": {
    "minecraft": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/path/to/minecraft_project",
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "/path/to/your/service-account-key.json"
      }
    }
  }
}
```

### Step 4: Restart Claude Desktop

Fully quit and reopen Claude Desktop. The Minecraft tools should now appear.

### Step 5: Start chatting!

Just ask Claude about your Minecraft server. Try these prompts:

- **"Tell me what happened on the server"** — uses the built-in `tell-story` prompt for a full narrative
- **"Who's winning?"** — leaderboard with rivalry framing
- **"What did Alex do today?"** — player-specific adventure story

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `MC_GCP_PROJECT_ID` | `minecraft-free-487319` | Google Cloud project ID |
| `MC_BQ_DATASET` | `minecraft` | BigQuery dataset name |
| `GOOGLE_APPLICATION_CREDENTIALS` | (none) | Path to GCP service account key |

## Available Tools

| Tool | What it does |
|------|-------------|
| `get_player_stats` | Latest stats for one or all players with derived metrics |
| `get_recent_events` | Recent events (deaths, advancements, joins, chat) |
| `get_leaderboard` | Player rankings for any stat |
| `compare_players` | Head-to-head comparison of two players |
| `get_mob_report` | Most dangerous mobs / most hunted mobs |
| `get_item_breakdown` | Top items by category (mined, crafted, etc.) |
| `get_server_summary` | Overall server activity summary |

## Troubleshooting

**"No server data found"**
- Check that your Google Cloud credentials have BigQuery read access
- Verify the project ID and dataset name match your setup

**Tools not appearing in Claude Desktop**
- Make sure you fully quit and restarted Claude Desktop (not just closed the window)
- Check that the command path is correct in `claude_desktop_config.json`
- Try running `minecraft-mcp` in your terminal to see if there are import errors

**Authentication errors**
- Run `gcloud auth application-default login` to refresh credentials
- Or ensure `GOOGLE_APPLICATION_CREDENTIALS` points to a valid service account key
