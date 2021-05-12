import uuid
from unittest.mock import MagicMock, patch

from ops.charm import ActionEvent
from ops.model import BlockedStatus, MaintenanceStatus

import pytest


def test_create(harness):
    assert harness.charm.state.license_accepted is False
    assert harness.charm.state.last_config_password is None


def test_config_password_creates_file(harness):
    assert harness.charm.state.last_config_password is None
    harness.update_config({"splunk-password": "testing"})
    assert harness.charm.state.last_config_password == "testing"
    assert harness.charm.state.splunk_password == "testing"


def test_reset_password_creates_random(harness):
    harness.charm.state.splunk_password = str(uuid.uuid4())
    assert harness.charm.state.last_config_password is None
    with patch("charm.random_password", return_value="random_password"):
        harness.update_config({"splunk-password": ""})
    assert harness.charm.state.splunk_password == "random_password"
    assert harness.charm.state.last_config_password == ""


@pytest.mark.parametrize(
    "config_expected",
    [
        ({}, None),
        ({"splunk-role": "test-role"}, "SPLUNK_ROLE"),
        ({"splunk-license": "test-license"}, "SPLUNK_LICENSE_URI"),
    ],
    ids=[
        "empty",
        "splunk-role",
        "splunk-license",
    ],
)
def test_splunk_layer(harness, config_expected):
    config, expected = config_expected
    harness.charm.state.last_config_password = config.get("splunk-password", "")
    harness.update_config(config)
    result = harness.charm._splunk_layer()
    assert type(result) is dict
    env = result["services"]["splunk"]["environment"]
    assert env["SPLUNK_PASSWORD"] == harness.charm.state.splunk_password
    if expected:
        assert {env[expected]} == set(config.values())


def test_blocked_if_license_not_accepted(harness):
    harness.update_config({})
    assert harness.charm.unit.status == BlockedStatus("Run 'accept-license' action")


def test_blocked_if_minimum_password_error(harness):
    harness.charm._on_accept_license_action(None)
    harness.update_config({"splunk-password": "short"})
    assert harness.charm.unit.status == BlockedStatus(
        "Password doesn't meet minimum requirements."
    )


def test_pause(harness):
    harness.charm.state.auto_start = True
    harness.charm._on_pause_action(None)
    harness.charm._on_accept_license_action(None)
    assert harness.charm.state.auto_start is False
    assert harness.charm.unit.status == MaintenanceStatus("splunk service is paused")


def test_resume(harness):
    harness.charm.state.auto_start = False
    harness.charm._on_resume_action(None)
    harness.charm._on_accept_license_action(None)
    assert harness.charm.state.auto_start is True
    assert harness.charm.unit.status.message == "ready"


def test_reveal_password(harness):
    act = MagicMock(spec=ActionEvent)
    harness.charm.state.splunk_password = "testing"
    harness.charm._on_reveal_admin_password_action(act)
    act.set_results.assert_called_with({"username": "admin", "password": "testing"})
