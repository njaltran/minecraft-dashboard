FROM python:3.11-slim

WORKDIR /app

RUN useradd -m -u 1000 mcpuser

COPY mcp_server/ /app/mcp_server/

RUN pip install --no-cache-dir \
    "google-cloud-bigquery>=3.25" \
    "mcp[cli]>=1.2.0" \
    "pydantic>=2.9" \
    "pydantic-settings>=2.5" \
    "db-dtypes>=1.2"

USER mcpuser

ENV MC_GCP_PROJECT_ID=minecraft-free-487319 \
    MC_BQ_DATASET=minecraft \
    PYTHONPATH=/app

ENTRYPOINT ["python", "-m", "mcp_server.server"]
