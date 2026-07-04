"""CyberRescue MCP server — main entry point and tool registration.

Tool logic lives in core.py; this module only wires it up as MCP tools
served over stdio for Claude Desktop.
"""

from typing import Optional

from mcp.server.fastmcp import FastMCP

from cyberrescue import core

mcp = FastMCP("CyberRescue")


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
    return await core.stream_container_logs(container_id, tail, since, filter_keyword)


@mcp.tool()
async def inspect_memory_dump(container_id: str, include_processes: bool = True) -> dict:
    """Return live memory and CPU stats, plus top processes, for a container.

    Uses `docker stats --no-stream` for a point-in-time snapshot (this is not
    a real heap dump — the name is aspirational). The container must be
    running for stats to be available.

    Args:
        container_id: Container ID or name.
        include_processes: If True, also runs `ps aux --sort=-%mem` inside
            the container and includes the output.

    Returns:
        dict with cpu_percent, memory_mb, memory_limit_mb, memory_percent,
        and optionally processes (list of strings, one per ps line).
    """
    return await core.inspect_memory_dump(container_id, include_processes)


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
    return await core.execute_isolated_script(container_id, command, timeout_seconds)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
