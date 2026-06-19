# 🐋 CyberRescue

<p align="center">
  <img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License MIT">
  <img src="https://img.shields.io/badge/Python-3.12%2B-brightgreen.svg" alt="Python 3.12+">
  <img src="https://img.shields.io/badge/Built%20with-MCP-orange.svg" alt="Built with Model Context Protocol">
</p>

### **Give Claude eyes and hands inside your broken Docker containers.**

---

## 📺 Live Triage Demonstration (33s)

<p align="center">
  <img src="./assets/cyberrescue-demo.gif" width="100%" alt="CyberRescue Autonomous Debugging Loop Demo">
</p>

> **Architectural Paradigm Shift:** CyberRescue operates entirely at the host user-space layer, interfacing directly with the master Docker daemon (`/var/run/docker.sock`). This enables local AI agents running inside secure sandboxes (like Claude Code) or remote windows (like Claude Cowork) to query real-time log streams and extract kernel metrics from containers that have completely exited or are locked in startup boot-loops.

---
# CyberRescue

A locally-hosted MCP (Model Context Protocol) server that gives Claude real tools to debug Docker containers — fetch logs, inspect memory/CPU, and run diagnostic commands inside a container, all from a chat with Claude Desktop.

## What it does

CyberRescue exposes three tools to Claude:

- **`stream_container_logs`** — fetch stdout/stderr logs from a container by ID or name (tail, since-timestamp, keyword filter; 50KB hard cap with truncation flag).
- **`inspect_memory_dump`** — live CPU/memory snapshot via `docker stats`, plus top processes via `ps aux --sort=-%mem`.
- **`execute_isolated_script`** — run a shell command inside a container via `docker exec`, with input validation, a command blocklist, and a hard asyncio timeout.

Everything runs locally over stdio — no network ports, no cloud service, no API keys beyond what you already use for Claude Desktop.

## Requirements

- macOS (Apple Silicon) **or** Windows 10/11 with WSL2
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (running)
- [uv](https://docs.astral.sh/uv/) (Python package/project manager)
- [Claude Desktop](https://claude.ai/download)

---

## Setup — macOS

### 1. System tools

```bash
xcode-select --install
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
brew install git
curl -LsSf https://astral.sh/uv/install.sh | sh
brew install --cask docker
```

Open Docker Desktop from Applications and let it finish starting (steady whale icon in the menu bar). Then install Claude Desktop from [claude.ai](https://claude.ai) → Download for Mac.

### 2. Clone and install

```bash
git clone https://github.com/vivekpatil200320/cyberrescue.git
cd cyberrescue
uv sync
```

### 3. Verify

```bash
uv run python -c "from cyberrescue.server import mcp; print('OK:', mcp.name)"
uv run pytest tests/ -v
```

### 4. Register with Claude Desktop

Find your `uv` path:

```bash
which uv
```

Edit (or create) `~/Library/Application Support/Claude/claude_desktop_config.json`:

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

If the file already has other `mcpServers` entries, merge `"cyberrescue"` in as an additional key rather than overwriting the file.

Fully quit Claude Desktop (Cmd+Q) and reopen it. Check the tools/slider icon near the message box — `cyberrescue` should appear with all three tools listed.

---

## Setup — Windows (via WSL2)

WSL2 is the recommended path because Docker Desktop for Windows runs its Linux containers through it, and `python-on-whales`/`docker exec` behave most predictably there.

### 1. Install WSL2 and Ubuntu

In an **Administrator PowerShell**:

```powershell
wsl --install
```

Restart if prompted, then open the new "Ubuntu" app from the Start menu and finish the Linux user setup.

### 2. Install Docker Desktop for Windows

Download from [docker.com](https://www.docker.com/products/docker-desktop/), install, and during setup enable **"Use WSL 2 based engine"**. In Docker Desktop settings, under Resources → WSL Integration, enable integration with your Ubuntu distro.

### 3. Inside the WSL Ubuntu terminal — install tooling

```bash
sudo apt update
sudo apt install -y git python3 build-essential
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
```

### 4. Clone and install

```bash
git clone https://github.com/vivekpatil200320/cyberrescue.git
cd cyberrescue
uv sync
```

### 5. Verify

```bash
uv run python -c "from cyberrescue.server import mcp; print('OK:', mcp.name)"
uv run pytest tests/ -v
docker ps -a
```

(`docker ps` should work inside WSL once Docker Desktop's WSL integration is enabled.)

### 6. Install Claude Desktop (native Windows)

Download from [claude.ai](https://claude.ai) → Download for Windows, install normally (not inside WSL).

### 7. Register with Claude Desktop

Find your `uv` path inside WSL:

```bash
which uv
```

Edit `%APPDATA%\Claude\claude_desktop_config.json` (open via File Explorer: paste `%APPDATA%\Claude` into the address bar) and add an entry that runs the server through WSL:

```json
{
  "mcpServers": {
    "cyberrescue": {
      "command": "wsl.exe",
      "args": [
        "bash",
        "-c",
        "cd /home/YOUR_LINUX_USERNAME/cyberrescue && /home/YOUR_LINUX_USERNAME/.local/bin/uv run python -m cyberrescue.server"
      ]
    }
  }
}
```

Replace `YOUR_LINUX_USERNAME` and the path with your actual WSL username and clone location. Fully quit Claude Desktop and reopen it. Check the tools/slider icon — `cyberrescue` should appear with all three tools.

---

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

See [SECURITY.md](SECURITY.md) for the input validation, command blocklist, and concurrency/sanitization policy.

## Future Enhancements

- Standalone binary packaging (PyInstaller/Nuitka) for zero-Python-install distribution
- Streaming log reads for very large logs (currently buffers full log before truncating)
- Optional SQLite audit log for compliance use cases
- Native (non-WSL) Windows support

## License

MIT
