import uuid
from unittest.mock import patch

from ops.model import ActiveStatus, BlockedStatus

import pytest


@pytest.fixture
def mock_write():
    with patch("charm.Path.write_text", return_value=None) as m:
        yield m


@pytest.fixture
def mock_mkdir():
    with patch("charm.Path.mkdir", return_value=None) as m:
        yield m


def test_create(harness):
    assert harness.charm.state.license_accepted is False
    assert harness.charm.state.last_config_password is None


def test_config_password_creates_file(harness, mock_write, mock_mkdir):
    assert harness.charm.state.last_config_password is None
    harness.update_config({"splunk-password": "testing"})
    assert harness.charm.state.last_config_password == "testing"
    assert harness.charm.state.splunk_password == "testing"
    mock_write.assert_called_with("testing\n")
    mock_mkdir.assert_called_with(parents=True, exist_ok=True)


def test_reset_password_creates_random(harness, mock_write, mock_mkdir):
    harness.charm.state.splunk_password = str(uuid.uuid4())
    assert harness.charm.state.last_config_password is None
    with patch("charm.random_password", return_value="random_password"):
        harness.update_config({"splunk-password": ""})
    assert harness.charm.state.splunk_password == "random_password"
    assert harness.charm.state.last_config_password == ""
    mock_write.assert_called_with("random_password\n")
    mock_mkdir.assert_called_with(parents=True, exist_ok=True)


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


def test_blocked_if_license_not_accepted(harness, mock_write, mock_mkdir):
    harness.update_config({})
    assert harness.charm.unit.status == BlockedStatus("Run 'accept-license' action")

    harness.charm._on_accept_license_action(None)
    harness.update_config({})
    assert harness.charm.unit.status == ActiveStatus("ready")
