# Security Policy

CyberRescue executes commands inside Docker containers on your behalf, based on instructions from an AI client (Claude). It is designed for **local, single-user, single-host use only** — it has no network listener and is not intended to be exposed remotely or used in multi-tenant environments.

## Threat model

The primary risk is an AI client (or a manipulated prompt) instructing CyberRescue to run a destructive or data-exfiltrating command inside a container, or to target a container/path outside the intended scope.

## Mitigations

**Container ID validation**
All `container_id` inputs are validated against `^[a-zA-Z0-9][a-zA-Z0-9_.-]+$` before any Docker command is constructed. Inputs that don't match are rejected before any subprocess is spawned.

**Command blocklist** (`execute_isolated_script` only)
Commands are checked against known-dangerous patterns before execution:
- `rm -rf /`
- `curl ... | sh` / `wget ... | sh`
- `chmod 777`
- `/etc/passwd`
- redirects to `/dev/sd*`

This is a blocklist, not an allowlist — it blocks known-bad patterns but cannot guarantee exhaustive coverage of every dangerous command. Use CyberRescue only against containers you trust and own.

**Timeouts**
`execute_isolated_script` enforces a hard timeout via `asyncio.wait_for`, with the subprocess killed on timeout. A runaway command cannot hang the server.

**Concurrency cap**
A bounded `asyncio.Semaphore(4)` limits simultaneous Docker daemon calls, preventing an agent loop from flooding the daemon.

**Error sanitization**
Raw Docker daemon error messages (which can include host paths) are logged locally but never returned verbatim to the MCP client — clients receive a generic, sanitized error message instead.

**No network exposure**
CyberRescue communicates with Claude Desktop exclusively over stdio. It opens no network ports and has no remote attack surface.

## Out of scope

- Multi-host / Docker Swarm deployments
- Multi-tenant or remote access
- Audit logging / compliance trails (not implemented in v0.1.0)
- Rate limiting (not implemented in v0.1.0 — acceptable for single-user local use)

## Reporting

This is a personal/portfolio project. If you find an issue, open a GitHub issue on this repo.
