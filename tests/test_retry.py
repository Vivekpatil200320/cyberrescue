"""Tests for the retry-with-backoff helper on read-only docker calls."""

import asyncio

import pytest
from python_on_whales.exceptions import DockerException

from cyberrescue import core


def _docker_exc():
    return DockerException(["docker", "stats"], 1)


class TestDockerCallWithRetry:
    def test_returns_result_on_first_success(self):
        result = asyncio.run(core._docker_call_with_retry(lambda: "ok"))
        assert result == "ok"

    def test_retries_transient_failure_then_succeeds(self, monkeypatch):
        monkeypatch.setattr(core, "RETRY_BASE_DELAY_S", 0)
        calls = {"n": 0}

        def flaky():
            calls["n"] += 1
            if calls["n"] < 3:
                raise _docker_exc()
            return "recovered"

        result = asyncio.run(core._docker_call_with_retry(flaky))
        assert result == "recovered"
        assert calls["n"] == 3

    def test_raises_after_exhausting_attempts(self, monkeypatch):
        monkeypatch.setattr(core, "RETRY_BASE_DELAY_S", 0)
        calls = {"n": 0}

        def always_fails():
            calls["n"] += 1
            raise _docker_exc()

        with pytest.raises(DockerException):
            asyncio.run(core._docker_call_with_retry(always_fails))
        assert calls["n"] == core.RETRY_ATTEMPTS
