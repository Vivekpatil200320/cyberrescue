cat > README.md << 'EOF'
# CyberRescue

A locally-hosted MCP (Model Context Protocol) server that gives Claude real tools to debug Docker containers — fetch logs, inspect memory/CPU, and run diagnostic commands inside a container, all from a chat with Claude Desktop.

## What it does

CyberRescue exposes three tools to Claude:

- **`stream_container_logs`** — fetch stdout/stderr logs from a container by ID or name (tail, since-timestamp, keyword filter; 50KB hard cap with truncation flag).
- **`inspect_memory_dump`** — live CPU/memory snapshot via `docker stats`, plus top processes via `ps aux --sort=-%mem`.
- **`execute_isolated_script`** — run a shell command inside a container via `docker exec`, with input validation, a command blocklist, and a hard asyncio timeout.

Everything runs locally over stdio — no network ports, no cloud service, no API keys beyond what you already use for Claude Desktop.

## Requirements

- macOS, Apple Silicon
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (running)
- [uv](https://docs.astral.sh/uv/) (Python package/project manager)
- [Claude Desktop](https://claude.ai/download)

## Installation

```bash
git clone https://github.com/vivekpatil200320/cyberrescue.git
cd cyberrescue
uv sync
```

Verify the install:

```bash
uv run python -c "from cyberrescue.server import mcp; print('OK:', mcp.name)"
uv run pytest tests/ -v
```

## Register with Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` and add (merge into existing `mcpServers` if present):

```json
{
  "mcpServers": {
    "cyberrescue": {
      "command": "/Users/YOUR_USERNAME/.local/bin/uv",
      "args": [
        "run",
        "--project",
        "/Users/YOUR_USERNAME/path/to/cyberrescue",
        "python",
        "-m",
        "cyberrescue.server"
      ]
    }
  }
}
```

Replace both paths with your actual `uv` location (`which uv`) and clone path. Fully quit Claude Desktop (Cmd+Q) and reopen it.

## Usage

Ask Claude Desktop something like:

> Debug the container named `my-app`: read the last 150 log lines, check its memory and CPU usage, and run `printenv DATABASE_URL` inside it.

Claude will call the three tools as needed and report back root cause and fix.

## Demo containers

`demo/` contains three intentionally broken images for testing:

- `broken_flask` — crashes on startup with a missing-env-var `KeyError`
- `leaking_node` — leaks ~10MB/sec until OOM-killed
- `crashed_nginx` — fails to start due to invalid config syntax

```bash
docker build -t demo-broken-flask demo/broken_flask
docker build -t demo-leaking-node demo/leaking_node
docker build -t demo-crashed-nginx demo/crashed_nginx
```

## Security

See [SECURITY.md](SECURITY.md) for the input validation and command blocklist policy.

## License

MIT
EOF
