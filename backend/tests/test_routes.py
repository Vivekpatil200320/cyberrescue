"""Tests for the demo-container HTTP routes.

Mocks python_on_whales.docker so the suite never needs a real Docker daemon.
"""

from unittest.mock import AsyncMock, patch


class FakeContainerState:
    def __init__(self, status):
        self.status = status


class FakeContainer:
    def __init__(self, status):
        self.state = FakeContainerState(status)


class TestListContainers:
    def test_reports_known_names_with_state(self, client):
        with patch(
            "app.routes.containers.docker.container.inspect",
            return_value=FakeContainer("running"),
        ):
            resp = client.get("/api/containers")
        assert resp.status_code == 200
        names = {c["name"] for c in resp.json()["containers"]}
        assert names == {"broken-flask", "leaking-node", "crashed-nginx"}
        assert all(c["state"] == "running" for c in resp.json()["containers"])


class TestLogsAndStats:
    def test_rejects_unknown_container_name(self, client):
        resp = client.get("/api/containers/not-a-demo-container/logs")
        assert resp.status_code == 404

    def test_returns_logs_for_known_container(self, client):
        fake_result = {
            "container_id": "leaking-node",
            "log_lines": ["line one", "line two"],
            "line_count": 2,
            "truncated": False,
        }
        with patch(
            "cyberrescue.core.stream_container_logs", new=AsyncMock(return_value=fake_result)
        ):
            resp = client.get("/api/containers/leaking-node/logs")
        assert resp.status_code == 200
        assert resp.json() == fake_result

    def test_stats_rejects_unknown_container(self, client):
        resp = client.get("/api/containers/nope/stats")
        assert resp.status_code == 404


class TestMenu:
    def test_returns_fixed_menu_for_known_container(self, client):
        resp = client.get("/api/containers/crashed-nginx/menu")
        assert resp.status_code == 200
        keys = {c["key"] for c in resp.json()["commands"]}
        assert "check_config" in keys

    def test_rejects_unknown_container(self, client):
        resp = client.get("/api/containers/nope/menu")
        assert resp.status_code == 404


class TestDiagnose:
    def test_rejects_unknown_container(self, client):
        resp = client.post(
            "/api/containers/nope/diagnose", json={"command_key": "check_process"}
        )
        assert resp.status_code == 404

    def test_rejects_unknown_command_key(self, client):
        resp = client.post(
            "/api/containers/leaking-node/diagnose", json={"command_key": "rm_everything"}
        )
        assert resp.status_code == 400

    def test_rejects_cross_container_command_key(self, client):
        # "check_heap" only exists in the leaking-node menu.
        resp = client.post(
            "/api/containers/crashed-nginx/diagnose", json={"command_key": "check_heap"}
        )
        assert resp.status_code == 400

    def test_runs_resolved_command_for_valid_key(self, client):
        fake_result = {
            "stdout": "PID USER ...",
            "stderr": "",
            "exit_code": 0,
            "timed_out": False,
        }
        with patch(
            "cyberrescue.core.execute_isolated_script", new=AsyncMock(return_value=fake_result)
        ) as mock_exec:
            resp = client.post(
                "/api/containers/leaking-node/diagnose",
                json={"command_key": "check_process"},
            )
        assert resp.status_code == 200
        assert resp.json() == fake_result
        # The literal command was resolved server-side, not client-supplied.
        mock_exec.assert_awaited_once()
        called_container, called_command = mock_exec.await_args.args[:2]
        assert called_container == "leaking-node"
        assert called_command == "ps aux --sort=-%mem"
