# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Vivek Patil

"""CyberRescue MCP server — main entry point and tool implementations."""

import asyncio
import logging
import sys
from datetime import datetime
from typing import Optional

from mcp.server.fastmcp import FastMCP
from python_on_whales import docker
from python_on_whales.exceptions import DockerException

from cyberrescue.security import check_command_safety, validate_container_id

mcp = FastMCP("CyberRescue")
logger = logging.getLogger("cyberrescue")

MAX_LOG_BYTES = 50 * 1024  # 50KB hard cap

# Caps concurrent docker daemon calls so a multi-tool agent loop can't
# flood the daemon with unbounded simultaneous subprocesses.
_docker_sem = asyncio.Semaphore(4)

# Global flag to intercept headless execution sandboxes (like Glama verification)
DOCKER_AVAILABLE = False
try:
    if docker.ping():
        DOCKER_AVAILABLE = True
except Exception:
    # CRITICAL: Log to sys.stderr only. Writing to sys.stdout corrupts JSON-RPC protocol chunks!
    print(
        "WARNING: Local Docker Engine daemon socket is unreachable. "
        "Running server in diagnostic verification fallback mode.",
        file=sys.stderr
    )


# Retry policy for read-only telemetry calls (logs, stats). Transient
# daemon hiccups — socket resets, brief unresponsiveness under load —
# resolve within a retry or two; only idempotent reads are retried,
# never `docker exec`.
RETRY_ATTEMPTS = 3
RETRY_BASE_DELAY_S = 0.5


async def _docker_call_with_retry(fn, /, *args, **kwargs):
    """Run a read-only docker call in a thread, retrying transient failures.

    Exponential back-off: 0.5s, 1s between attempts. Raises the last
    DockerException if all attempts fail.
    """
    last_exc: Exception | None = None
    for attempt in range(RETRY_ATTEMPTS):
        try:
            return await asyncio.to_thread(fn, *args, **kwargs)
        except DockerException as exc:
            last_exc = exc
            if attempt < RETRY_ATTEMPTS - 1:
                delay = RETRY_BASE_DELAY_S * (2 ** attempt)
                logger.warning(
                    "Docker call failed (attempt %d/%d), retrying in %.1fs: %s",
                    attempt + 1, RETRY_ATTEMPTS, delay, exc,
                )
                await asyncio.sleep(delay)
    assert last_exc is not None
    raise last_exc


def _safe_docker_error(container_id: str, exc: Exception) -> RuntimeError:
    """Log the real exception internally; return a sanitized one to the client.

    Raw DockerException text can include host paths (socket paths, user
    dirs) — never pass it straight through to the MCP client.
    """
    logger.error("Docker error for container %s: %s", container_id, exc)
    return RuntimeError(
        f"Docker operation failed for container {container_id!r}. "
        "Check the container exists and the Docker daemon is running."
    )


@mcp.tool()
async def stream_container_logs(
    container_id: str,
    tail: int = 100,
    since: Optional[str] = None,
    filter_keyword: Optional[str] = None,
) -> dict:
    """Fetch stdout/stderr logs from a Docker container by ID or name.

    Args:
        container_id: Container ID or name.
        tail: Number of lines to fetch from the end of the logs.
        since: Optional ISO 8601 timestamp; only return logs after this time.
        filter_keyword: Optional substring; only return lines containing it.

    Returns:
        dict with container_id, log_lines, line_count, truncated.
    """
    validate_container_id(container_id)

    if not DOCKER_AVAILABLE:
        return {
            "container_id": container_id,
            "log_lines": ["Fallback: Docker daemon unreachable in this environment execution sandbox."],
            "line_count": 1,
            "truncated": False,
        }

    since_dt = None
    if since:
        try:
            since_dt = datetime.fromisoformat(since)
        except ValueError as exc:
            raise ValueError(
                f"Invalid `since` timestamp: {since!r}. Expected ISO 8601, "
                "e.g. 2026-06-18T10:00:00"
            ) from exc

    async with _docker_sem:
        try:
            raw_logs = await _docker_call_with_retry(
                docker.container.logs,
                container_id,
                tail=tail,
                since=since_dt,
                timestamps=True,
            )
        except DockerException as exc:
            raise _safe_docker_error(container_id, exc) from None

    lines = raw_logs.splitlines()

    if filter_keyword:
        lines = [line for line in lines if filter_keyword in line]

    truncated = False
    joined = "\n".join(lines)
    if len(joined.encode("utf-8")) > MAX_LOG_BYTES:
        truncated = True
        kept = []
        total_bytes = 0
        for line in reversed(lines):
            line_bytes = len(line.encode("utf-8")) + 1
            if total_bytes + line_bytes > MAX_LOG_BYTES:
                break
            kept.append(line)
            total_bytes += line_bytes
        lines = list(reversed(kept))

    return {
        "container_id": container_id,
        "log_lines": lines,
        "line_count": len(lines),
        "truncated": truncated,
    }


