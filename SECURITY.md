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

## Out of scope (local MCP mode)

- Multi-host / Docker Swarm deployments
- Multi-tenant or remote access
- Audit logging / compliance trails (not implemented in v0.1.0)
- Rate limiting (not implemented in v0.1.0 — acceptable for single-user local use)

## Public demo mode

The web demo (`backend/` + `web/`, described in the README) is a **separate trust model**,
not a relaxation of the local-mode policy above. Local mode assumes a trusted single user
talking to their own containers over stdio; public demo mode assumes an anonymous internet
visitor and is designed accordingly:

**Container allowlist, not user-supplied IDs**
Every public route validates the container name against `cyberrescue.demo_policy.DEMO_CONTAINERS`
— exactly `broken-flask`, `leaking-node`, `crashed-nginx`. There is no route that accepts an
arbitrary `container_id`; the local mode's regex-based `validate_container_id` still runs
underneath as defense-in-depth, but the primary control is the fixed allowlist.

**Fixed diagnostic menu, not freeform shell text**
`execute_isolated_script` is freeform for local Claude Desktop users (guarded only by the
blocklist in `security.py`, which itself admits it "cannot guarantee exhaustive coverage" —
an acceptable tradeoff for a trusted local user, not for an anonymous public one). The public
`/diagnose` route instead accepts only a `command_key` enum
(`cyberrescue.demo_policy.DEMO_COMMAND_MENU`); the server looks up the literal shell string,
so client-supplied text is never interpolated into a shell. The existing blocklist still runs
against the resolved command as cheap additional defense-in-depth.

**Rate limiting**
Per-IP limits (via `slowapi`) on every public route, tighter on `/diagnose` and tightest on
`/narrate` (the route that calls the Anthropic API), plus a separate concurrency cap on
in-flight Anthropic calls to bound spend from a traffic burst.

**No client-trusted evidence**
`/narrate` re-fetches logs/stats server-side rather than accepting client-submitted "evidence"
as the basis for the LLM prompt.

**Periodic reset**
The 3 demo containers are recreated on a timer (`infra/systemd/cyberrescue-reset.timer`,
`infra/reset_demo.py`) so a visitor interacting with (or crashing) a container can't
permanently affect the demo for the next visitor. `restart: on-failure` in
`infra/docker-compose.yml` is a faster always-on backstop between resets.

**CORS**
The backend's `allow_origins` is restricted to the exact deployed frontend URL(s) — never `*`,
since this backend performs real Docker operations.

**Secrets never reach the frontend**
`ANTHROPIC_API_KEY` lives only in the VPS-side environment file (`/etc/cyberrescue/backend.env`,
`chmod 600`, never committed); the frontend only knows the backend's public base URL.

## Reporting

This is a personal/portfolio project. If you find an issue, open a GitHub issue on this repo.
