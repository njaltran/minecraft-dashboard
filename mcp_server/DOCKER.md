# Running Minecraft MCP Server in Docker

## Build

```bash
cd /path/to/minecraft_project
docker build -t minecraft-mcp:latest .
```

## Authentication

The server needs read access to BigQuery. Two options:

### Option 1: Service Account Key (simplest for sharing)

Get a service account JSON key with **BigQuery Data Viewer** role, then mount it:

```bash
docker run --rm -i \
  -v /path/to/service-account-key.json:/gcp/creds.json:ro \
  -e GOOGLE_APPLICATION_CREDENTIALS=/gcp/creds.json \
  minecraft-mcp:latest
```

### Option 2: OAuth 2.0 via gcloud (for developers)

```bash
gcloud auth application-default login
```

Then mount the ADC credentials:

```bash
docker run --rm -i \
  -v ~/.config/gcloud/application_default_credentials.json:/gcp/creds.json:ro \
  -e GOOGLE_APPLICATION_CREDENTIALS=/gcp/creds.json \
  minecraft-mcp:latest
```

ADC file locations:
- **macOS/Linux**: `~/.config/gcloud/application_default_credentials.json`
- **Windows**: `%APPDATA%\gcloud\application_default_credentials.json`

## Claude Desktop Configuration

Edit your Claude Desktop config:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

### With service account key

```json
{
  "mcpServers": {
    "minecraft": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i", "--init",
        "-v", "/absolute/path/to/service-account-key.json:/gcp/creds.json:ro",
        "-e", "GOOGLE_APPLICATION_CREDENTIALS=/gcp/creds.json",
        "minecraft-mcp:latest"
      ]
    }
  }
}
```

### With OAuth 2.0 ADC

```json
{
  "mcpServers": {
    "minecraft": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i", "--init",
        "-v", "/Users/yourname/.config/gcloud/application_default_credentials.json:/gcp/creds.json:ro",
        "-e", "GOOGLE_APPLICATION_CREDENTIALS=/gcp/creds.json",
        "minecraft-mcp:latest"
      ]
    }
  }
}
```

### Custom project or dataset

Add extra `-e` flags before the image name:

```
"-e", "MC_GCP_PROJECT_ID=my-project",
"-e", "MC_BQ_DATASET=my_dataset",
```

## Sharing the Image

### Via Docker Hub

```bash
docker tag minecraft-mcp:latest yourusername/minecraft-mcp:latest
docker push yourusername/minecraft-mcp:latest
```

Recipients use `yourusername/minecraft-mcp:latest` in their config.

### Via tar file

```bash
docker save minecraft-mcp:latest | gzip > minecraft-mcp.tar.gz
# Send the file, then recipient runs:
docker load < minecraft-mcp.tar.gz
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_APPLICATION_CREDENTIALS` | *(required)* | Path to GCP credentials JSON inside the container |
| `MC_GCP_PROJECT_ID` | `minecraft-free-487319` | BigQuery project ID |
| `MC_BQ_DATASET` | `minecraft` | BigQuery dataset name |

## Troubleshooting

**MCP server not connecting**: Make sure `-i` and `--init` flags are present — `-i` is required for stdio communication.

**Permission errors**: The container runs as non-root (uid 1000). Ensure the credentials file is world-readable on the host (`chmod 644`).

**Windows paths**: Use forward slashes: `C:/Users/Name/key.json:/gcp/creds.json:ro`

**"Could not find credentials"**: Verify the volume mount path is absolute and the file exists.
