"""Recreate the 3 public-demo containers from a clean state.

Run on a schedule (see systemd/cyberrescue-reset.timer) so that anonymous
visitors interacting with the demo can never permanently break it for the
next visitor. Docker's own `restart: on-failure` (set in docker-compose.yml)
already handles crash-loops between resets; this script forces a full
recreate on top of that as a periodic safety net.
"""

import logging
import sys
from pathlib import Path

from python_on_whales import DockerClient
from python_on_whales.exceptions import DockerException

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("cyberrescue.reset")

COMPOSE_FILE = Path(__file__).parent / "docker-compose.yml"
SERVICES = ["broken-flask", "leaking-node", "crashed-nginx"]


def main() -> int:
    docker = DockerClient(compose_files=[str(COMPOSE_FILE)])
    try:
        docker.compose.up(services=SERVICES, detach=True, force_recreate=True, build=False)
    except DockerException:
        logger.exception("Failed to reset demo containers")
        return 1

    logger.info("Reset demo containers: %s", ", ".join(SERVICES))
    return 0


if __name__ == "__main__":
    sys.exit(main())
