"""Allowlist and fixed diagnostic-command menu for the public web demo.

The public HTTP backend must never accept arbitrary container IDs or
arbitrary shell text — both are unbounded attack surface for an anonymous
internet user. This module is the single source of truth for what the
public demo is allowed to touch: exactly 3 pre-built containers, and for
each, a small fixed set of pre-audited diagnostic commands selected by an
opaque key (never interpolated from client-supplied text).

This does not apply to the local stdio MCP tools used by Claude Desktop —
those remain freeform for a trusted single local user, per SECURITY.md.
"""

from cyberrescue.security import ValidationError

DEMO_CONTAINERS = frozenset({"broken-flask", "leaking-node", "crashed-nginx"})

# container_id -> { command_key: (label, literal shell command) }
DEMO_COMMAND_MENU: dict[str, dict[str, tuple[str, str]]] = {
    "broken-flask": {
        "check_env": ("Check environment variables", "printenv | sort"),
        "check_process": ("List running processes", "ps aux"),
    },
    "leaking-node": {
        "check_process": ("List running processes", "ps aux --sort=-%mem"),
        "check_heap": ("Check Node heap usage", 'node -e "console.log(process.memoryUsage())"'),
    },
    "crashed-nginx": {
        "check_config": ("Validate nginx config syntax", "nginx -t"),
        "check_process": ("List running processes", "ps aux"),
    },
}


def validate_demo_container(container_id: str) -> str:
    """Raise ValidationError unless container_id is one of the 3 demo containers.

    Runs in addition to (not instead of) the existing regex-based
    validate_container_id check.
    """
    if container_id not in DEMO_CONTAINERS:
        raise ValidationError(
            f"Unknown demo container {container_id!r}. "
            f"Must be one of: {sorted(DEMO_CONTAINERS)}"
        )
    return container_id


def resolve_demo_command(container_id: str, command_key: str) -> str:
    """Look up the literal shell command for a (container, command_key) pair.

    Raises ValidationError if the container or key isn't in the fixed menu.
    The caller (never the client) supplies command_key as a validated enum
    value — client-controlled text is never interpolated into a shell.
    """
    validate_demo_container(container_id)
    menu = DEMO_COMMAND_MENU[container_id]
    if command_key not in menu:
        raise ValidationError(
            f"Unknown command_key {command_key!r} for container {container_id!r}. "
            f"Must be one of: {sorted(menu)}"
        )
    return menu[command_key][1]