@mcp.tool()
async def inspect_memory_dump(container_id: str, include_processes: bool = True) -> dict:
    """Return live memory and CPU stats, plus top processes, for a container.

    Uses `docker stats --no-stream` for a point-in-time snapshot. The container 
    must be running for stats to be available.

    Args:
        container_id: Container ID or name.
        include_processes: If True, also runs `ps aux --sort=-%mem` inside
            the container and includes the output.

    Returns:
        dict with cpu_percent, memory_mb, memory_limit_mb, memory_percent,
        and optionally processes (list of strings, one per ps line).
    """
    validate_container_id(container_id)

    if not DOCKER_AVAILABLE:
        return {
            "cpu_percent": 0.0,
            "memory_mb": 0.0,
            "memory_limit_mb": 0.0,
            "memory_percent": 0.0,
            "processes": ["Fallback: Metrics metrics unavailable without a local Docker socket descriptor context."],
        }

    async with _docker_sem:
        try:
            stats_list = await _docker_call_with_retry(docker.stats, containers=container_id)
        except DockerException as exc:
            raise _safe_docker_error(container_id, exc) from None

    if not stats_list:
        raise RuntimeError(
            f"No stats returned for container {container_id!r}. It may not "
            "exist or may not be running (docker stats requires a running container)."
        )

    stats = stats_list[0]

    result = {
        "cpu_percent": stats.cpu_percentage,
        "memory_mb": round(stats.memory_used / (1024 * 1024), 2),
        "memory_limit_mb": round(stats.memory_limit / (1024 * 1024), 2),
        "memory_percent": stats.memory_percentage,
    }

    if include_processes:
        async with _docker_sem:
            try:
                ps_output = await asyncio.to_thread(
                    docker.container.execute, container_id, ["ps", "aux", "--sort=-%mem"]
                )
                result["processes"] = ps_output.splitlines()
            except DockerException as exc:
                logger.error("ps failed in container %s: %s", container_id, exc)
                result["processes"] = ["<process listing unavailable in this container>"]

    return result


@mcp.tool()
async def execute_isolated_script(
    container_id: str, command: str, timeout_seconds: int = 30
) -> dict:
    """Run a shell command string inside a container via `docker exec`.

    Validates container_id and blocks known-dangerous command patterns
    before running anything. Enforces a hard timeout via asyncio so a
    runaway command can never hang the server.

    Args:
        container_id: Container ID or name.
        command: Shell command string to run (executed via `sh -c`).
        timeout_seconds: Max seconds to wait before killing the command.

    Returns:
        dict with stdout, stderr, exit_code, timed_out.
    """
    validate_container_id(container_id)
    check_command_safety(command)

    if not DOCKER_AVAILABLE:
        return {
            "stdout": "",
            "stderr": "Fallback: Execution rejected. Host machine engine is unreachable.",
            "exit_code": -1,
            "timed_out": False,
        }

    async with _docker_sem:
        proc = await asyncio.create_subprocess_exec(
            "docker", "exec", container_id, "sh", "-c", command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(), timeout=timeout_seconds
            )
            timed_out = False
            exit_code = proc.returncode
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            stdout_bytes, stderr_bytes = b"", b""
            timed_out = True
            exit_code = -1

    return {
        "stdout": stdout_bytes.decode("utf-8", errors="replace"),
        "stderr": stderr_bytes.decode("utf-8", errors="replace"),
        "exit_code": exit_code,
        "timed_out": timed_out,
    }


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
