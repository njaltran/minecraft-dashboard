# Getting Started with the Minecraft MCP Server

Welcome! This guide will get you up and running in about 5 minutes. Once set up, you can ask Claude natural language questions about our Minecraft server — "Who died the most?", "What happened today?", "Tell me about Steve's adventure" — and get story-driven answers.

## What You Need

1. **Docker Desktop** — [Download here](https://www.docker.com/products/docker-desktop/)
2. **Claude Desktop** — [Download here](https://claude.ai/download)
3. **The credentials file** — Ask the server admin for `minecraft-sa-key.json`

That's it. No Python, no coding, no terminal experience required beyond copy-pasting a few things.

## Step 1: Install Docker Desktop

Download and install [Docker Desktop](https://www.docker.com/products/docker-desktop/) for your OS. Open it and make sure it's running (you'll see the whale icon in your system tray / menu bar).

## Step 2: Pull the MCP Server Image

Open a terminal (Terminal on Mac, PowerShell on Windows) and run:

```bash
docker pull dockjacker/minecraft-mcp:latest
```

Wait for it to finish downloading.

## Step 3: Save the Credentials File

Save the `minecraft-sa-key.json` file you received from the admin somewhere safe on your computer. Remember the full path — you'll need it in the next step.

Examples:
- **Mac**: `/Users/yourname/minecraft-sa-key.json`
- **Windows**: `C:/Users/yourname/minecraft-sa-key.json`

## Step 4: Configure Claude Desktop

Open your Claude Desktop config file:

- **Mac**: Open Finder, press `Cmd+Shift+G`, paste `~/Library/Application Support/Claude/`, and open `claude_desktop_config.json`
- **Windows**: Press `Win+R`, paste `%APPDATA%\Claude\`, and open `claude_desktop_config.json`

If the file doesn't exist, create it. Replace the entire contents with:

```json
{
  "mcpServers": {
    "minecraft": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i", "--init",
        "-v", "/REPLACE/WITH/YOUR/PATH/minecraft-sa-key.json:/gcp/creds.json:ro",
        "-e", "GOOGLE_APPLICATION_CREDENTIALS=/gcp/creds.json",
        "dockjacker/minecraft-mcp:latest"
      ]
    }
  }
}
```

**Important**: Replace `/REPLACE/WITH/YOUR/PATH/minecraft-sa-key.json` with the actual path to your credentials file from Step 3. Use forward slashes `/` even on Windows.

If you already have other MCP servers configured, just add the `"minecraft": { ... }` block inside the existing `"mcpServers"` object.

## Step 5: Restart Claude Desktop

Fully quit Claude Desktop (don't just close the window — right-click the tray icon and quit), then reopen it.

## Step 6: Start Asking Questions!

Open a new conversation in Claude Desktop. You should see a hammer icon indicating MCP tools are connected. Try these:

- **"What happened on the server today?"** — Full narrative of recent activity
- **"Who's winning?"** — Leaderboard with rivalry framing
- **"Tell me about [player name]'s adventure"** — Player-specific story
- **"What are the most dangerous mobs?"** — Mob kill/death report
- **"Compare [player1] and [player2]"** — Head-to-head rivalry

## Troubleshooting

### "Tools not appearing in Claude Desktop"
- Make sure Docker Desktop is running
- Fully quit and restart Claude Desktop
- Check that the config file is valid JSON (no trailing commas, matching brackets)

### "Could not find credentials" or authentication errors
- Double-check the path to `minecraft-sa-key.json` in your config
- Make sure the path is absolute (starts with `/` on Mac or `C:/` on Windows)
- Make sure the file exists at that path

### "Docker not found"
- Make sure Docker Desktop is installed and running
- On Mac, you may need to allow Docker in System Settings > Privacy & Security

### Still stuck?
Reach out to the server admin for help.
