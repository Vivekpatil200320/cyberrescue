"""Container ID validation and command blocklist.

These guards run before any docker exec / docker logs call touches
user-supplied input. Fail closed: anything that doesn't clearly match
the allowed shape, or that matches a known-dangerous pattern, is rejected.
"""

import re

CONTAINER_ID_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]+$")

BLOCKED_COMMAND_PATTERNS = [
    re.compile(r"rm\s+-rf\s+/"),
    re.compile(r"curl.*\|.*sh"),
    re.compile(r"wget.*\|.*sh"),
    re.compile(r"chmod\s+777"),
    re.compile(r"/etc/passwd"),
    re.compile(r">\s*/dev/sd"),
]


class ValidationError(ValueError):
    """Raised when user-supplied input fails a security check."""


def validate_container_id(container_id: str) -> str:
    """Validate a container ID or name against the allowed pattern.

    Raises ValidationError if invalid. Returns the container_id unchanged
    if valid, so callers can use it inline.
    """
    if not container_id or not CONTAINER_ID_PATTERN.match(container_id):
        raise ValidationError(
            f"Invalid container_id: {container_id!r}. "
            f"Must match pattern: {CONTAINER_ID_PATTERN.pattern}"
        )
    return container_id


def check_command_safety(command: str) -> None:
    """Raise ValidationError if `command` matches any blocked pattern.

    Returns None (does nothing) if the command is allowed.
    """
    for pattern in BLOCKED_COMMAND_PATTERNS:
        if pattern.search(command):
            raise ValidationError(
                f"Command blocked by security policy "
                f"(matched pattern: {pattern.pattern!r}): {command!r}"
            )
