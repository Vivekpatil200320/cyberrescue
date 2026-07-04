"""Tests for the public-demo allowlist and fixed command menu."""

import pytest

from cyberrescue.demo_policy import (
    DEMO_CONTAINERS,
    DEMO_COMMAND_MENU,
    resolve_demo_command,
    validate_demo_container,
)
from cyberrescue.security import ValidationError


class TestValidateDemoContainer:
    @pytest.mark.parametrize("name", sorted(DEMO_CONTAINERS))
    def test_allows_known_demo_containers(self, name):
        assert validate_demo_container(name) == name

    def test_rejects_unknown_container(self):
        with pytest.raises(ValidationError):
            validate_demo_container("some-other-container")

    def test_rejects_near_miss_name(self):
        with pytest.raises(ValidationError):
            validate_demo_container("broken-flask-2")

    def test_rejects_empty_string(self):
        with pytest.raises(ValidationError):
            validate_demo_container("")

    def test_rejects_path_traversal_like_string(self):
        with pytest.raises(ValidationError):
            validate_demo_container("../etc/passwd")


class TestResolveDemoCommand:
    def test_resolves_known_key_for_each_container(self):
        for container_id, menu in DEMO_COMMAND_MENU.items():
            for command_key, (_, literal_command) in menu.items():
                assert resolve_demo_command(container_id, command_key) == literal_command

    def test_rejects_unknown_command_key(self):
        with pytest.raises(ValidationError):
            resolve_demo_command("leaking-node", "rm_everything")

    def test_rejects_cross_container_key_mismatch(self):
        # "check_heap" only exists for leaking-node, not crashed-nginx.
        with pytest.raises(ValidationError):
            resolve_demo_command("crashed-nginx", "check_heap")

    def test_rejects_unknown_container(self):
        with pytest.raises(ValidationError):
            resolve_demo_command("not-a-demo-container", "check_process")
