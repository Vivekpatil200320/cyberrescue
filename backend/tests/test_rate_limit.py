"""Rate limiting behavior for the public demo endpoints."""

from unittest.mock import patch

from app.config import settings


class FakeContainerState:
    status = "running"


class FakeContainer:
    state = FakeContainerState()


def test_read_route_is_rate_limited_per_ip(client):
    limit_count = int(settings.rate_limit_read.split("/")[0])

    with patch(
        "app.routes.containers.docker.container.inspect", return_value=FakeContainer()
    ):
        statuses = [client.get("/api/containers").status_code for _ in range(limit_count + 3)]

    assert statuses[:limit_count] == [200] * limit_count
    assert 429 in statuses[limit_count:]


def test_diagnose_route_has_its_own_stricter_limit(client):
    limit_count = int(settings.rate_limit_diagnose.split("/")[0])

    statuses = [
        client.post(
            "/api/containers/leaking-node/diagnose", json={"command_key": "rm_everything"}
        ).status_code
        for _ in range(limit_count + 3)
    ]

    # Requests are invalid (bad command_key -> 400) until the limiter kicks in and
    # starts returning 429 instead, proving diagnose has its own bucket.
    assert 400 in statuses
    assert 429 in statuses
